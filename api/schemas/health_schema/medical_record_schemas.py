from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MedicalRecordCreate(BaseModel):
    appointment_id: int
    branch_id: Optional[int] = None
    patient_id: int
    patient_name: Optional[str] = Field(None, max_length=100)
    doctor_id: int
    doctor_name: Optional[str] = Field(None, max_length=100)
    visit_date: Optional[datetime] = None
    chief_complaint: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    vital_signs: Optional[str] = None
    lab_results: Optional[str] = None
    notes: Optional[str] = None

class MedicalRecordUpdate(BaseModel):
    branch_id: Optional[int] = None
    visit_date: Optional[datetime] = None
    chief_complaint: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    vital_signs: Optional[str] = None
    lab_results: Optional[str] = None
    notes: Optional[str] = None

class MedicalRecordResponse(BaseModel):
    id: int
    record_number: str
    tenant_id: int
    branch_id: Optional[int]
    appointment_id: int
    patient_id: int
    patient_name: Optional[str]
    doctor_id: int
    doctor_name: Optional[str]
    visit_date: datetime
    chief_complaint: Optional[str]
    diagnosis: Optional[str]
    treatment_plan: Optional[str]
    vital_signs: Optional[str]
    lab_results: Optional[str]
    notes: Optional[str]
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime]
    updated_by: Optional[str]
    is_active: bool
    is_deleted: bool
    
    class Config:
        from_attributes = True
