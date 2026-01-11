from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List

from api.schemas.common import BaseResponse, PaginatedResponse
from api.schemas.health_schema.appointment_invoice_schema import (
    AppointmentInvoiceCreateSchema,
    AppointmentInvoiceUpdateSchema,
    AppointmentInvoiceStatus,
    AppointmentInvoicePaymentStatus
)
from api.middleware.auth_middleware import get_current_user
from modules.health_module.services.appointment_invoice_service import AppointmentInvoiceService

router = APIRouter()

@router.post("/appointment-invoices", response_model=BaseResponse)
async def create_appointment_invoice(
    invoice_data: AppointmentInvoiceCreateSchema,
    current_user: dict = Depends(get_current_user)
):
    try:
        service = AppointmentInvoiceService()
        invoice_dict = invoice_data.dict()
        invoice_dict["tenant_id"] = current_user["tenant_id"]
        invoice_dict["created_by"] = current_user["username"]
        
        invoice_id = service.create(invoice_dict)
        
        return BaseResponse(
            success=True,
            message="Appointment invoice created successfully",
            data={"id": invoice_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/appointment-invoices/{invoice_id}", response_model=BaseResponse)
async def get_appointment_invoice(
    invoice_id: int,
    include_barcode: bool = Query(False),
    current_user: dict = Depends(get_current_user)
):
    try:
        service = AppointmentInvoiceService()
        invoice_data = service.get_by_id(invoice_id, current_user["tenant_id"], include_barcode)
        
        if not invoice_data:
            raise HTTPException(status_code=404, detail="Appointment invoice not found")
        
        return BaseResponse(
            success=True,
            message="Appointment invoice retrieved successfully",
            data=invoice_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/appointment-invoices", response_model=PaginatedResponse)
async def get_appointment_invoices(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    appointment_id: Optional[int] = Query(None),
    status: Optional[List[AppointmentInvoiceStatus]] = Query(None),
    payment_status: Optional[List[AppointmentInvoicePaymentStatus]] = Query(None),
    include_items: bool = Query(False),
    current_user: dict = Depends(get_current_user)
):
    try:
        service = AppointmentInvoiceService()
        result = service.get_all(
            tenant_id=current_user["tenant_id"],
            page=page,
            per_page=per_page,
            search=search,
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_id=appointment_id,
            status=status,
            payment_status=payment_status,
            include_items=include_items
        )
        
        return PaginatedResponse(
            success=True,
            message="Appointment invoices retrieved successfully",
            **result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/appointment-invoices/{invoice_id}", response_model=BaseResponse)
async def update_appointment_invoice(
    invoice_id: int,
    invoice_data: AppointmentInvoiceUpdateSchema,
    current_user: dict = Depends(get_current_user)
):
    try:
        service = AppointmentInvoiceService()
        invoice_dict = invoice_data.dict(exclude_unset=True)
        invoice_dict["updated_by"] = current_user["username"]
        
        service.update(invoice_id, invoice_dict, current_user["tenant_id"])
        
        return BaseResponse(
            success=True,
            message="Appointment invoice updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/appointment-invoices/{invoice_id}", response_model=BaseResponse)
async def delete_appointment_invoice(
    invoice_id: int,
    current_user: dict = Depends(get_current_user)
):
    try:
        service = AppointmentInvoiceService()
        service.delete(invoice_id, current_user["tenant_id"], current_user["username"])
        
        return BaseResponse(
            success=True,
            message="Appointment invoice deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
