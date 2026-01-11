from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
import io
import csv
from datetime import datetime

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.schemas.health_schema.medical_record_schemas import MedicalRecordCreate, MedicalRecordUpdate
from sqlalchemy import or_
import math
from api.middleware.auth_middleware import get_current_user
from modules.health_module.services.patient_service import PatientService
from modules.health_module.services.doctor_service import DoctorService
from modules.health_module.services.appointment_service import AppointmentService
from modules.health_module.services.medical_record_service import MedicalRecordService
from modules.admin_module.models.agency import Agency

router = APIRouter()

# Medical Records endpoints
@router.get("/medical-records", response_model=PaginatedResponse)
async def get_medical_records(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.health_module.models.clinic_entities import MedicalRecord, Patient, Doctor, Appointment
    
    with db_manager.get_session() as session:
        query = session.query(MedicalRecord).join(Appointment).outerjoin(Patient, Appointment.patient_id == Patient.id).outerjoin(Doctor, Appointment.doctor_id == Doctor.id).filter(
            MedicalRecord.tenant_id == current_user.get('tenant_id', 1)
        ).order_by(MedicalRecord.visit_date.desc(), MedicalRecord.created_at.desc())
        
        if pagination.search:
            query = query.filter(or_(
                MedicalRecord.record_number.ilike(f"%{pagination.search}%"),
                MedicalRecord.chief_complaint.ilike(f"%{pagination.search}%"),
                MedicalRecord.diagnosis.ilike(f"%{pagination.search}%")
            ))
        
        total = query.count()
        records = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        record_data = []
        for record in records:
            try:
                data = {
                    "id": record.id,
                    "record_number": record.record_number,
                    "patient_id": record.appointment.patient_id if record.appointment else None,
                    "patient_name": f"{record.appointment.patient.first_name} {record.appointment.patient.last_name}" if record.appointment and record.appointment.patient else "Unknown Patient",
                    "doctor_id": record.appointment.doctor_id if record.appointment else None,
                    "doctor_name": f"{record.appointment.doctor.first_name} {record.appointment.doctor.last_name}" if record.appointment and record.appointment.doctor else "Unknown Doctor",
                    "appointment_id": record.appointment.appointment_number if record.appointment else None,
                    "visit_date": record.visit_date.isoformat() if record.visit_date else None,
                    "chief_complaint": record.chief_complaint,
                    "diagnosis": record.diagnosis,
                    "treatment_plan": record.treatment_plan,
                    "vital_signs": record.vital_signs,
                    "lab_results": record.lab_results,
                    "notes": record.notes,
                    "created_at": record.created_at.isoformat() if record.created_at else None
                }
                record_data.append(data)
            except Exception:
                continue
    
    return PaginatedResponse(
        success=True,
        message="Medical records retrieved successfully",
        data=record_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/medical-records", response_model=BaseResponse)
async def create_medical_record(record_data: MedicalRecordCreate, current_user: dict = Depends(get_current_user)):
    try:
        medical_record_service = MedicalRecordService()
        record_dict = record_data.model_dump()
        record_dict['tenant_id'] = current_user.get('tenant_id')
        record_dict['created_by'] = current_user.get('username', 'system')
        
        record = medical_record_service.create(record_dict)
        return BaseResponse(
            success=True,
            message="Medical record created successfully",
            data={"id": record.id, "record_number": record.record_number}
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating medical record: {str(e)}")

@router.get("/medical-records/export-template")
async def export_medical_records_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Patient Name", "Patient Phone", "Doctor Name", "Doctor Phone", "Visit Date", "Chief Complaint", "Diagnosis", "Treatment Plan", "BP", "Temperature", "Pulse", "Weight", "Lab Results", "Notes"])
    writer.writerow(["John Doe", "123-456-7890", "Dr. Jane Smith", "987-654-3210", "2024-01-15", "Headache", "Migraine", "Rest and medication", "120/80", "98.6°F", "72 bpm", "70 kg", "Normal", "Patient follow-up"])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=medical_records_import_template.csv"}
    )

@router.post("/medical-records/import", response_model=BaseResponse)
async def import_medical_records(request_data: Dict[str, str], current_user: dict = Depends(get_current_user)):
    try:
        csv_content = request_data.get('csv_content', '')
        if not csv_content:
            raise HTTPException(status_code=400, detail="CSV content is required")
        
        medical_record_service = MedicalRecordService()
        result = medical_record_service.import_medical_records(csv_content, current_user.get('tenant_id'))
        
        return BaseResponse(
            success=True,
            message=f"Imported {result['imported']} medical records successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing medical records: {str(e)}")

@router.get("/medical-records/{record_id}", response_model=BaseResponse)
async def get_medical_record(record_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.health_module.models.clinic_entities import MedicalRecord, Patient, Doctor
    
    with db_manager.get_session() as session:
        record = session.query(MedicalRecord).outerjoin(Patient).outerjoin(Doctor).filter(
            MedicalRecord.id == record_id,
            MedicalRecord.tenant_id == current_user['tenant_id']
        ).first()
        if not record:
            raise HTTPException(status_code=404, detail="Medical record not found")
        
        record_data = {
            "id": record.id,
            "record_number": record.record_number,
            "patient_id": record.patient_id,
            "patient_name": f"{record.patient.first_name} {record.patient.last_name}" if hasattr(record, 'patient') and record.patient else f"Patient {record.patient_id}",
            "doctor_id": record.doctor_id,
            "doctor_name": f"{record.doctor.first_name} {record.doctor.last_name}" if hasattr(record, 'doctor') and record.doctor else f"Doctor {record.doctor_id}",
            "appointment_id": record.appointment_id,
            "visit_date": record.visit_date.isoformat() if record.visit_date else None,
            "chief_complaint": record.chief_complaint,
            "diagnosis": record.diagnosis,
            "treatment_plan": record.treatment_plan,
            "vital_signs": record.vital_signs,
            "lab_results": record.lab_results,
            "notes": record.notes,
            "created_at": record.created_at.isoformat() if record.created_at else None
        }
    
    return BaseResponse(
        success=True,
        message="Medical record retrieved successfully",
        data=record_data
    )

@router.get("/medical-records/appointment/{appointment_id}", response_model=BaseResponse)
async def get_medical_record_by_appointment(appointment_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.health_module.models.clinic_entities import MedicalRecord, Patient, Doctor, Appointment
    
    with db_manager.get_session() as session:
        record = session.query(MedicalRecord).join(Appointment).outerjoin(Patient, Appointment.patient_id == Patient.id).outerjoin(Doctor, Appointment.doctor_id == Doctor.id).filter(
            MedicalRecord.appointment_id == appointment_id,
            MedicalRecord.tenant_id == current_user.get('tenant_id', 1)
        ).first()
        
        if not record:
            raise HTTPException(status_code=404, detail="Medical record not found for this appointment")
        
        record_data = {
            "id": record.id,
            "record_number": record.record_number,
            "appointment_id": record.appointment_id,
            "patient_id": record.appointment.patient_id if record.appointment else None,
            "patient_name": f"{record.appointment.patient.first_name} {record.appointment.patient.last_name}" if record.appointment and record.appointment.patient else "Unknown Patient",
            "doctor_id": record.appointment.doctor_id if record.appointment else None,
            "doctor_name": f"{record.appointment.doctor.first_name} {record.appointment.doctor.last_name}" if record.appointment and record.appointment.doctor else "Unknown Doctor",
            "visit_date": record.visit_date.isoformat() if record.visit_date else None,
            "chief_complaint": record.chief_complaint,
            "diagnosis": record.diagnosis,
            "treatment_plan": record.treatment_plan,
            "vital_signs": record.vital_signs,
            "lab_results": record.lab_results,
            "notes": record.notes,
            "created_at": record.created_at.isoformat() if record.created_at else None
        }
    
    return BaseResponse(
        success=True,
        message="Medical record retrieved successfully",
        data=record_data
    )

@router.put("/medical-records/{record_id}", response_model=BaseResponse)
async def update_medical_record(record_id: int, record_data: MedicalRecordUpdate, current_user: dict = Depends(get_current_user)):
    try:
        medical_record_service = MedicalRecordService()
        record_dict = record_data.model_dump(exclude_unset=True)
        record_dict['updated_by'] = current_user.get('username', 'system')
        
        record = medical_record_service.update(record_id, record_dict)
        if not record:
            raise HTTPException(status_code=404, detail="Medical record not found")
        return BaseResponse(
            success=True,
            message="Medical record updated successfully",
            data={"id": record.id, "record_number": record.record_number}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating medical record: {str(e)}")

@router.delete("/medical-records/{record_id}", response_model=BaseResponse)
async def delete_medical_record(record_id: int, current_user: dict = Depends(get_current_user)):
    try:
        medical_record_service = MedicalRecordService()
        success = medical_record_service.delete(record_id)
        if not success:
            raise HTTPException(status_code=404, detail="Medical record not found")
        return BaseResponse(
            success=True,
            message="Medical record deleted successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting medical record: {str(e)}")
