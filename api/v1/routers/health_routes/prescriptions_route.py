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
from modules.health_module.services.patient_service import PatientService
from modules.health_module.services.doctor_service import DoctorService
from modules.health_module.services.appointment_service import AppointmentService
from modules.health_module.services.medical_record_service import MedicalRecordService
from modules.admin_module.models.agency import Agency

router = APIRouter()
# Prescription endpoints
@router.get("/prescriptions", response_model=PaginatedResponse)
async def get_prescriptions(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.health_module.models.clinic_entities import Prescription, Patient, Doctor, Appointment
    
    with db_manager.get_session() as session:
        query = session.query(Prescription).outerjoin(Patient).outerjoin(Doctor).outerjoin(Appointment).filter(
            Prescription.tenant_id == current_user.get('tenant_id')
        )
        
        if pagination.search:
            search_term = f"%{pagination.search}%"
            query = query.filter(or_(
                Prescription.prescription_number.ilike(search_term),
                Prescription.instructions.ilike(search_term),
                Patient.first_name.ilike(search_term),
                Patient.last_name.ilike(search_term),
                Doctor.first_name.ilike(search_term),
                Doctor.last_name.ilike(search_term)
            ))
        
        total = query.count()
        prescriptions = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        prescription_data = []
        for prescription in prescriptions:
            try:
                data = {
                    "id": prescription.id,
                    "prescription_number": prescription.prescription_number,
                    "appointment_id": prescription.appointment.appointment_number if hasattr(prescription, 'appointment') and prescription.appointment else prescription.appointment_id,
                    "patient_id": prescription.patient_id,
                    "patient_name": f"{prescription.patient.first_name} {prescription.patient.last_name}" if hasattr(prescription, 'patient') and prescription.patient else f"Patient {prescription.patient_id}",
                    "doctor_id": prescription.doctor_id,
                    "doctor_name": f"{prescription.doctor.first_name} {prescription.doctor.last_name}" if hasattr(prescription, 'doctor') and prescription.doctor else f"Doctor {prescription.doctor_id}",
                    "prescription_date": prescription.prescription_date.isoformat() if prescription.prescription_date else None,
                    "instructions": prescription.instructions,
                    "created_at": prescription.created_at.isoformat() if prescription.created_at else None
                }
                prescription_data.append(data)
            except Exception:
                continue
    
    return PaginatedResponse(
        success=True,
        message="Prescriptions retrieved successfully",
        data=prescription_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/prescriptions", response_model=BaseResponse)
async def create_prescription(prescription_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from modules.health_module.services.prescription_service import PrescriptionService
    from modules.account_module.services.transaction_posting_service import TransactionPostingService
    from core.database.connection import db_manager
    
    prescription_service = PrescriptionService()
    # Always use tenant_id from logged-in user, never from request
    prescription_data['tenant_id'] = current_user.get('tenant_id')
    
    # Extract items from prescription data
    items_data = prescription_data.pop('items', [])
    test_items_data = prescription_data.pop('test_items', [])
    
    # Add created_by to items (PrescriptionItem has created_by)
    for item in items_data:
        item['created_by'] = current_user.get('username')
    
    # Add created_by and tenant_id to test items
    for test_item in test_items_data:
        test_item['created_by'] = current_user.get('username')
        test_item['tenant_id'] = current_user.get('tenant_id')
    
    prescription = prescription_service.create(prescription_data, items_data, test_items_data)
    
    return BaseResponse(
        success=True,
        message="Prescription created successfully",
        data={"id": prescription.id}
    )

@router.put("/prescriptions/{prescription_id}", response_model=BaseResponse)
async def update_prescription(prescription_id: int, prescription_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from modules.health_module.services.prescription_service import PrescriptionService
    
    prescription_service = PrescriptionService()
    
    # Extract items from prescription data
    items_data = prescription_data.pop('items', None)
    test_items_data = prescription_data.pop('test_items', None)
    
    # Add updated_by to items
    if items_data:
        for item in items_data:
            item['updated_by'] = current_user.get('username')
    
    # Add updated_by and tenant_id to test items
    if test_items_data:
        for test_item in test_items_data:
            test_item['updated_by'] = current_user.get('username')
            test_item['tenant_id'] = current_user.get('tenant_id')
    
    prescription = prescription_service.update(prescription_id, prescription_data, items_data, test_items_data)
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return BaseResponse(
        success=True,
        message="Prescription updated successfully",
        data={"id": prescription.id}
    )

@router.delete("/prescriptions/{prescription_id}", response_model=BaseResponse)
async def delete_prescription(prescription_id: int, current_user: dict = Depends(get_current_user)):
    from modules.health_module.services.prescription_service import PrescriptionService
    
    prescription_service = PrescriptionService()
    success = prescription_service.delete(prescription_id, current_user.get('tenant_id'))
    if not success:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return BaseResponse(
        success=True,
        message="Prescription deleted successfully"
    )

@router.get("/prescriptions/{prescription_id}", response_model=BaseResponse)
async def get_prescription(prescription_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.health_module.models.clinic_entities import Prescription, PrescriptionItem, PrescriptionTestItem, Patient, Doctor
    from modules.inventory_module.models.clinic_entities import Product
    from modules.health_module.models.clinic_entities import Test
    
    with db_manager.get_session() as session:
        prescription = session.query(Prescription).outerjoin(Patient).outerjoin(Doctor).filter(Prescription.id == prescription_id).first()
        if not prescription:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        # Get prescription items with product details
        items = session.query(PrescriptionItem, Product).join(Product, PrescriptionItem.product_id == Product.id).filter(
            PrescriptionItem.prescription_id == prescription_id,
            PrescriptionItem.is_deleted == False
        ).all()
        
        items_data = []
        for item, product in items:
            items_data.append({
                "id": item.id,
                "product_id": item.product_id,
                "product_name": product.name if product else f"Product {item.product_id}",
                "dosage": item.dosage,
                "frequency": item.frequency,
                "duration": item.duration,
                "quantity": float(item.quantity) if item.quantity else None,
                "instructions": item.instructions
            })
        
        # Get prescription test items
        test_items = session.query(PrescriptionTestItem, Test).join(Test, PrescriptionTestItem.test_id == Test.id).filter(
            PrescriptionTestItem.prescription_id == prescription_id,
            PrescriptionTestItem.is_deleted == False
        ).all()
        
        test_items_data = []
        for test_item, test in test_items:
            test_items_data.append({
                "id": test_item.id,
                "test_id": test_item.test_id,
                "test_name": test.name if test else test_item.test_name,
                "instructions": test_item.instructions
            })
        
        # Calculate patient age if date_of_birth exists
        patient_age = None
        if hasattr(prescription, 'patient') and prescription.patient and prescription.patient.date_of_birth:
            from datetime import date
            today = date.today()
            dob = prescription.patient.date_of_birth
            patient_age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        
        # Get appointment number if appointment exists
        appointment_number = None
        if prescription.appointment_id:
            from modules.health_module.models.clinic_entities import Appointment
            appointment = session.query(Appointment).filter(Appointment.id == prescription.appointment_id).first()
            if appointment:
                appointment_number = appointment.appointment_number
        
        prescription_data = {
            "id": prescription.id,
            "prescription_number": prescription.prescription_number,
            "appointment_id": prescription.appointment_id,
            "appointment_number": appointment_number,
            "patient_id": prescription.patient_id,
            "patient_name": f"{prescription.patient.first_name} {prescription.patient.last_name}" if hasattr(prescription, 'patient') and prescription.patient else f"Patient {prescription.patient_id}",
            "patient_phone": prescription.patient.phone if hasattr(prescription, 'patient') and prescription.patient else None,
            "patient_age": patient_age,
            "doctor_id": prescription.doctor_id,
            "doctor_name": f"{prescription.doctor.first_name} {prescription.doctor.last_name}" if hasattr(prescription, 'doctor') and prescription.doctor else f"Doctor {prescription.doctor_id}",
            "doctor_license_number": prescription.doctor.license_number if hasattr(prescription, 'doctor') and prescription.doctor else None,
            "prescription_date": prescription.prescription_date.isoformat() if prescription.prescription_date else None,
            "instructions": prescription.instructions,
            "items": items_data,
            "test_items": test_items_data,
            "created_at": prescription.created_at.isoformat() if prescription.created_at else None
        }
    
    return BaseResponse(
        success=True,
        message="Prescription retrieved successfully",
        data=prescription_data
    )
