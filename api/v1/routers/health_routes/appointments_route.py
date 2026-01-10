from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
import io
import csv
from datetime import datetime
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.schemas.health_schema.appointment_schemas import AppointmentCreate, AppointmentUpdate, AppointmentResponse
from api.middleware.auth_middleware import get_current_user
from modules.health_module.services.appointment_service import AppointmentService

router = APIRouter()

@router.get("/appointments", response_model=PaginatedResponse)
async def get_appointments(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    try:
        appointment_service = AppointmentService()
        result = appointment_service.get_all(
            tenant_id=current_user.get('tenant_id'),
            search=pagination.search,
            offset=pagination.offset,
            limit=pagination.per_page
        )
        
        appointment_data = [{
            "id": apt.id,
            "appointment_number": apt.appointment_number,
            "appointment_date": apt.appointment_date.isoformat(),
            "appointment_time": apt.appointment_time.strftime("%H:%M"),
            "duration_minutes": apt.duration_minutes,
            "patient_id": apt.patient_id,
            "patient_name": apt.patient_name,
            "patient_phone": apt.patient_phone,
            "doctor_id": apt.doctor_id,
            "doctor_name": apt.doctor_name,
            "doctor_phone": apt.doctor_phone,
            "doctor_license_number": apt.doctor_license_number,
            "doctor_specialization": apt.doctor_specialization,
            "agency_id": apt.agency_id,
            "agency_name": apt.agency_name,
            "agency_phone": apt.agency_phone,
            "branch_id": apt.branch_id,
            "status": apt.status,
            "reason": apt.reason,
            "notes": apt.notes,
            "created_at": apt.created_at.isoformat() if apt.created_at else None
        } for apt in result['appointments']]
        
        return PaginatedResponse(
            success=True,
            message="Appointments retrieved successfully",
            data=appointment_data,
            total=result['total'],
            page=pagination.page,
            per_page=pagination.per_page,
            total_pages=math.ceil(result['total'] / pagination.per_page)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/appointments", response_model=BaseResponse)
async def create_appointment(appointment_data: AppointmentCreate, current_user: dict = Depends(get_current_user)):
    try:
        appointment_service = AppointmentService()
        data_dict = appointment_data.model_dump(exclude_unset=True)
        data_dict['tenant_id'] = current_user.get('tenant_id')
        data_dict['created_by'] = current_user.get('username', 'system')
        
        appointment = appointment_service.create(data_dict)
        return BaseResponse(
            success=True,
            message="Appointment created successfully",
            data={"id": appointment.id, "appointment_number": appointment.appointment_number}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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
    try:
        appointment_service = AppointmentService()
        
        if appointment_identifier.isdigit():
            appointment = appointment_service.get_by_id(appointment_id=int(appointment_identifier))
        else:
            appointment = appointment_service.get_by_id(appointment_number=appointment_identifier)
        
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        appointment_data = {
            "id": appointment.id,
            "appointment_number": appointment.appointment_number,
            "appointment_date": appointment.appointment_date.isoformat(),
            "appointment_time": appointment.appointment_time.strftime("%H:%M"),
            "duration_minutes": appointment.duration_minutes,
            "patient_id": appointment.patient_id,
            "patient_name": appointment.patient_name,
            "patient_phone": appointment.patient_phone,
            "doctor_id": appointment.doctor_id,
            "doctor_name": appointment.doctor_name,
            "doctor_phone": appointment.doctor_phone,
            "doctor_license_number": appointment.doctor_license_number,
            "doctor_specialization": appointment.doctor_specialization,
            "agency_id": appointment.agency_id,
            "agency_name": appointment.agency_name,
            "agency_phone": appointment.agency_phone,
            "branch_id": appointment.branch_id,
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/appointments/{appointment_id}", response_model=BaseResponse)
async def update_appointment(appointment_id: int, appointment_data: AppointmentUpdate, current_user: dict = Depends(get_current_user)):
    try:
        appointment_service = AppointmentService()
        update_dict = appointment_data.model_dump(exclude_unset=True)
        
        appointment = appointment_service.update(
            appointment_id=appointment_id,
            update_data=update_dict,
            updated_by=current_user.get('username', 'system')
        )
        
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return BaseResponse(
            success=True,
            message="Appointment updated successfully",
            data={"id": appointment.id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/appointments/{appointment_id}", response_model=BaseResponse)
async def delete_appointment(appointment_id: int, current_user: dict = Depends(get_current_user)):
    try:
        appointment_service = AppointmentService()
        success = appointment_service.delete(
            appointment_id=appointment_id,
            deleted_by=current_user.get('username', 'system')
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return BaseResponse(
            success=True,
            message="Appointment deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
