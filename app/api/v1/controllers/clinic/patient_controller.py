from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.core.auth.oauth2_scheme import get_current_user
from app.core.utils.api_response import APIResponse
from app.modules.clinic.services.patient_service import PatientService

router = APIRouter()

@router.get("/patients")
async def get_patients(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    patient_service = PatientService(db)
    patients = patient_service.get_all()
    
    patient_data = [{
        "id": patient.id,
        "patient_number": patient.patient_number,
        "first_name": patient.first_name,
        "last_name": patient.last_name,
        "phone": patient.phone,
        "email": patient.email,
        "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
        "gender": patient.gender,
        "blood_group": patient.blood_group,
        "is_active": patient.is_active
    } for patient in patients]
    
    return APIResponse.success(patient_data)

@router.post("/patients")
async def create_patient(
    patient_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    patient_service = PatientService(db)
    patient = patient_service.create(patient_data)
    return APIResponse.created({"id": patient.id})

@router.get("/patients/{patient_id}")
async def get_patient(
    patient_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    patient_service = PatientService(db)
    patient = patient_service.get_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return APIResponse.success({
        "id": patient.id,
        "patient_number": patient.patient_number,
        "first_name": patient.first_name,
        "last_name": patient.last_name,
        "phone": patient.phone,
        "email": patient.email,
        "is_active": patient.is_active
    })