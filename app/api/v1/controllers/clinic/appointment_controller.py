from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.core.auth.oauth2_scheme import get_current_user
from app.core.utils.api_response import APIResponse
from app.modules.clinic.services.appointment_service import AppointmentService

router = APIRouter()

@router.get("/appointments")
async def get_appointments(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    appointment_service = AppointmentService(db)
    appointments = appointment_service.get_all()
    
    appointment_data = [{
        "id": appointment.id,
        "appointment_number": appointment.appointment_number,
        "patient_id": appointment.patient_id,
        "doctor_id": appointment.doctor_id,
        "appointment_date": appointment.appointment_date.isoformat() if appointment.appointment_date else None,
        "appointment_time": appointment.appointment_time.isoformat() if appointment.appointment_time else None,
        "status": appointment.status,
        "reason": appointment.reason,
        "is_active": appointment.is_active
    } for appointment in appointments]
    
    return APIResponse.success(appointment_data)

@router.post("/appointments")
async def create_appointment(
    appointment_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    appointment_service = AppointmentService(db)
    appointment = appointment_service.create(appointment_data)
    return APIResponse.created({"id": appointment.id})