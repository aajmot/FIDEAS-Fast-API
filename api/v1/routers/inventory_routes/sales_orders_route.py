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
        "total_amount": float(order.total_amount),
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
                'total_amount': order_data['order'].get('total_amount'),
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
            "customer_id": order.customer_id,
            "customer_name": customer.name if customer else "",
            "agency_id": order.agency_id,
            "agency_name": agency_name,
            "order_date": order.order_date.isoformat() if order.order_date else None,
            "total_amount": float(order.total_amount),
            "discount_percent": float(order.discount_percent) if hasattr(order, 'discount_percent') else 0,
            "discount_amount": float(order.discount_amount) if hasattr(order, 'discount_amount') else 0,
            "roundoff": float(order.roundoff) if hasattr(order, 'roundoff') else 0,
            "status": order.status,
            "items": [{
                "id": item.id,
                "product_id": item.product_id,
                "product_name": product.name,
                "quantity": float(item.quantity),
                "free_quantity": float(getattr(item, 'free_quantity', 0)),
                "unit_price": float(item.unit_price) if getattr(item, 'unit_price', None) is not None else None,
                "mrp": float(item.mrp) if getattr(item, 'mrp', None) is not None else None,
                "gst_rate": float(item.gst_rate) if getattr(item, 'gst_rate', None) is not None else 0,
                "gst_amount": float(item.gst_amount) if getattr(item, 'gst_amount', None) is not None else None,
                "cgst_amount": float(item.cgst_amount) if getattr(item, 'cgst_amount', None) is not None else None,
                "sgst_amount": float(item.sgst_amount) if getattr(item, 'sgst_amount', None) is not None else None,
                "cgst_rate": float(item.cgst_rate) if getattr(item, 'cgst_rate', None) is not None else 0,
                "sgst_rate": float(item.sgst_rate) if getattr(item, 'sgst_rate', None) is not None else 0,
                "discount_percent": float(item.discount_percent) if getattr(item, 'discount_percent', None) is not None else 0,
                "discount_amount": float(item.discount_amount) if getattr(item, 'discount_amount', None) is not None else 0,
                "total_amount": float(item.total_price) if getattr(item, 'total_price', None) is not None else None,
                "description": getattr(item, 'description', None),
                "batch_number": getattr(item, 'batch_number', '')
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
