from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import date
from decimal import Decimal
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse
from modules.inventory_module.models.sales_invoice_schemas import (
    SalesInvoiceRequest,
    SalesInvoiceResponse,
    SalesInvoiceListResponse,
    EInvoiceGenerateRequest,
    EWayBillGenerateRequest
)
from modules.inventory_module.services.sales_invoice_service import SalesInvoiceService

router = APIRouter()
sales_invoice_service = SalesInvoiceService()


@router.get("/sales-invoices", response_model=SalesInvoiceListResponse)
async def get_sales_invoices(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=500, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by invoice or reference number"),
    status: Optional[str] = Query(None, description="Filter by status"),
    customer_id: Optional[int] = Query(None, description="Filter by customer"),
    invoice_type: Optional[str] = Query(None, description="Filter by invoice type"),
    date_from: Optional[date] = Query(None, description="Filter from date"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    current_user: dict = Depends(get_current_user)
):
    """Get all sales invoices with pagination and filters"""
    result = sales_invoice_service.get_all(
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        customer_id=customer_id,
        invoice_type=invoice_type,
        date_from=date_from,
        date_to=date_to
    )
    return result


@router.get("/sales-invoices/{invoice_id}", response_model=SalesInvoiceResponse)
async def get_sales_invoice(
    invoice_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific sales invoice by ID"""
    invoice = sales_invoice_service.get_by_id(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Sales invoice not found")
    return invoice


@router.post("/sales-invoices", response_model=SalesInvoiceResponse)
async def create_sales_invoice(
    invoice: SalesInvoiceRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new sales invoice"""
    try:
        result = sales_invoice_service.create(invoice.dict())
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating sales invoice: {str(e)}")


@router.put("/sales-invoices/{invoice_id}", response_model=SalesInvoiceResponse)
async def update_sales_invoice(
    invoice_id: int,
    invoice: SalesInvoiceRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing sales invoice"""
    try:
        result = sales_invoice_service.update(invoice_id, invoice.dict())
        if not result:
            raise HTTPException(status_code=404, detail="Sales invoice not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating sales invoice: {str(e)}")


@router.delete("/sales-invoices/{invoice_id}", response_model=BaseResponse)
async def delete_sales_invoice(
    invoice_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Soft delete a sales invoice"""
    try:
        result = sales_invoice_service.delete(invoice_id)
        if not result:
            raise HTTPException(status_code=404, detail="Sales invoice not found")
        return BaseResponse(success=True, message="Sales invoice deleted successfully", data={"id": invoice_id})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting sales invoice: {str(e)}")


@router.post("/sales-invoices/{invoice_id}/payment", response_model=SalesInvoiceResponse)
async def record_payment(
    invoice_id: int,
    payment_amount: Decimal = Query(..., gt=0, description="Payment amount"),
    current_user: dict = Depends(get_current_user)
):
    """Record a payment for a sales invoice"""
    try:
        result = sales_invoice_service.update_payment(invoice_id, payment_amount)
        if not result:
            raise HTTPException(status_code=404, detail="Sales invoice not found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording payment: {str(e)}")
