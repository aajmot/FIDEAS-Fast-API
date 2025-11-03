from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.schemas.purchase_orders import PurchaseOrderRequest
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
        "reference_number": order.reference_number,
        "supplier_id": order.supplier_id,
        "supplier_name": order.supplier_name,
        "supplier_gstin": order.supplier_gstin,
        "order_date": order.order_date.isoformat() if order.order_date else None,
        
        # Amount breakdown
        "subtotal_amount": float(order.subtotal_amount) if order.subtotal_amount else 0,
        "header_discount_percent": float(order.header_discount_percent) if order.header_discount_percent else 0,
        "header_discount_amount": float(order.header_discount_amount) if order.header_discount_amount else 0,
        "taxable_amount": float(order.taxable_amount) if order.taxable_amount else 0,
        
        # Tax breakdown
        "cgst_amount": float(order.cgst_amount) if order.cgst_amount else 0,
        "sgst_amount": float(order.sgst_amount) if order.sgst_amount else 0,
        "igst_amount": float(order.igst_amount) if order.igst_amount else 0,
        "cess_amount": float(order.cess_amount) if order.cess_amount else 0,
        "total_tax_amount": float(order.total_tax_amount) if order.total_tax_amount else 0,
        
        "roundoff": float(order.roundoff) if order.roundoff else 0,
        "net_amount": float(order.net_amount) if order.net_amount else 0,
        
        # Currency
        "currency_id": order.currency_id if hasattr(order, 'currency_id') else 1,
        "exchange_rate": float(order.exchange_rate) if hasattr(order, 'exchange_rate') and order.exchange_rate else 1,
        "net_amount_base": float(order.net_amount_base) if hasattr(order, 'net_amount_base') and order.net_amount_base else float(order.net_amount),
        
        # Tax & RCM
        "is_reverse_charge": order.is_reverse_charge if hasattr(order, 'is_reverse_charge') else False,
        "is_tax_inclusive": order.is_tax_inclusive if hasattr(order, 'is_tax_inclusive') else False,
        
        # Status
        "status": order.status,
        "approval_status": order.approval_status,
        "approval_request_id": order.approval_request_id if hasattr(order, 'approval_request_id') else None,
        
        # Reversal
        "reversal_reason": order.reversal_reason if hasattr(order, 'reversal_reason') else None,
        "reversed_at": order.reversed_at.isoformat() if hasattr(order, 'reversed_at') and order.reversed_at else None,
        "reversed_by": order.reversed_by if hasattr(order, 'reversed_by') else None,
        
        # Audit
        "created_at": order.created_at.isoformat() if hasattr(order, 'created_at') and order.created_at else None,
        "created_by": order.created_by if hasattr(order, 'created_by') else None,
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
async def create_purchase_order(order_data: PurchaseOrderRequest, current_user: dict = Depends(get_current_user)):
    from modules.inventory_module.services.purchase_order_service import PurchaseOrderService
    from modules.account_module.services.transaction_posting_service import TransactionPostingService
    from core.database.connection import db_manager

    with db_manager.get_session() as session:
        purchase_order_service = PurchaseOrderService()
        
        # Split the data into order and items
        # Exclude generated columns that are computed by the database
        order_dict = order_data.model_dump(exclude={'total_tax_amount', 'net_amount_base', 'items'})
        items = [item.model_dump() for item in order_data.items]
        
        # Create the order
        order_id = purchase_order_service.create_with_items(order_dict, items)

        # Post to accounting
        try:
            posting_data = {
                'reference_type': 'PURCHASE_ORDER',
                'reference_id': order_id,
                'reference_number': order_dict['po_number'],
                'total_amount': float(order_dict['net_amount']),
                'transaction_date': order_dict['order_date'],
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
            "reference_number": order.reference_number,
            "supplier_id": order.supplier_id,
            "supplier_name": supplier.name if supplier else order.supplier_name,
            "supplier_gstin": order.supplier_gstin,
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
            "cess_amount": float(order.cess_amount) if order.cess_amount else 0,
            "total_tax_amount": float(order.total_tax_amount) if order.total_tax_amount else 0,
            
            "roundoff": float(order.roundoff) if order.roundoff else 0,
            "net_amount": float(order.net_amount),
            
            # Currency
            "currency_id": order.currency_id,
            "exchange_rate": float(order.exchange_rate) if order.exchange_rate else 1,
            "net_amount_base": float(order.net_amount_base) if order.net_amount_base else float(order.net_amount),
            
            # Tax & RCM
            "is_reverse_charge": order.is_reverse_charge,
            "is_tax_inclusive": order.is_tax_inclusive,
            
            # Status
            "status": order.status,
            "approval_status": order.approval_status,
            "approval_request_id": order.approval_request_id,
            
            # Reversal
            "reversal_reason": order.reversal_reason,
            "reversed_at": order.reversed_at.isoformat() if order.reversed_at else None,
            "reversed_by": order.reversed_by,
            
            "items": [{
                "id": item.id,
                "product_id": item.product_id,
                "product_name": product.name,
                "hsn_code": item.hsn_code,
                "description": item.description,
                "quantity": float(item.quantity),
                "free_quantity": float(item.free_quantity) if item.free_quantity else 0,
                "unit_price": float(item.unit_price),
                "mrp": float(item.mrp) if item.mrp else None,
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
                "cess_rate": float(item.cess_rate) if item.cess_rate else 0,
                "cess_amount": float(item.cess_amount) if item.cess_amount else 0,
                
                "total_price": float(item.total_price),
                "batch_number": item.batch_number,
                "expiry_date": item.expiry_date.isoformat() if item.expiry_date else None,
                "is_active": item.is_active
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
