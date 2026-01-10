from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, time, datetime
from enum import Enum

class AppointmentStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"

class AppointmentCreate(BaseModel):
    appointment_number: Optional[str] = None
    appointment_date: date
    appointment_time: time
    duration_minutes: Optional[int] = 30
    
    patient_id: int
    patient_name: Optional[str] = None
    patient_phone: Optional[str] = None
    
    doctor_id: int
    doctor_name: Optional[str] = None
    doctor_phone: Optional[str] = None
    doctor_license_number: Optional[str] = None
    doctor_specialization: Optional[str] = None
    
    agency_id: Optional[int] = None
    agency_name: Optional[str] = None
    agency_phone: Optional[str] = None
    
    branch_id: Optional[int] = None
    status: Optional[AppointmentStatus] = AppointmentStatus.SCHEDULED
    reason: Optional[str] = None
    notes: Optional[str] = None

class AppointmentUpdate(BaseModel):
    appointment_date: Optional[date] = None
    appointment_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    
    patient_id: Optional[int] = None
    patient_name: Optional[str] = None
    patient_phone: Optional[str] = None
    
    doctor_id: Optional[int] = None
    doctor_name: Optional[str] = None
    doctor_phone: Optional[str] = None
    doctor_license_number: Optional[str] = None
    doctor_specialization: Optional[str] = None
    
    agency_id: Optional[int] = None
    agency_name: Optional[str] = None
    agency_phone: Optional[str] = None
    
    branch_id: Optional[int] = None
    status: Optional[AppointmentStatus] = None
    reason: Optional[str] = None
    notes: Optional[str] = None

class AppointmentResponse(BaseModel):
    id: int
    appointment_number: str
    appointment_date: date
    appointment_time: time
    duration_minutes: Optional[int]
    
    patient_id: int
    patient_name: Optional[str]
    patient_phone: Optional[str]
    
    doctor_id: int
    doctor_name: Optional[str]
    doctor_phone: Optional[str]
    doctor_license_number: Optional[str]
    doctor_specialization: Optional[str]
    
    agency_id: Optional[int]
    agency_name: Optional[str]
    agency_phone: Optional[str]
    
    branch_id: Optional[int]
    tenant_id: int
    status: str
    reason: Optional[str]
    notes: Optional[str]
    
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime]
    updated_by: Optional[str]
    is_active: bool
    is_deleted: bool
    
    class Config:
        from_attributes = True
