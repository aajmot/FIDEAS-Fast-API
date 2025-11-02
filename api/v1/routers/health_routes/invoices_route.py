from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
import io
import csv
from datetime import datetime

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from sqlalchemy import or_
import math
from api.middleware.auth_middleware import get_current_user
from modules.clinic_module.services.patient_service import PatientService
from modules.clinic_module.services.doctor_service import DoctorService
from modules.clinic_module.services.appointment_service import AppointmentService
from modules.clinic_module.services.medical_record_service import MedicalRecordService
from modules.admin_module.models.agency import Agency

router = APIRouter()

# Billing endpoints
@router.get("/invoices", response_model=PaginatedResponse)
async def get_invoices(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.clinic_module.models.entities import Invoice, Patient
    
    with db_manager.get_session() as session:
        query = session.query(Invoice).outerjoin(Patient).filter(
            Invoice.tenant_id == current_user.get('tenant_id', 1)
        )
        
        if pagination.search:
            query = query.filter(or_(
                Invoice.invoice_number.ilike(f"%{pagination.search}%"),
                Invoice.payment_status.ilike(f"%{pagination.search}%")
            ))
        
        total = query.count()
        invoices = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        invoice_data = []
        for invoice in invoices:
            try:
                data = {
                    "id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "appointment_number": invoice.appointment.appointment_number if hasattr(invoice, 'appointment') and invoice.appointment else None,
                    "patient_id": invoice.patient_id,
                    "patient_name": f"{invoice.patient.first_name} {invoice.patient.last_name}" if hasattr(invoice, 'patient') and invoice.patient else f"Patient {invoice.patient_id}",
                    "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
                    "consultation_fee": float(invoice.consultation_fee) if invoice.consultation_fee else 0,
                    "discount_percentage": float(invoice.discount_percentage) if invoice.discount_percentage else 0,
                    "discount_amount": float(invoice.discount_amount) if invoice.discount_amount else 0,
                    "total_amount": float(invoice.total_amount) if invoice.total_amount else 0,
                    "final_amount": float(invoice.final_amount) if invoice.final_amount else 0,
                    "payment_status": invoice.payment_status,
                    "payment_method": invoice.payment_method,
                    "created_at": invoice.created_at.isoformat() if invoice.created_at else None
                }
                invoice_data.append(data)
            except Exception:
                continue
    
    return PaginatedResponse(
        success=True,
        message="Invoices retrieved successfully",
        data=invoice_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/invoices", response_model=BaseResponse)
async def create_invoice(invoice_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from modules.clinic_module.services.billing_service import BillingService
    from modules.account_module.services.transaction_posting_service import TransactionPostingService
    from core.database.connection import db_manager
    
    billing_service = BillingService()
    if 'tenant_id' not in invoice_data:
        invoice_data['tenant_id'] = current_user.get('tenant_id', 1)
    
    # Extract items from invoice data
    items_data = invoice_data.pop('items', [])
    
    invoice = billing_service.create_invoice(invoice_data, items_data)
    
    # Post to accounting
    try:
        with db_manager.get_session() as session:
            posting_data = {
                'reference_type': 'CLINIC_INVOICE',
                'reference_id': invoice.id,
                'reference_number': invoice.invoice_number,
                'total_amount': float(invoice.final_amount),
                'transaction_date': invoice.invoice_date,
                'created_by': current_user['username']
            }
            TransactionPostingService.post_transaction(
                session, 'CLINIC_BILL', posting_data, current_user['tenant_id']
            )
            session.commit()
    except Exception as e:
        print(f"Accounting posting failed for invoice: {e}")
    
    return BaseResponse(
        success=True,
        message="Invoice created successfully",
        data={"id": invoice.id}
    )

@router.get("/invoices/{invoice_id}", response_model=BaseResponse)
async def get_invoice(invoice_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.clinic_module.models.entities import Invoice, InvoiceItem, Patient, Appointment
    
    with db_manager.get_session() as session:
        from modules.clinic_module.models.entities import Doctor
        
        invoice = session.query(Invoice).outerjoin(Patient).outerjoin(Appointment).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Get patient and doctor details through appointment if available
        patient_phone = None
        doctor_name = None
        
        if invoice.appointment_id:
            appointment = session.query(Appointment).outerjoin(Patient).outerjoin(Doctor).filter(Appointment.id == invoice.appointment_id).first()
            if appointment:
                if appointment.patient:
                    patient_phone = appointment.patient.phone
                if appointment.doctor:
                    doctor_name = f"{appointment.doctor.first_name} {appointment.doctor.last_name}"
        
        # Get invoice items
        items = session.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice_id).all()
        
        items_data = []
        for item in items:
            items_data.append({
                "id": item.id,
                "item_type": item.item_type,
                "description": item.description,
                "quantity": float(item.quantity) if item.quantity else 1,
                "unit_price": float(item.unit_price) if item.unit_price else 0,
                "total_price": float(item.total_price) if item.total_price else 0
            })
        
        invoice_data = {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "appointment_number": invoice.appointment.appointment_number if hasattr(invoice, 'appointment') and invoice.appointment else None,
            "patient_id": invoice.patient_id,
            "patient_name": f"{invoice.patient.first_name} {invoice.patient.last_name}" if hasattr(invoice, 'patient') and invoice.patient else f"Patient {invoice.patient_id}",
            "patient_phone": patient_phone,
            "doctor_name": doctor_name,
            "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
            "consultation_fee": float(invoice.consultation_fee) if invoice.consultation_fee else 0,
            "discount_percentage": float(invoice.discount_percentage) if invoice.discount_percentage else 0,
            "discount_amount": float(invoice.discount_amount) if invoice.discount_amount else 0,
            "total_amount": float(invoice.total_amount) if invoice.total_amount else 0,
            "final_amount": float(invoice.final_amount) if invoice.final_amount else 0,
            "payment_status": invoice.payment_status,
            "payment_method": invoice.payment_method,
            "items": items_data,
            "created_at": invoice.created_at.isoformat() if invoice.created_at else None
        }
    
    return BaseResponse(
        success=True,
        message="Invoice retrieved successfully",
        data=invoice_data
    )

@router.put("/invoices/{invoice_id}", response_model=BaseResponse)
async def update_invoice(invoice_id: int, invoice_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from modules.clinic_module.services.billing_service import BillingService
    
    billing_service = BillingService()
    
    # Extract items from invoice data
    items_data = invoice_data.pop('items', None)
    
    invoice = billing_service.update(invoice_id, invoice_data, items_data)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return BaseResponse(
        success=True,
        message="Invoice updated successfully",
        data={"id": invoice.id}
    )

@router.delete("/invoices/{invoice_id}", response_model=BaseResponse)
async def delete_invoice(invoice_id: int, current_user: dict = Depends(get_current_user)):
    from modules.clinic_module.services.billing_service import BillingService
    
    billing_service = BillingService()
    success = billing_service.delete(invoice_id)
    if not success:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return BaseResponse(
        success=True,
        message="Invoice deleted successfully"
    )