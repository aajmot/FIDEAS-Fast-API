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

# Patient endpoints
@router.get("/patients", response_model=PaginatedResponse)
async def get_patients(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.clinic_module.models.entities import Patient
    
    with db_manager.get_session() as session:
        query = session.query(Patient).filter(
            Patient.is_active == True,
            Patient.tenant_id == current_user.get('tenant_id', 1)
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
    # Add tenant_id from current user if not provided
    if 'tenant_id' not in patient_data:
        patient_data['tenant_id'] = current_user.get('tenant_id', 1)
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
    from modules.clinic_module.models.entities import Patient
    
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
    # Add tenant_id from current user if not provided
    if 'tenant_id' not in doctor_data:
        doctor_data['tenant_id'] = current_user.get('tenant_id', 1)
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

# Agency endpoints for appointments
@router.get("/agencies", response_model=PaginatedResponse)
async def get_agencies(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    
    with db_manager.get_session() as session:
        query = session.query(Agency).filter(Agency.tenant_id == current_user.get('tenant_id', 1))
        
        if pagination.search:
            search_term = f"%{pagination.search}%"
            query = query.filter(Agency.name.ilike(search_term))
        
        total = query.count()
        agencies = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        agency_data = [{
            "id": agency.id,
            "name": agency.name,
            "phone": agency.phone
        } for agency in agencies]
    
    return PaginatedResponse(
        success=True,
        message="Agencies retrieved successfully",
        data=agency_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

# Appointment endpoints
@router.get("/appointments", response_model=PaginatedResponse)
async def get_appointments(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.clinic_module.models.entities import Appointment, Patient, Doctor
    
    with db_manager.get_session() as session:
        query = session.query(Appointment).outerjoin(Patient).outerjoin(Doctor).filter(
            Appointment.tenant_id == current_user.get('tenant_id', 1)
        ).order_by(Appointment.appointment_date.desc(), Appointment.created_at.desc())
        
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
    # Add tenant_id from current user if not provided
    if 'tenant_id' not in appointment_data:
        appointment_data['tenant_id'] = current_user.get('tenant_id', 1)
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
    
    result = appointment_service.import_appointments(csv_content, current_user.get('tenant_id', 1))
    
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

# Medical Records endpoints
@router.get("/medical-records", response_model=PaginatedResponse)
async def get_medical_records(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.clinic_module.models.entities import MedicalRecord, Patient, Doctor, Appointment
    
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
async def create_medical_record(record_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from modules.clinic_module.services.medical_record_service import MedicalRecordService
    
    medical_record_service = MedicalRecordService()
    if 'tenant_id' not in record_data:
        record_data['tenant_id'] = current_user.get('tenant_id', 1)
    record = medical_record_service.create(record_data)
    return BaseResponse(
        success=True,
        message="Medical record created successfully",
        data={"id": record.id}
    )

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
async def import_medical_records(request_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from modules.clinic_module.services.medical_record_service import MedicalRecordService
    
    csv_content = request_data.get('csv_content', '')
    
    if not csv_content:
        raise HTTPException(status_code=400, detail="CSV content is required")
    
    medical_record_service = MedicalRecordService()
    result = medical_record_service.import_medical_records(csv_content, current_user.get('tenant_id', 1))
    
    return BaseResponse(
        success=True,
        message=f"Imported {result['imported']} medical records successfully",
        data=result
    )

@router.get("/medical-records/{record_id}", response_model=BaseResponse)
async def get_medical_record(record_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.clinic_module.models.entities import MedicalRecord, Patient, Doctor
    
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
    from modules.clinic_module.models.entities import MedicalRecord, Patient, Doctor, Appointment
    
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
async def update_medical_record(record_id: int, record_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from modules.clinic_module.services.medical_record_service import MedicalRecordService
    
    medical_record_service = MedicalRecordService()
    record = medical_record_service.update(record_id, record_data)
    if not record:
        raise HTTPException(status_code=404, detail="Medical record not found")
    return BaseResponse(
        success=True,
        message="Medical record updated successfully",
        data={"id": record.id}
    )

@router.delete("/medical-records/{record_id}", response_model=BaseResponse)
async def delete_medical_record(record_id: int, current_user: dict = Depends(get_current_user)):
    from modules.clinic_module.services.medical_record_service import MedicalRecordService
    
    medical_record_service = MedicalRecordService()
    success = medical_record_service.delete(record_id)
    if not success:
        raise HTTPException(status_code=404, detail="Medical record not found")
    return BaseResponse(
        success=True,
        message="Medical record deleted successfully"
    )

# Prescription endpoints
@router.get("/prescriptions", response_model=PaginatedResponse)
async def get_prescriptions(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.clinic_module.models.entities import Prescription, Patient, Doctor, Appointment
    
    with db_manager.get_session() as session:
        query = session.query(Prescription).outerjoin(Patient).outerjoin(Doctor).outerjoin(Appointment).filter(
            Prescription.tenant_id == current_user.get('tenant_id', 1)
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
    from modules.clinic_module.services.prescription_service import PrescriptionService
    from modules.account_module.services.transaction_posting_service import TransactionPostingService
    from core.database.connection import db_manager
    
    prescription_service = PrescriptionService()
    if 'tenant_id' not in prescription_data:
        prescription_data['tenant_id'] = current_user.get('tenant_id', 1)
    
    # Extract items from prescription data
    items_data = prescription_data.pop('items', [])
    test_items_data = prescription_data.pop('test_items', [])
    
    # Add created_by to items
    for item in items_data:
        item['created_by'] = current_user.get('username')
    
    # Add created_by and tenant_id to test items
    for test_item in test_items_data:
        test_item['created_by'] = current_user.get('username')
        test_item['tenant_id'] = current_user.get('tenant_id', 1)
    
    prescription = prescription_service.create(prescription_data, items_data, test_items_data)
    
    return BaseResponse(
        success=True,
        message="Prescription created successfully",
        data={"id": prescription.id}
    )

@router.put("/prescriptions/{prescription_id}", response_model=BaseResponse)
async def update_prescription(prescription_id: int, prescription_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from modules.clinic_module.services.prescription_service import PrescriptionService
    
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
            test_item['tenant_id'] = current_user.get('tenant_id', 1)
    
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
    from modules.clinic_module.services.prescription_service import PrescriptionService
    
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
    from modules.clinic_module.models.entities import Prescription, PrescriptionItem, PrescriptionTestItem, Patient, Doctor
    from modules.inventory_module.models.entities import Product
    from modules.care_module.models.entities import Test
    
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
            from modules.clinic_module.models.entities import Appointment
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

# Billing Master endpoints
@router.get("/billing-masters", response_model=PaginatedResponse)
async def get_billing_masters(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.clinic_module.models.entities import ClinicBillingMaster
    
    with db_manager.get_session() as session:
        query = session.query(ClinicBillingMaster).filter(
            ClinicBillingMaster.is_deleted == False,
            ClinicBillingMaster.tenant_id == current_user.get('tenant_id', 1)
        )
        
        if pagination.search:
            search_term = f"%{pagination.search}%"
            query = query.filter(or_(
                ClinicBillingMaster.description.ilike(search_term),
                ClinicBillingMaster.note.ilike(search_term)
            ))
        
        total = query.count()
        billing_masters = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        billing_master_data = [{
            "id": bm.id,
            "description": bm.description,
            "note": bm.note,
            "amount": float(bm.amount),
            "hsn_code": bm.hsn_code,
            "gst_percentage": float(bm.gst_percentage) if bm.gst_percentage else 0.0,
            "is_active": bm.is_active,
            "created_at": bm.created_at.isoformat() if bm.created_at else None,
            "updated_at": bm.updated_at.isoformat() if bm.updated_at else None
        } for bm in billing_masters]
    
    return PaginatedResponse(
        success=True,
        message="Billing masters retrieved successfully",
        data=billing_master_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/billing-masters", response_model=BaseResponse)
async def create_billing_master(billing_master_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from modules.clinic_module.services.billing_master_service import BillingMasterService
    
    billing_master_service = BillingMasterService()
    if 'tenant_id' not in billing_master_data:
        billing_master_data['tenant_id'] = current_user.get('tenant_id', 1)
    billing_master = billing_master_service.create(billing_master_data)
    return BaseResponse(
        success=True,
        message="Billing master created successfully",
        data={"id": billing_master['id']}
    )

@router.get("/billing-masters/export-template")
async def export_billing_masters_template(current_user: dict = Depends(get_current_user)):
    from modules.clinic_module.services.billing_master_service import BillingMasterService
    
    billing_master_service = BillingMasterService()
    template_content = billing_master_service.export_template()
    
    return StreamingResponse(
        io.BytesIO(template_content.encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=billing_masters_template.csv"}
    )

@router.post("/billing-masters/import", response_model=BaseResponse)
async def import_billing_masters(request_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from modules.clinic_module.services.billing_master_service import BillingMasterService
    
    csv_content = request_data.get('csv_content', '')
    
    if not csv_content:
        raise HTTPException(status_code=400, detail="CSV content is required")
    
    billing_master_service = BillingMasterService()
    result = billing_master_service.import_billing_masters(csv_content, current_user.get('tenant_id', 1))
    
    return BaseResponse(
        success=True,
        message=f"Imported {result['imported']} billing masters successfully",
        data=result
    )

@router.get("/billing-masters/{billing_master_id}", response_model=BaseResponse)
async def get_billing_master(billing_master_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.clinic_module.models.entities import ClinicBillingMaster
    
    with db_manager.get_session() as session:
        billing_master = session.query(ClinicBillingMaster).filter(
            ClinicBillingMaster.id == billing_master_id,
            ClinicBillingMaster.is_deleted == False
        ).first()
        if not billing_master:
            raise HTTPException(status_code=404, detail="Billing master not found")
        
        billing_master_data = {
            "id": billing_master.id,
            "description": billing_master.description,
            "note": billing_master.note,
            "amount": float(billing_master.amount),
            "hsn_code": billing_master.hsn_code,
            "gst_percentage": float(billing_master.gst_percentage) if billing_master.gst_percentage else 0.0,
            "is_active": billing_master.is_active,
            "created_at": billing_master.created_at.isoformat() if billing_master.created_at else None,
            "updated_at": billing_master.updated_at.isoformat() if billing_master.updated_at else None
        }
    
    return BaseResponse(
        success=True,
        message="Billing master retrieved successfully",
        data=billing_master_data
    )

@router.put("/billing-masters/{billing_master_id}", response_model=BaseResponse)
async def update_billing_master(billing_master_id: int, billing_master_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from modules.clinic_module.services.billing_master_service import BillingMasterService
    
    billing_master_service = BillingMasterService()
    billing_master = billing_master_service.update(billing_master_id, billing_master_data)
    if not billing_master:
        raise HTTPException(status_code=404, detail="Billing master not found")
    return BaseResponse(
        success=True,
        message="Billing master updated successfully",
        data={"id": billing_master['id']}
    )

@router.delete("/billing-masters/{billing_master_id}", response_model=BaseResponse)
async def delete_billing_master(billing_master_id: int, current_user: dict = Depends(get_current_user)):
    from modules.clinic_module.services.billing_master_service import BillingMasterService
    
    billing_master_service = BillingMasterService()
    success = billing_master_service.delete(billing_master_id)
    if not success:
        raise HTTPException(status_code=404, detail="Billing master not found")
    return BaseResponse(
        success=True,
        message="Billing master deleted successfully"
    )

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