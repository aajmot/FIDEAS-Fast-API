from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import date
from decimal import Decimal
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse
from modules.inventory_module.models.purchase_invoice_schemas import (
    PurchaseInvoiceRequest,
    PurchaseInvoiceResponse,
    PurchaseInvoiceListResponse
)
from modules.inventory_module.services.purchase_invoice_service import PurchaseInvoiceService

router = APIRouter()
purchase_invoice_service = PurchaseInvoiceService()


@router.get("/purchase-invoices", response_model=PurchaseInvoiceListResponse)
async def get_purchase_invoices(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=500, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by invoice or reference number"),
    status: Optional[str] = Query(None, description="Filter by status"),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier"),
    date_from: Optional[date] = Query(None, description="Filter from date"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    current_user: dict = Depends(get_current_user)
):
    """Get all purchase invoices with pagination and filters"""
    result = purchase_invoice_service.get_all(
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        supplier_id=supplier_id,
        date_from=date_from,
        date_to=date_to
    )
    return result


@router.get("/purchase-invoices/{invoice_id}", response_model=PurchaseInvoiceResponse)
async def get_purchase_invoice(
    invoice_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific purchase invoice by ID"""
    invoice = purchase_invoice_service.get_by_id(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Purchase invoice not found")
    return invoice


@router.post("/purchase-invoices", response_model=PurchaseInvoiceResponse)
async def create_purchase_invoice(
    invoice: PurchaseInvoiceRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new purchase invoice"""
    try:
        result = purchase_invoice_service.create(invoice.dict())
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating purchase invoice: {str(e)}")


@router.put("/purchase-invoices/{invoice_id}", response_model=PurchaseInvoiceResponse)
async def update_purchase_invoice(
    invoice_id: int,
    invoice: PurchaseInvoiceRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing purchase invoice"""
    try:
        result = purchase_invoice_service.update(invoice_id, invoice.dict())
        if not result:
            raise HTTPException(status_code=404, detail="Purchase invoice not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating purchase invoice: {str(e)}")


@router.delete("/purchase-invoices/{invoice_id}", response_model=BaseResponse)
async def delete_purchase_invoice(
    invoice_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Soft delete a purchase invoice"""
    try:
        result = purchase_invoice_service.delete(invoice_id)
        if not result:
            raise HTTPException(status_code=404, detail="Purchase invoice not found")
        return BaseResponse(success=True, message="Purchase invoice deleted successfully", data={"id": invoice_id})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting purchase invoice: {str(e)}")


@router.post("/purchase-invoices/{invoice_id}/payment", response_model=PurchaseInvoiceResponse)
async def record_payment(
    invoice_id: int,
    payment_amount: Decimal = Query(..., gt=0, description="Payment amount"),
    current_user: dict = Depends(get_current_user)
):
    """Record a payment for a purchase invoice"""
    try:
        result = purchase_invoice_service.update_payment(invoice_id, payment_amount)
        if not result:
            raise HTTPException(status_code=404, detail="Purchase invoice not found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording payment: {str(e)}")
