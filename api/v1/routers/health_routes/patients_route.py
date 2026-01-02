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

# Patient endpoints
@router.get("/patients", response_model=PaginatedResponse)
async def get_patients(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.health_module.models.clinic_entities import Patient
    
    with db_manager.get_session() as session:
        query = session.query(Patient).filter(
            Patient.is_active == True,
            Patient.tenant_id == current_user.get('tenant_id')
        )
        
        if pagination.search:
            search_term = f"%{pagination.search}%"
            query = query.filter(or_(
                Patient.patient_number.ilike(search_term),
                Patient.first_name.ilike(search_term),
                Patient.last_name.ilike(search_term),
                Patient.email.ilike(search_term),
                Patient.phone.ilike(search_term)
            ))
        
        total = query.count()
        patients = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        patient_data = [{
            "id": patient.id,
            "patient_number": patient.patient_number,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "email": patient.email,
            "phone": patient.phone,
            "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            "gender": patient.gender,
            "address": patient.address,
            "emergency_contact": patient.emergency_contact,
            "emergency_phone": patient.emergency_phone,
            "blood_group": patient.blood_group,
            "is_active": patient.is_active,
            "created_at": patient.created_at.isoformat() if patient.created_at else None
        } for patient in patients]
    
    return PaginatedResponse(
        success=True,
        message="Patients retrieved successfully",
        data=patient_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/patients", response_model=BaseResponse)
async def create_patient(patient_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    patient_service = PatientService()
    # Always use tenant_id from logged-in user, never from request
    patient_data['tenant_id'] = current_user.get('tenant_id')
    patient_data['created_by'] = current_user.get('username')
    patient = patient_service.create(patient_data)
    return BaseResponse(
        success=True,
        message="Patient created successfully",
        data={"id": patient.id}
    )

# Export/Import endpoints
@router.get("/patients/export-template")
async def export_patients_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["first_name", "last_name", "email", "phone", "date_of_birth", "gender", "address", "emergency_contact", "emergency_phone", "blood_group", "allergies", "medical_history"])
    writer.writerow(["John", "Doe", "john@example.com", "123-456-7890", "1990-01-01", "Male", "123 Main St", "Jane Doe", "987-654-3210", "O+", "None", "No significant history"])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=patients_template.csv"}
    )

@router.post("/patients/import", response_model=BaseResponse)
async def import_patients(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    patient_service = PatientService()
    imported_count = 0
    
    for row in csv_data:
        try:
            patient_data = {
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "email": row.get("email", ""),
                "phone": row["phone"],
                "gender": row.get("gender", ""),
                "address": row.get("address", ""),
                "emergency_contact": row.get("emergency_contact", ""),
                "emergency_phone": row.get("emergency_phone", ""),
                "blood_group": row.get("blood_group", ""),
                "allergies": row.get("allergies", ""),
                "medical_history": row.get("medical_history", ""),
                "tenant_id": current_user.get('tenant_id', 1)
            }
            if row.get("date_of_birth"):
                patient_data["date_of_birth"] = datetime.strptime(row["date_of_birth"], "%Y-%m-%d").date()
            
            patient_service.create(patient_data)
            imported_count += 1
        except Exception:
            continue
    
    return BaseResponse(
        success=True,
        message=f"Imported {imported_count} patients successfully"
    )

@router.get("/patients/{patient_id}", response_model=BaseResponse)
async def get_patient(patient_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.health_module.models.clinic_entities import Patient
    
    with db_manager.get_session() as session:
        patient = session.query(Patient).filter(
            Patient.id == patient_id,
            Patient.tenant_id == current_user['tenant_id']
        ).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        patient_data = {
            "id": patient.id,
            "patient_number": patient.patient_number,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "email": patient.email,
            "phone": patient.phone,
            "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            "gender": patient.gender,
            "address": patient.address,
            "emergency_contact": patient.emergency_contact,
            "emergency_phone": patient.emergency_phone,
            "blood_group": patient.blood_group,
            "allergies": patient.allergies,
            "medical_history": patient.medical_history,
            "is_active": patient.is_active,
            "created_at": patient.created_at.isoformat() if patient.created_at else None
        }
    
    return BaseResponse(
        success=True,
        message="Patient retrieved successfully",
        data=patient_data
    )

@router.put("/patients/{patient_id}", response_model=BaseResponse)
async def update_patient(patient_id: int, patient_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    patient_service = PatientService()
    patient = patient_service.update(patient_id, patient_data)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return BaseResponse(
        success=True,
        message="Patient updated successfully",
        data={"id": patient.id}
    )

@router.delete("/patients/{patient_id}", response_model=BaseResponse)
async def delete_patient(patient_id: int, current_user: dict = Depends(get_current_user)):
    patient_service = PatientService()
    success = patient_service.delete(patient_id)
    if not success:
        raise HTTPException(status_code=404, detail="Patient not found")
    return BaseResponse(
        success=True,
        message="Patient deleted successfully"
    )
