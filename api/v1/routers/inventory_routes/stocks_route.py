from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
import io
import csv
from fastapi import APIRouter, Depends, Query
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse
from core.database.connection import db_manager
from modules.inventory_module.services.inventory_costing_service import InventoryCostingService
from sqlalchemy import func, and_, case
from datetime import datetime, timedelta
from decimal import Decimal
from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from sqlalchemy import or_
import math
from api.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.get("/stock-meter/export-template")
async def export_stock_meter_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["product_id", "quantity", "unit_price", "location"])
    writer.writerow(["1", "100", "10.50", "Warehouse A"])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=stock_meter_template.csv"}
    )


@router.post("/stock-meter/import", response_model=BaseResponse)
async def import_stock_meter(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    from core.database.connection import db_manager
    from modules.inventory_module.models.entities import StockMeter
    
    imported_count = 0
    with db_manager.get_session() as session:
        for row in csv_data:
            try:
                stock = StockMeter(
                    product_id=int(row["product_id"]),
                    quantity=int(row["quantity"]),
                    unit_price=float(row["unit_price"]),
                    location=row["location"]
                )
                session.add(stock)
                imported_count += 1
            except Exception:
                continue
        session.commit()
    
    return BaseResponse(
        success=True,
        message=f"Imported {imported_count} stock records successfully"
    )


# Stock Meter Summary endpoint
@router.get("/stock-meter-summary", response_model=BaseResponse)
async def get_stock_meter_summary(product_id: int = None, current_user: dict = Depends(get_current_user)):
    from modules.inventory_module.services.stock_summary_service import StockSummaryService
    
    service = StockSummaryService()
    summary_data = service.get_stock_meter_summary(product_id)
    
    return BaseResponse(
        success=True,
        message="Stock meter summary retrieved successfully",
        data=summary_data
    )


# Stock Summary endpoint
@router.get("/stock-summary", response_model=BaseResponse)
async def get_stock_summary(product_id: int = None, current_user: dict = Depends(get_current_user)):
    from modules.inventory_module.services.stock_summary_service import StockSummaryService
    
    service = StockSummaryService()
    summary_data = service.get_stock_summary(product_id)
    
    return BaseResponse(
        success=True,
        message="Stock summary retrieved successfully",
        data=summary_data
    )


# Stock Details endpoint
@router.get("/stock-details", response_model=PaginatedResponse)
async def get_stock_details(product_id: int = None, pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from modules.inventory_module.services.stock_summary_service import StockSummaryService
    
    service = StockSummaryService()
    stock_data, total = service.get_stock_details_with_status(
        product_id=product_id,
        page=pagination.page,
        per_page=pagination.per_page,
        search=pagination.search
    )
    
    return PaginatedResponse(
        success=True,
        message="Stock details retrieved successfully",
        data=stock_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )


# Stock Tracking Summary endpoint
@router.get("/stock-tracking-summary", response_model=BaseResponse)
async def get_stock_tracking_summary(
    product_id: int = None,
    movement_type: str = None,
    reference_type: str = None,
    from_date: str = None,
    to_date: str = None,
    current_user: dict = Depends(get_current_user)
):
    from modules.inventory_module.services.stock_summary_service import StockSummaryService
    
    service = StockSummaryService()
    summary_data = service.get_stock_tracking_summary(
        product_id=product_id,
        movement_type=movement_type,
        reference_type=reference_type,
        from_date=from_date,
        to_date=to_date
    )
    
    return BaseResponse(
        success=True,
        message="Stock tracking summary retrieved successfully",
        data=summary_data
    )


# Stock Movements endpoint
@router.get("/stock-movements", response_model=PaginatedResponse)
async def get_stock_movements(
    product_id: int = None,
    movement_type: str = None,
    reference_type: str = None,
    from_date: str = None,
    to_date: str = None,
    pagination: PaginationParams = Depends(),
    current_user: dict = Depends(get_current_user)
):
    from core.database.connection import db_manager
    from modules.inventory_module.models.stock_entity import StockTransaction
    from modules.inventory_module.models.entities import Product
    from sqlalchemy.orm import joinedload
    from sqlalchemy import and_, func
    from datetime import datetime
    from core.shared.utils.session_manager import session_manager
    
    with db_manager.get_session() as session:
        query = session.query(StockTransaction).options(joinedload(StockTransaction.product)).join(Product)
        
        # Apply tenant filter
        tenant_id = session_manager.get_current_tenant_id()
        if tenant_id:
            query = query.filter(StockTransaction.tenant_id == tenant_id)
        
        # Apply filters
        if product_id:
            query = query.filter(StockTransaction.product_id == product_id)
        
        if movement_type:
            if movement_type == 'in':
                query = query.filter(StockTransaction.transaction_type == 'IN')
            elif movement_type == 'out':
                query = query.filter(StockTransaction.transaction_type == 'OUT')
        
        if reference_type:
            source_mapping = {
                'Purchase Order': 'PURCHASE',
                'Sales Order': 'SALES',
                'Product Waste': 'WASTE',
                'Stock Adjustment': 'ADJUSTMENT'
            }
            if reference_type in source_mapping:
                query = query.filter(StockTransaction.transaction_source == source_mapping[reference_type])
        
        if from_date:
            try:
                from_dt = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
                query = query.filter(StockTransaction.transaction_date >= from_dt)
            except ValueError:
                pass
        
        if to_date:
            try:
                to_dt = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
                query = query.filter(StockTransaction.transaction_date <= to_dt)
            except ValueError:
                pass
        
        # Apply search filter
        if pagination.search:
            query = query.filter(or_(
                Product.name.ilike(f"%{pagination.search}%"),
                StockTransaction.reference_number.ilike(f"%{pagination.search}%"),
                StockTransaction.batch_number.ilike(f"%{pagination.search}%")
            ))
        
        total = query.count()
        transactions = query.order_by(StockTransaction.transaction_date.desc()).offset(pagination.offset).limit(pagination.per_page).all()
        
        # Calculate running balance for each transaction
        movement_data = []
        for transaction in transactions:
            # Map transaction source to reference type
            reference_type_map = {
                'PURCHASE': 'Purchase Order',
                'SALES': 'Sales Order',
                'WASTE': 'Product Waste',
                'ADJUSTMENT': 'Stock Adjustment',
                'SALES_REVERSAL': 'Sales Reversal',
                'PURCHASE_REVERSAL': 'Purchase Reversal'
            }
            
            movement_data.append({
                "id": transaction.id,
                "product_id": transaction.product_id,
                "product_name": transaction.product.name,
                "batch_number": transaction.batch_number or "",
                "movement_type": transaction.transaction_type.lower(),
                "quantity": float(transaction.quantity),
                "reference_type": reference_type_map.get(transaction.transaction_source, transaction.transaction_source),
                "reference_number": transaction.reference_number,
                "movement_date": transaction.transaction_date.isoformat() if transaction.transaction_date else None,
                "notes": f"{transaction.transaction_source} transaction",
                "unit_price": float(transaction.unit_price or 0)
            })
    
    return PaginatedResponse(
        success=True,
        message="Stock movements retrieved successfully",
        data=movement_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )


@router.get("/stock-valuation", response_model=BaseResponse)
async def get_stock_valuation(current_user: dict = Depends(get_current_user)):
    """Get current stock valuation"""
    from modules.inventory_module.models.stock_entity import StockTransaction
    from modules.inventory_module.models.entities import Product
    
    with db_manager.get_session() as session:
        products = session.query(
            Product.id, Product.name,
            func.sum(case(
                (StockTransaction.transaction_type == 'IN', StockTransaction.quantity),
                else_=-StockTransaction.quantity
            )).label('qty'),
            func.avg(StockTransaction.unit_price).label('avg_cost')
        ).join(StockTransaction).filter(
            Product.tenant_id == current_user['tenant_id']
        ).group_by(Product.id, Product.name).all()
        
        valuation = [{
            'product_id': p[0],
            'product_name': p[1],
            'quantity': float(p[2] or 0),
            'avg_cost': float(p[3] or 0),
            'value': float(p[2] or 0) * float(p[3] or 0)
        } for p in products]
        
        total_value = sum(item['value'] for item in valuation)
        
        return BaseResponse(
            success=True,
            message="Stock valuation retrieved successfully",
            data={'items': valuation, 'total_value': total_value}
        )

@router.get("/stock-aging", response_model=BaseResponse)
async def get_stock_aging(current_user: dict = Depends(get_current_user)):
    """Get stock aging analysis"""
    from modules.inventory_module.models.stock_entity import StockTransaction
    from modules.inventory_module.models.entities import Product
    
    with db_manager.get_session() as session:
        cutoff_30 = datetime.now() - timedelta(days=30)
        cutoff_60 = datetime.now() - timedelta(days=60)
        cutoff_90 = datetime.now() - timedelta(days=90)
        
        aging = session.query(
            Product.name,
            func.sum(case(
                (and_(StockTransaction.transaction_date >= cutoff_30, StockTransaction.transaction_type == 'IN'), 
                 StockTransaction.quantity),
                else_=0
            )).label('age_0_30'),
            func.sum(case(
                (and_(StockTransaction.transaction_date >= cutoff_60, StockTransaction.transaction_date < cutoff_30, 
                      StockTransaction.transaction_type == 'IN'), 
                 StockTransaction.quantity),
                else_=0
            )).label('age_31_60'),
            func.sum(case(
                (and_(StockTransaction.transaction_date >= cutoff_90, StockTransaction.transaction_date < cutoff_60, 
                      StockTransaction.transaction_type == 'IN'), 
                 StockTransaction.quantity),
                else_=0
            )).label('age_61_90'),
            func.sum(case(
                (and_(StockTransaction.transaction_date < cutoff_90, StockTransaction.transaction_type == 'IN'), 
                 StockTransaction.quantity),
                else_=0
            )).label('age_90_plus')
        ).join(StockTransaction).filter(
            Product.tenant_id == current_user['tenant_id']
        ).group_by(Product.name).all()
        
        aging_data = [{
            'product': a[0],
            '0-30_days': float(a[1] or 0),
            '31-60_days': float(a[2] or 0),
            '61-90_days': float(a[3] or 0),
            '90+_days': float(a[4] or 0)
        } for a in aging]
        
        return BaseResponse(
            success=True,
            message="Stock aging retrieved successfully",
            data=aging_data
        )

@router.get("/cogs", response_model=BaseResponse)
async def calculate_cogs(
    product_id: int = Query(...),
    quantity: float = Query(...),
    method: str = Query('FIFO'),
    current_user: dict = Depends(get_current_user)
):
    """Calculate Cost of Goods Sold"""
    cogs = InventoryCostingService.calculate_cogs(product_id, Decimal(str(quantity)), method)
    
    return BaseResponse(
        success=True,
        message="COGS calculated successfully",
        data={'cogs': float(cogs), 'method': method}
    )
