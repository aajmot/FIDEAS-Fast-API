from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional

from api.schemas.common import BaseResponse, PaginatedResponse
from api.schemas.health_schema.test_invoice_schema import TestInvoiceCreateSchema, TestInvoiceUpdateSchema
from api.middleware.auth_middleware import get_current_user
from modules.health_module.services.test_invoice_service import TestInvoiceService

router = APIRouter()

@router.post("/testinvoices", response_model=BaseResponse)
async def create_test_invoice(
    invoice_data: TestInvoiceCreateSchema,
    current_user: dict = Depends(get_current_user)
):
    service = TestInvoiceService()
    invoice_dict = invoice_data.dict()
    invoice_dict["tenant_id"] = current_user["tenant_id"]
    invoice_dict["created_by"] = current_user["username"]
    
    invoice_id = service.create(invoice_dict)
    
    return BaseResponse(
        success=True,
        message="Test invoice created successfully",
        data={"id": invoice_id}
    )

@router.get("/testinvoices/{invoice_id}", response_model=BaseResponse)
async def get_test_invoice(
    invoice_id: int,
    include_barcode: bool = False,
    current_user: dict = Depends(get_current_user)
):
    service = TestInvoiceService()
    invoice_data = service.get_by_id(invoice_id, current_user["tenant_id"], include_barcode)
    
    if not invoice_data:
        raise HTTPException(status_code=404, detail="Test invoice not found")
    
    return BaseResponse(
        success=True,
        message="Test invoice retrieved successfully",
        data=invoice_data
    )

@router.get("/testinvoices", response_model=PaginatedResponse)
async def get_test_invoices(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    payment_status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    service = TestInvoiceService()
    result = service.get_all(
        tenant_id=current_user["tenant_id"],
        page=page,
        per_page=per_page,
        search=search,
        status=status,
        payment_status=payment_status
    )
    
    return PaginatedResponse(
        success=True,
        message="Test invoices retrieved successfully",
        **result
    )

@router.put("/testinvoices/{invoice_id}", response_model=BaseResponse)
async def update_test_invoice(
    invoice_id: int,
    invoice_data: TestInvoiceUpdateSchema,
    current_user: dict = Depends(get_current_user)
):
    service = TestInvoiceService()
    invoice_dict = invoice_data.dict(exclude_unset=True)
    invoice_dict["updated_by"] = current_user["username"]
    
    service.update(invoice_id, invoice_dict, current_user["tenant_id"])
    
    return BaseResponse(
        success=True,
        message="Test invoice updated successfully"
    )
