from fastapi import APIRouter, Depends, Query
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse
from core.database.connection import db_manager
from modules.inventory_module.services.inventory_costing_service import InventoryCostingService
from sqlalchemy import func, and_, case
from datetime import datetime, timedelta
from decimal import Decimal

router = APIRouter()

@router.get("/stock-valuation", response_model=BaseResponse)
async def get_stock_valuation(current_user: dict = Depends(get_current_user)):
    """Get current stock valuation"""
    from modules.inventory_module.models.stock_entities import StockTransaction
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
    from modules.inventory_module.models.stock_entities import StockTransaction
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
