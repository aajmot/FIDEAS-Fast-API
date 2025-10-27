from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
import io
import csv
from datetime import datetime

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from sqlalchemy import or_
import math
from api.middleware.auth_middleware import get_current_user
from modules.account_module.services.account_service import AccountService
from modules.account_module.services.voucher_service import VoucherService
from modules.account_module.services.payment_service import PaymentService
from modules.account_module.services.audit_service import AuditService
from sqlalchemy import func

router = APIRouter()

# Currency Management endpoints
@router.get("/currencies", response_model=PaginatedResponse)
async def get_currencies(current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Currency
    
    with db_manager.get_session() as session:
        currencies = session.query(Currency).filter(Currency.is_active == True).all()
        
        currency_data = [{
            "id": curr.id,
            "code": curr.code,
            "name": curr.name,
            "symbol": curr.symbol,
            "is_base": curr.is_base
        } for curr in currencies]
    
    return PaginatedResponse(
        success=True,
        message="Currencies retrieved successfully",
        data=currency_data,
        total=len(currency_data),
        page=1,
        per_page=len(currency_data),
        total_pages=1
    )

@router.get("/exchange-rates", response_model=BaseResponse)
async def get_exchange_rate(
    from_currency: str = Query(...),
    to_currency: str = Query(...),
    date: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import ExchangeRate, Currency
    from datetime import datetime
    
    with db_manager.get_session() as session:
        effective_date = datetime.fromisoformat(date).date() if date else datetime.now().date()
        
        from_curr = session.query(Currency).filter(Currency.code == from_currency).first()
        to_curr = session.query(Currency).filter(Currency.code == to_currency).first()
        
        if not from_curr or not to_curr:
            raise HTTPException(status_code=404, detail="Currency not found")
        
        rate = session.query(ExchangeRate).filter(
            ExchangeRate.from_currency_id == from_curr.id,
            ExchangeRate.to_currency_id == to_curr.id,
            ExchangeRate.effective_date <= effective_date,
            ExchangeRate.tenant_id == current_user['tenant_id']
        ).order_by(ExchangeRate.effective_date.desc()).first()
        
        if not rate:
            return BaseResponse(
                success=True,
                message="No exchange rate found, using default",
                data={"rate": 1.0}
            )
        
        return BaseResponse(
            success=True,
            message="Exchange rate retrieved successfully",
            data={"rate": float(rate.rate)}
        )

@router.get("/exchange-rates/all", response_model=BaseResponse)
async def get_all_exchange_rates(current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import ExchangeRate, Currency
    
    with db_manager.get_session() as session:
        rates = session.query(ExchangeRate).filter(
            ExchangeRate.tenant_id == current_user['tenant_id']
        ).order_by(ExchangeRate.effective_date.desc()).all()
        
        rate_data = []
        for rate in rates:
            from_curr = session.query(Currency).filter(Currency.id == rate.from_currency_id).first()
            to_curr = session.query(Currency).filter(Currency.id == rate.to_currency_id).first()
            
            rate_data.append({
                "id": rate.id,
                "from_currency": from_curr.code if from_curr else "",
                "to_currency": to_curr.code if to_curr else "",
                "rate": float(rate.rate),
                "effective_date": rate.effective_date.isoformat()
            })
        
        return BaseResponse(
            success=True,
            message="Exchange rates retrieved successfully",
            data=rate_data
        )

@router.post("/exchange-rates", response_model=BaseResponse)
async def create_exchange_rate(rate_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import ExchangeRate, Currency
    from datetime import datetime
    
    with db_manager.get_session() as session:
        try:
            from_curr = session.query(Currency).filter(Currency.code == rate_data['from_currency']).first()
            to_curr = session.query(Currency).filter(Currency.code == rate_data['to_currency']).first()
            
            if not from_curr or not to_curr:
                raise HTTPException(status_code=404, detail="Currency not found")
            
            rate = ExchangeRate(
                from_currency_id=from_curr.id,
                to_currency_id=to_curr.id,
                rate=rate_data['rate'],
                effective_date=datetime.fromisoformat(rate_data['effective_date']).date(),
                tenant_id=current_user['tenant_id']
            )
            session.add(rate)
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Exchange rate created successfully",
                data={"id": rate.id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.delete("/exchange-rates/{rate_id}", response_model=BaseResponse)
async def delete_exchange_rate(rate_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import ExchangeRate
    
    with db_manager.get_session() as session:
        try:
            rate = session.query(ExchangeRate).filter(
                ExchangeRate.id == rate_id,
                ExchangeRate.tenant_id == current_user['tenant_id']
            ).first()
            
            if not rate:
                raise HTTPException(status_code=404, detail="Exchange rate not found")
            
            session.delete(rate)
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Exchange rate deleted successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.post("/exchange-rates/import", response_model=BaseResponse)
async def import_exchange_rates(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import ExchangeRate, Currency
    from datetime import datetime
    
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    imported_count = 0
    with db_manager.get_session() as session:
        try:
            for row in csv_data:
                from_curr = session.query(Currency).filter(Currency.code == row['from_currency']).first()
                to_curr = session.query(Currency).filter(Currency.code == row['to_currency']).first()
                
                if not from_curr or not to_curr:
                    continue
                
                rate = ExchangeRate(
                    from_currency_id=from_curr.id,
                    to_currency_id=to_curr.id,
                    rate=float(row['rate']),
                    effective_date=datetime.fromisoformat(row['effective_date']).date(),
                    tenant_id=current_user['tenant_id']
                )
                session.add(rate)
                imported_count += 1
            
            session.commit()
            return BaseResponse(
                success=True,
                message=f"Imported {imported_count} exchange rates successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.get("/exchange-rates/export-template")
async def export_exchange_rates_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['from_currency', 'to_currency', 'rate', 'effective_date'])
    writer.writerow(['USD', 'INR', '83.50', '2024-01-01'])
    writer.writerow(['EUR', 'INR', '91.20', '2024-01-01'])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=exchange_rates_template.csv"}
    )
