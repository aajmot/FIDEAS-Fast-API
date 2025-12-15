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
# Appointment endpoints
@router.get("/appointments", response_model=PaginatedResponse)
async def get_appointments(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.clinic_module.models.entities import Appointment, Patient, Doctor
    
    with db_manager.get_session() as session:
        query = session.query(Appointment)
        
        # Only filter by tenant_id if it's provided and not None
        tenant_id = current_user.get('tenant_id')
        if tenant_id is not None:
            query = query.filter(Appointment.tenant_id == tenant_id)
        
        query = query.order_by(Appointment.appointment_date.desc(), Appointment.created_at.desc())
        
        if pagination.search:
            query = query.filter(or_(
                Appointment.appointment_number.ilike(f"%{pagination.search}%"),
                Appointment.status.ilike(f"%{pagination.search}%"),
                Appointment.notes.ilike(f"%{pagination.search}%")
            ))
        
        total = query.count()
        appointments = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        appointment_data = []
        for appointment in appointments:
            try:
                data = {
                    "id": appointment.id,
                    "appointment_number": appointment.appointment_number,
                    "patient_id": appointment.patient_id,
                    "patient_name": f"{appointment.patient.first_name} {appointment.patient.last_name}" if hasattr(appointment, 'patient') and appointment.patient else f"Patient {appointment.patient_id}",
                    "patient_phone": appointment.patient.phone if hasattr(appointment, 'patient') and appointment.patient else None,
                    "doctor_id": appointment.doctor_id,
                    "doctor_name": f"{appointment.doctor.first_name} {appointment.doctor.last_name}" if hasattr(appointment, 'doctor') and appointment.doctor else f"Doctor {appointment.doctor_id}",
                    "doctor_phone": appointment.doctor.phone if hasattr(appointment, 'doctor') and appointment.doctor else None,
                    "doctor_license_number": appointment.doctor.license_number if hasattr(appointment, 'doctor') and appointment.doctor else None,
                    "agency_id": appointment.agency_id,
                    "appointment_date": appointment.appointment_date.isoformat() if appointment.appointment_date else None,
                    "appointment_time": appointment.appointment_time.strftime("%H:%M") if appointment.appointment_time else None,
                    "duration_minutes": appointment.duration_minutes,
                    "status": appointment.status,
                    "reason": appointment.reason,
                    "notes": appointment.notes,
                    "created_at": appointment.created_at.isoformat() if appointment.created_at else None
                }
                appointment_data.append(data)
            except Exception:
                # Skip appointments with missing relations
                continue
    
    return PaginatedResponse(
        success=True,
        message="Appointments retrieved successfully",
        data=appointment_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/appointments", response_model=BaseResponse)
async def create_appointment(appointment_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    appointment_service = AppointmentService()
    # Always use tenant_id from logged-in user, never from request
    appointment_data['tenant_id'] = current_user.get('tenant_id')
    appointment_data['created_by'] = current_user.get('username')
    appointment = appointment_service.create(appointment_data)
    return BaseResponse(
        success=True,
        message="Appointment created successfully",
        data={"id": appointment.id, "appointment_number": appointment.appointment_number}
    )

@router.get("/appointments/export-template")
async def export_appointments_template(current_user: dict = Depends(get_current_user)):
    appointment_service = AppointmentService()
    template_content = appointment_service.export_template()
    
    return StreamingResponse(
        io.BytesIO(template_content.encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=appointments_import_template.csv"}
    )

@router.post("/appointments/import", response_model=BaseResponse)
async def import_appointments(request_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    appointment_service = AppointmentService()
    csv_content = request_data.get('csv_content', '')
    
    if not csv_content:
        raise HTTPException(status_code=400, detail="CSV content is required")
    
    result = appointment_service.import_appointments(csv_content, current_user.get('tenant_id'))
    
    return BaseResponse(
        success=True,
        message=f"Imported {result['imported']} appointments successfully",
        data=result
    )

@router.get("/appointments/{appointment_identifier}", response_model=BaseResponse)
async def get_appointment(appointment_identifier: str, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.clinic_module.models.entities import Appointment, Patient, Doctor
    
    with db_manager.get_session() as session:
        # Try to find by ID first (if it's numeric), then by appointment number
        if appointment_identifier.isdigit():
            appointment = session.query(Appointment).join(Patient).join(Doctor).filter(Appointment.id == int(appointment_identifier)).first()
        else:
            appointment = session.query(Appointment).join(Patient).join(Doctor).filter(Appointment.appointment_number == appointment_identifier).first()
        
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        appointment_data = {
            "id": appointment.id,
            "appointment_number": appointment.appointment_number,
            "patient_id": appointment.patient_id,
            "patient_name": f"{appointment.patient.first_name} {appointment.patient.last_name}",
            "patient_phone": appointment.patient.phone if appointment.patient else None,
            "doctor_id": appointment.doctor_id,
            "doctor_name": f"{appointment.doctor.first_name} {appointment.doctor.last_name}",
            "doctor_phone": appointment.doctor.phone if appointment.doctor else None,
            "doctor_license_number": appointment.doctor.license_number if appointment.doctor else None,
            "agency_id": appointment.agency_id,
            "appointment_date": appointment.appointment_date.isoformat() if appointment.appointment_date else None,
            "appointment_time": appointment.appointment_time.strftime("%H:%M") if appointment.appointment_time else None,
            "duration_minutes": appointment.duration_minutes,
            "status": appointment.status,
            "reason": appointment.reason,
            "notes": appointment.notes,
            "created_at": appointment.created_at.isoformat() if appointment.created_at else None
        }
    
    return BaseResponse(
        success=True,
        message="Appointment retrieved successfully",
        data=appointment_data
    )

@router.put("/appointments/{appointment_id}", response_model=BaseResponse)
async def update_appointment(appointment_id: int, appointment_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.clinic_module.models.entities import Appointment
    
    with db_manager.get_session() as session:
        appointment = session.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        for key, value in appointment_data.items():
            if hasattr(appointment, key):
                setattr(appointment, key, value)
        
        session.commit()
        appointment_id_result = appointment.id
    
    return BaseResponse(
        success=True,
        message="Appointment updated successfully",
        data={"id": appointment_id_result}
    )

@router.delete("/appointments/{appointment_id}", response_model=BaseResponse)
async def delete_appointment(appointment_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.clinic_module.models.entities import Appointment
    
    with db_manager.get_session() as session:
        appointment = session.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        session.delete(appointment)
    
    return BaseResponse(
        success=True,
        message="Appointment deleted successfully"
    )
