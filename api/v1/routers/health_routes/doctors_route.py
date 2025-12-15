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

# Doctor endpoints
@router.get("/doctors", response_model=PaginatedResponse)
async def get_doctors(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.clinic_module.models.entities import Doctor
    
    with db_manager.get_session() as session:
        query = session.query(Doctor).filter(
            Doctor.is_active == True,
            Doctor.tenant_id == current_user.get('tenant_id', 1)
        )
        
        if pagination.search:
            search_term = f"%{pagination.search}%"
            query = query.filter(or_(
                Doctor.employee_id.ilike(search_term),
                Doctor.first_name.ilike(search_term),
                Doctor.last_name.ilike(search_term),
                Doctor.email.ilike(search_term),
                Doctor.specialization.ilike(search_term),
                Doctor.license_number.ilike(search_term)
            ))
        
        total = query.count()
        doctors = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        doctor_data = [{
            "id": doctor.id,
            "doctor_id": doctor.employee_id,
            "first_name": doctor.first_name,
            "last_name": doctor.last_name,
            "email": doctor.email,
            "phone": doctor.phone,
            "specialization": doctor.specialization,
            "license_number": doctor.license_number,
            "schedule_start": doctor.schedule_start.strftime("%H:%M") if doctor.schedule_start else None,
            "schedule_end": doctor.schedule_end.strftime("%H:%M") if doctor.schedule_end else None,
            "consultation_fee": float(doctor.consultation_fee) if doctor.consultation_fee else None,
            "is_active": doctor.is_active,
            "created_at": doctor.created_at.isoformat() if doctor.created_at else None
        } for doctor in doctors]
    
    return PaginatedResponse(
        success=True,
        message="Doctors retrieved successfully",
        data=doctor_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/doctors", response_model=BaseResponse)
async def create_doctor(doctor_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    doctor_service = DoctorService()
    # Always use tenant_id from logged-in user, never from request
    doctor_data['tenant_id'] = current_user.get('tenant_id')
    doctor = doctor_service.create(doctor_data)
    return BaseResponse(
        success=True,
        message="Doctor created successfully",
        data={"id": doctor.id}
    )

@router.get("/doctors/export-template")
async def export_doctors_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["first_name", "last_name", "email", "phone", "specialization", "license_number", "schedule_start", "schedule_end", "consultation_fee"])
    writer.writerow(["Dr. Jane", "Smith", "jane@clinic.com", "123-456-7890", "Cardiology", "LIC123456", "09:00", "17:00", "500.00"])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=doctors_template.csv"}
    )

@router.post("/doctors/import", response_model=BaseResponse)
async def import_doctors(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    doctor_service = DoctorService()
    imported_count = 0
    
    for row in csv_data:
        try:
            doctor_data = {
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "email": row.get("email", ""),
                "phone": row["phone"],
                "specialization": row.get("specialization", ""),
                "license_number": row.get("license_number", ""),
                "schedule_start": row.get("schedule_start", ""),
                "schedule_end": row.get("schedule_end", ""),
                "tenant_id": current_user.get('tenant_id', 1)
            }
            if row.get("consultation_fee"):
                doctor_data["consultation_fee"] = float(row["consultation_fee"])
            
            doctor_service.create(doctor_data)
            imported_count += 1
        except Exception:
            continue
    
    return BaseResponse(
        success=True,
        message=f"Imported {imported_count} doctors successfully"
    )

@router.get("/doctors/{doctor_id}", response_model=BaseResponse)
async def get_doctor(doctor_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.clinic_module.models.entities import Doctor
    
    with db_manager.get_session() as session:
        doctor = session.query(Doctor).filter(
            Doctor.id == doctor_id,
            Doctor.tenant_id == current_user['tenant_id']
        ).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        doctor_data = {
            "id": doctor.id,
            "doctor_id": doctor.employee_id,
            "first_name": doctor.first_name,
            "last_name": doctor.last_name,
            "specialization": doctor.specialization,
            "license_number": doctor.license_number,
            "phone": doctor.phone,
            "email": doctor.email,
            "schedule_start": doctor.schedule_start.strftime("%H:%M") if doctor.schedule_start else None,
            "schedule_end": doctor.schedule_end.strftime("%H:%M") if doctor.schedule_end else None,
            "consultation_fee": float(doctor.consultation_fee) if doctor.consultation_fee else None,
            "is_active": doctor.is_active,
            "created_at": doctor.created_at.isoformat() if doctor.created_at else None
        }
    
    return BaseResponse(
        success=True,
        message="Doctor retrieved successfully",
        data=doctor_data
    )

@router.put("/doctors/{doctor_id}", response_model=BaseResponse)
async def update_doctor(doctor_id: int, doctor_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    doctor_service = DoctorService()
    doctor = doctor_service.update(doctor_id, doctor_data)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return BaseResponse(
        success=True,
        message="Doctor updated successfully",
        data={"id": doctor.id}
    )

@router.delete("/doctors/{doctor_id}", response_model=BaseResponse)
async def delete_doctor(doctor_id: int, current_user: dict = Depends(get_current_user)):
    doctor_service = DoctorService()
    success = doctor_service.delete(doctor_id)
    if not success:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return BaseResponse(
        success=True,
        message="Doctor deleted successfully"
    )
