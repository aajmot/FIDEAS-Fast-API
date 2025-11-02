from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.get("/purchase-orders", response_model=PaginatedResponse)
async def get_purchase_orders(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from modules.inventory_module.services.purchase_order_service import PurchaseOrderService

    purchase_order_service = PurchaseOrderService()
    orders = purchase_order_service.get_all(page=pagination.page, page_size=pagination.per_page)
    total = purchase_order_service.get_total_count()

    order_data = [{
        "id": order.id,
        "po_number": order.po_number,
        "supplier_name": order.supplier_name,
        "order_date": order.order_date.isoformat() if order.order_date else None,
        "total_amount": float(order.total_amount),
        "status": order.status
    } for order in orders]

    return PaginatedResponse(
        success=True,
        message="Purchase orders retrieved successfully",
        data=order_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )


@router.post("/purchase-orders", response_model=BaseResponse)
async def create_purchase_order(order_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from modules.inventory_module.services.purchase_order_service import PurchaseOrderService
    from modules.account_module.services.transaction_posting_service import TransactionPostingService
    from core.database.connection import db_manager

    with db_manager.get_session() as session:
        purchase_order_service = PurchaseOrderService()
        order_id = purchase_order_service.create_with_items(order_data['order'], order_data['items'])

        # Post to accounting
        try:
            posting_data = {
                'reference_type': 'PURCHASE_ORDER',
                'reference_id': order_id,
                'reference_number': order_data['order'].get('po_number'),
                'total_amount': order_data['order'].get('total_amount'),
                'transaction_date': order_data['order'].get('order_date'),
                'created_by': current_user['username']
            }
            voucher_id = TransactionPostingService.post_transaction(
                session, 'PURCHASE_ORDER', posting_data, current_user['tenant_id']
            )
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Accounting posting failed: {e}")

        return BaseResponse(
            success=True,
            message="Purchase order created successfully",
            data={"id": order_id}
        )


@router.get("/purchase-orders/{order_id}", response_model=BaseResponse)
async def get_purchase_order(order_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.inventory_module.models.entities import PurchaseOrder, PurchaseOrderItem, Product, Supplier

    with db_manager.get_session() as session:
        order = session.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Purchase order not found")

        items = session.query(PurchaseOrderItem, Product).join(Product).filter(
            PurchaseOrderItem.purchase_order_id == order_id
        ).all()

        supplier = session.query(Supplier).filter(Supplier.id == order.supplier_id).first()

        order_data = {
            "id": order.id,
            "po_number": order.po_number,
            "supplier_id": order.supplier_id,
            "supplier_name": supplier.name if supplier else "",
            "order_date": order.order_date.isoformat() if order.order_date else None,
            "total_amount": float(order.total_amount),
            "discount_percent": float(order.discount_percent),
            "discount_amount": float(order.discount_amount),
            "roundoff": float(order.roundoff),
            "status": order.status,
            "items": [{
                "id": item.id,
                "product_id": item.product_id,
                "product_name": product.name,
                "quantity": float(item.quantity),
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
                "total_amount": float(item.total_amount) if getattr(item, 'total_amount', None) is not None else None,
                "description": getattr(item, 'description', None)
            } for item, product in items]
        }

    return BaseResponse(
        success=True,
        message="Purchase order retrieved successfully",
        data=order_data
    )


@router.post("/purchase-orders/{order_id}/reverse", response_model=BaseResponse)
async def reverse_purchase_order(order_id: int, reason_data: Dict[str, str], current_user: dict = Depends(get_current_user)):
    from modules.inventory_module.services.purchase_order_service import PurchaseOrderService

    purchase_order_service = PurchaseOrderService()
    success = purchase_order_service.reverse_order(order_id, reason_data.get('reason', ''))
    if not success:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    return BaseResponse(success=True, message="Purchase order reversed successfully")
