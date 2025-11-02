from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse
from core.database.connection import db_manager
from sqlalchemy import func, and_

router = APIRouter()

@router.get("/gstr1", response_model=BaseResponse)
async def get_gstr1(month: str = Query(...), current_user: dict = Depends(get_current_user)):
    """Generate GSTR-1 report for outward supplies"""
    from modules.inventory_module.models.entities import SalesOrder, SalesOrderItem, Customer, Product
    
    year, month_num = map(int, month.split('-'))
    start_date = datetime(year, month_num, 1)
    end_date = datetime(year, month_num + 1, 1) if month_num < 12 else datetime(year + 1, 1, 1)
    
    with db_manager.get_session() as session:
        # B2B invoices
        b2b_invoices = session.query(
            Customer.name, Customer.tax_id,
            SalesOrder.order_number, SalesOrder.order_date, SalesOrder.total_amount,
            func.sum(SalesOrderItem.quantity * SalesOrderItem.unit_price * SalesOrderItem.gst_rate / 100).label('gst_amount')
        ).join(SalesOrderItem).join(Customer).filter(
            and_(
                SalesOrder.tenant_id == current_user['tenant_id'],
                SalesOrder.order_date >= start_date,
                SalesOrder.order_date < end_date,
                Customer.tax_id.isnot(None)
            )
        ).group_by(Customer.name, Customer.tax_id, SalesOrder.order_number, SalesOrder.order_date, SalesOrder.total_amount).all()
        
        # B2C invoices
        b2c_invoices = session.query(
            func.sum(SalesOrder.total_amount).label('total'),
            func.count(SalesOrder.id).label('count')
        ).join(Customer).filter(
            and_(
                SalesOrder.tenant_id == current_user['tenant_id'],
                SalesOrder.order_date >= start_date,
                SalesOrder.order_date < end_date,
                Customer.tax_id.is_(None)
            )
        ).first()
        
        return BaseResponse(
            success=True,
            message="GSTR-1 generated successfully",
            data={
                'month': month,
                'b2b': [{'customer': inv[0], 'gstin': inv[1], 'invoice': inv[2], 'date': inv[3].isoformat(), 'amount': float(inv[4]), 'gst': float(inv[5])} for inv in b2b_invoices],
                'b2c': {'total': float(b2c_invoices[0] or 0), 'count': b2c_invoices[1] or 0}
            }
        )

@router.get("/gstr3b", response_model=BaseResponse)
async def get_gstr3b(month: str = Query(...), current_user: dict = Depends(get_current_user)):
    """Generate GSTR-3B summary return"""
    from modules.inventory_module.models.entities import SalesOrder, SalesOrderItem, PurchaseOrder, PurchaseOrderItem
    
    year, month_num = map(int, month.split('-'))
    start_date = datetime(year, month_num, 1)
    end_date = datetime(year, month_num + 1, 1) if month_num < 12 else datetime(year + 1, 1, 1)
    
    with db_manager.get_session() as session:
        # Outward supplies
        outward = session.query(
            func.sum(SalesOrderItem.quantity * SalesOrderItem.unit_price).label('taxable'),
            func.sum(SalesOrderItem.quantity * SalesOrderItem.unit_price * SalesOrderItem.gst_rate / 100).label('gst')
        ).join(SalesOrder).filter(
            and_(
                SalesOrder.tenant_id == current_user['tenant_id'],
                SalesOrder.order_date >= start_date,
                SalesOrder.order_date < end_date
            )
        ).first()
        
        # Inward supplies
        inward = session.query(
            func.sum(PurchaseOrderItem.quantity * PurchaseOrderItem.unit_price).label('taxable'),
            func.sum(PurchaseOrderItem.quantity * PurchaseOrderItem.unit_price * PurchaseOrderItem.gst_rate / 100).label('gst')
        ).join(PurchaseOrder).filter(
            and_(
                PurchaseOrder.tenant_id == current_user['tenant_id'],
                PurchaseOrder.order_date >= start_date,
                PurchaseOrder.order_date < end_date
            )
        ).first()
        
        outward_taxable = float(outward[0] or 0)
        outward_gst = float(outward[1] or 0)
        inward_gst = float(inward[1] or 0)
        
        return BaseResponse(
            success=True,
            message="GSTR-3B generated successfully",
            data={
                'month': month,
                'outward_supplies': {'taxable_value': outward_taxable, 'gst': outward_gst},
                'inward_supplies': {'itc_available': inward_gst},
                'net_gst_liability': outward_gst - inward_gst
            }
        )
