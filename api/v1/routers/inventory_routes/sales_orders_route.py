from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.get("/sales-orders", response_model=PaginatedResponse)
async def get_sales_orders(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from modules.inventory_module.services.sales_order_service import SalesOrderService

    sales_order_service = SalesOrderService()
    orders = sales_order_service.get_all(page=pagination.page, page_size=pagination.per_page)
    total = sales_order_service.get_total_count()

    order_data = [{
        "id": order.id,
        "so_number": order.order_number,
        "customer_name": order.customer_name,
        "agency_id": getattr(order, 'agency_id', None),
        "agency_name": getattr(order, 'agency_name', None),
        "order_date": order.order_date.isoformat() if order.order_date else None,
        "net_amount": float(order.net_amount),
        "status": order.status
    } for order in orders]

    return PaginatedResponse(
        success=True,
        message="Sales orders retrieved successfully",
        data=order_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )


@router.post("/sales-orders", response_model=BaseResponse)
async def create_sales_order(order_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from modules.inventory_module.services.sales_order_service import SalesOrderService
    from modules.account_module.services.transaction_posting_service import TransactionPostingService
    from core.database.connection import db_manager

    with db_manager.get_session() as session:
        sales_order_service = SalesOrderService()
        order_id = sales_order_service.create_with_items(order_data['order'], order_data['items'])

        # Post to accounting
        try:
            posting_data = {
                'reference_type': 'SALES_ORDER',
                'reference_id': order_id,
                'reference_number': order_data['order'].get('order_number'),
                'total_amount': order_data['order'].get('net_amount'),
                'transaction_date': order_data['order'].get('order_date'),
                'created_by': current_user['username']
            }
            voucher_id = TransactionPostingService.post_transaction(
                session, 'SALES_ORDER', posting_data, current_user['tenant_id']
            )
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Accounting posting failed: {e}")

        return BaseResponse(
            success=True,
            message="Sales order created successfully",
            data={"id": order_id}
        )


@router.get("/sales-orders/{order_id}", response_model=BaseResponse)
async def get_sales_order(order_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.inventory_module.models.entities import SalesOrder, SalesOrderItem, Product, Customer
    from modules.admin_module.models.agency import Agency

    with db_manager.get_session() as session:
        order = session.query(SalesOrder).filter(SalesOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Sales order not found")

        items = session.query(SalesOrderItem, Product).join(Product).filter(
            SalesOrderItem.sales_order_id == order_id
        ).all()

        customer = session.query(Customer).filter(Customer.id == order.customer_id).first()

        agency_name = None
        if order.agency_id:
            agency = session.query(Agency).filter(Agency.id == order.agency_id).first()
            if agency:
                agency_name = f"{agency.name} | {agency.phone}"

        order_data = {
            "id": order.id,
            "so_number": order.order_number,
            "reference_number": order.reference_number,
            "customer_id": order.customer_id,
            "customer_name": customer.name if customer else order.customer_name,
            "customer_phone": order.customer_phone,
            "agency_id": order.agency_id,
            "agency_name": agency_name,
            "order_date": order.order_date.isoformat() if order.order_date else None,
            
            # Amount breakdown
            "subtotal_amount": float(order.subtotal_amount),
            "header_discount_percent": float(order.header_discount_percent) if order.header_discount_percent else 0,
            "header_discount_amount": float(order.header_discount_amount) if order.header_discount_amount else 0,
            "taxable_amount": float(order.taxable_amount),
            
            # Tax breakdown
            "cgst_amount": float(order.cgst_amount) if order.cgst_amount else 0,
            "sgst_amount": float(order.sgst_amount) if order.sgst_amount else 0,
            "igst_amount": float(order.igst_amount) if order.igst_amount else 0,
            "utgst_amount": float(order.utgst_amount) if order.utgst_amount else 0,
            "total_tax_amount": float(order.total_tax_amount) if order.total_tax_amount else 0,
            
            # Agent commission
            "agent_commission_percent": float(order.agent_commission_percent) if order.agent_commission_percent else None,
            "agent_commission_amount": float(order.agent_commission_amount) if order.agent_commission_amount else 0,
            
            "roundoff": float(order.roundoff) if order.roundoff else 0,
            "net_amount": float(order.net_amount),
            
            # Currency
            "currency_id": order.currency_id,
            "exchange_rate": float(order.exchange_rate) if order.exchange_rate else 1,
            "net_amount_base": float(order.net_amount_base) if order.net_amount_base else float(order.net_amount),
            
            # Status & Reversal
            "status": order.status,
            "reversal_reason": order.reversal_reason,
            "reversed_at": order.reversed_at.isoformat() if order.reversed_at else None,
            "reversed_by": order.reversed_by,
            
            "items": [{
                "id": item.id,
                "product_id": item.product_id,
                "product_name": product.name,
                "batch_number": item.batch_number,
                "expiry_date": item.expiry_date.isoformat() if item.expiry_date else None,
                "quantity": float(item.quantity),
                "free_quantity": float(item.free_quantity) if item.free_quantity else 0,
                "mrp_price": float(item.mrp_price) if item.mrp_price else None,
                "unit_price": float(item.unit_price),
                "line_discount_percent": float(item.line_discount_percent) if item.line_discount_percent else 0,
                "line_discount_amount": float(item.line_discount_amount) if item.line_discount_amount else 0,
                
                # Tax breakdown per line
                "taxable_amount": float(item.taxable_amount),
                "cgst_rate": float(item.cgst_rate) if item.cgst_rate else 0,
                "cgst_amount": float(item.cgst_amount) if item.cgst_amount else 0,
                "sgst_rate": float(item.sgst_rate) if item.sgst_rate else 0,
                "sgst_amount": float(item.sgst_amount) if item.sgst_amount else 0,
                "igst_rate": float(item.igst_rate) if item.igst_rate else 0,
                "igst_amount": float(item.igst_amount) if item.igst_amount else 0,
                "utgst_rate": float(item.utgst_rate) if item.utgst_rate else 0,
                "utgst_amount": float(item.utgst_amount) if item.utgst_amount else 0,
                
                # Agent commission per line
                "agent_commission_percent": float(item.agent_commission_percent) if item.agent_commission_percent else None,
                "agent_commission_amount": float(item.agent_commission_amount) if item.agent_commission_amount else 0,
                
                "total_price": float(item.total_price),
                "narration": item.narration
            } for item, product in items]
        }

    return BaseResponse(
        success=True,
        message="Sales order retrieved successfully",
        data=order_data
    )


@router.post("/sales-orders/{order_id}/reverse", response_model=BaseResponse)
async def reverse_sales_order(order_id: int, reason_data: Dict[str, str], current_user: dict = Depends(get_current_user)):
    from modules.inventory_module.services.sales_order_service import SalesOrderService

    sales_order_service = SalesOrderService()
    success = sales_order_service.reverse_order(order_id, reason_data.get('reason', ''))
    if not success:
        raise HTTPException(status_code=404, detail="Sales order not found")

    return BaseResponse(success=True, message="Sales order reversed successfully")
