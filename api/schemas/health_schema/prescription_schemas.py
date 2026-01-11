from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PrescriptionItemCreate(BaseModel):
    product_id: int
    product_name: Optional[str] = Field(None, max_length=200)
    dosage: Optional[str] = Field(None, max_length=100)
    frequency: Optional[str] = Field(None, max_length=100)
    duration: Optional[str] = Field(None, max_length=100)
    quantity: Optional[float] = None
    instructions: Optional[str] = None

class PrescriptionTestItemCreate(BaseModel):
    test_id: int
    test_name: Optional[str] = Field(None, max_length=200)
    instructions: Optional[str] = None

class PrescriptionCreate(BaseModel):
    prescription_number: str = Field(..., max_length=50)
    appointment_id: int
    branch_id: Optional[int] = None
    patient_id: int
    patient_name: Optional[str] = Field(None, max_length=100)
    patient_phone: Optional[str] = Field(None, max_length=20)
    doctor_id: int
    doctor_name: Optional[str] = Field(None, max_length=100)
    doctor_license_number: Optional[str] = Field(None, max_length=50)
    prescription_date: Optional[datetime] = None
    instructions: Optional[str] = None
    notes: Optional[str] = None
    items: List[PrescriptionItemCreate] = []
    test_items: List[PrescriptionTestItemCreate] = []

class PrescriptionItemUpdate(BaseModel):
    product_id: Optional[int] = None
    product_name: Optional[str] = Field(None, max_length=200)
    dosage: Optional[str] = Field(None, max_length=100)
    frequency: Optional[str] = Field(None, max_length=100)
    duration: Optional[str] = Field(None, max_length=100)
    quantity: Optional[float] = None
    instructions: Optional[str] = None

class PrescriptionTestItemUpdate(BaseModel):
    test_id: Optional[int] = None
    test_name: Optional[str] = Field(None, max_length=200)
    instructions: Optional[str] = None

class PrescriptionUpdate(BaseModel):
    branch_id: Optional[int] = None
    prescription_date: Optional[datetime] = None
    instructions: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[PrescriptionItemUpdate]] = None
    test_items: Optional[List[PrescriptionTestItemUpdate]] = None

class PrescriptionItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str]
    dosage: Optional[str]
    frequency: Optional[str]
    duration: Optional[str]
    quantity: Optional[float]
    instructions: Optional[str]
    
    class Config:
        from_attributes = True

class PrescriptionTestItemResponse(BaseModel):
    id: int
    test_id: int
    test_name: Optional[str]
    instructions: Optional[str]
    
    class Config:
        from_attributes = True

class PrescriptionResponse(BaseModel):
    id: int
    prescription_number: str
    tenant_id: int
    branch_id: Optional[int]
    appointment_id: int
    patient_id: int
    patient_name: Optional[str]
    patient_phone: Optional[str]
    doctor_id: int
    doctor_name: Optional[str]
    doctor_license_number: Optional[str]
    prescription_date: datetime
    instructions: Optional[str]
    notes: Optional[str]
    items: List[PrescriptionItemResponse] = []
    test_items: List[PrescriptionTestItemResponse] = []
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime]
    updated_by: Optional[str]
    is_active: bool
    is_deleted: bool
    
    class Config:
        from_attributes = True
