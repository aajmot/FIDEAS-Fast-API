from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from datetime import datetime
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user
from modules.account_module.services.payment_service import PaymentService
from sqlalchemy import or_

router = APIRouter()

# Payment endpoints
@router.get("/payments", response_model=PaginatedResponse)
async def get_payments(
    pagination: PaginationParams = Depends(),
    payment_mode: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Payment

    with db_manager.get_session() as session:
        query = session.query(Payment).filter(
            Payment.tenant_id == current_user['tenant_id']
        )
        
        if payment_mode:
            query = query.filter(Payment.payment_mode == payment_mode)
        
        if pagination.search:
            query = query.filter(or_(
                Payment.payment_type.ilike(f"%{pagination.search}%"),
                Payment.remarks.ilike(f"%{pagination.search}%"),
                Payment.payment_number.ilike(f"%{pagination.search}%")
            ))
        
        query = query.order_by(Payment.payment_date.desc(), Payment.id.desc())
        
        total = query.count()
        payments = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        payment_data = [{
            "id": payment.id,
            "payment_number": payment.payment_number,
            "payment_mode": payment.payment_mode,
            "payment_type": payment.payment_type,
            "account_id": payment.account_id,
            "amount": float(payment.amount) if payment.amount else 0,
            "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
            "reference_type": payment.reference_type or "",
            "reference_number": payment.reference_number or "",
            "remarks": payment.remarks or "",
            "status": "Completed"
        } for payment in payments]
    
    return PaginatedResponse(
        success=True,
        message="Payments retrieved successfully",
        data=payment_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/payments", response_model=BaseResponse)
async def create_payment(payment_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Payment

    with db_manager.get_session() as session:
        try:
            payment = Payment(
                payment_number=payment_data['payment_number'],
                payment_date=datetime.fromisoformat(payment_data['payment_date']),
                payment_type=payment_data['payment_type'],
                payment_mode=payment_data['payment_mode'],
                reference_type=payment_data.get('reference_type', 'GENERAL'),
                reference_id=payment_data.get('reference_id', 0),
                reference_number=payment_data.get('reference_number', ''),
                amount=payment_data['amount'],
                account_id=payment_data.get('account_id'),
                remarks=payment_data.get('remarks'),
                tenant_id=current_user['tenant_id'],
                created_by=current_user['username']
            )
            session.add(payment)
            session.flush()
            payment_id = payment.id
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Payment created successfully",
                data={"id": payment_id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.post("/record-payment", response_model=BaseResponse)
async def record_payment(payment_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    try:
        if 'payment_date' in payment_data and isinstance(payment_data['payment_date'], str):
            payment_data['payment_date'] = datetime.fromisoformat(payment_data['payment_date'].replace('Z', ''))
        
        payment_service = PaymentService()
        payment = payment_service.record_payment(payment_data)
        return BaseResponse(
            success=True,
            message="Payment recorded successfully",
            data={"id": payment.id, "payment_number": payment.payment_number}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/record-receipt", response_model=BaseResponse)
async def record_receipt(receipt_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    try:
        if 'payment_date' in receipt_data and isinstance(receipt_data['payment_date'], str):
            receipt_data['payment_date'] = datetime.fromisoformat(receipt_data['payment_date'].replace('Z', ''))
        
        payment_service = PaymentService()
        receipt = payment_service.record_receipt(receipt_data)
        return BaseResponse(
            success=True,
            message="Receipt recorded successfully",
            data={"id": receipt.id, "payment_number": receipt.payment_number}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/payments/{payment_id}", response_model=BaseResponse)
async def update_payment(payment_id: int, payment_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Payment

    with db_manager.get_session() as session:
        try:
            payment = session.query(Payment).filter(
                Payment.id == payment_id,
                Payment.tenant_id == current_user['tenant_id']
            ).first()
            
            if not payment:
                raise HTTPException(status_code=404, detail="Payment not found")
            
            if 'payment_date' in payment_data:
                payment.payment_date = datetime.fromisoformat(payment_data['payment_date'])
            if 'payment_type' in payment_data:
                payment.payment_type = payment_data['payment_type']
            if 'payment_mode' in payment_data:
                payment.payment_mode = payment_data['payment_mode']
            if 'amount' in payment_data:
                payment.amount = payment_data['amount']
            if 'account_id' in payment_data:
                payment.account_id = payment_data['account_id']
            if 'remarks' in payment_data:
                payment.remarks = payment_data['remarks']
            if 'reference_type' in payment_data:
                payment.reference_type = payment_data['reference_type']
            if 'reference_number' in payment_data:
                payment.reference_number = payment_data['reference_number']
            
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Payment updated successfully",
                data={"id": payment_id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.delete("/payments/{payment_id}", response_model=BaseResponse)
async def delete_payment(payment_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Payment

    with db_manager.get_session() as session:
        try:
            payment = session.query(Payment).filter(
                Payment.id == payment_id,
                Payment.tenant_id == current_user['tenant_id']
            ).first()
            
            if not payment:
                raise HTTPException(status_code=404, detail="Payment not found")
            
            session.delete(payment)
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Payment deleted successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))
