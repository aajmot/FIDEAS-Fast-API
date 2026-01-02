from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date, datetime
from enum import Enum

class EmploymentType(str, Enum):
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"
    CONTRACT = "CONTRACT"

class TechnicianStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"

class LabTechnicianCreate(BaseModel):
    technician_name: str = Field(..., min_length=1, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = None
    qualification: Optional[str] = Field(None, max_length=100)
    specialization: Optional[str] = Field(None, max_length=100)
    license_number: Optional[str] = Field(None, max_length=50)
    license_expiry: Optional[date] = None
    employment_type: EmploymentType = EmploymentType.INTERNAL
    status: TechnicianStatus = TechnicianStatus.ACTIVE
    remarks: Optional[str] = None

    @field_validator('license_expiry')
    @classmethod
    def validate_license_expiry(cls, v):
        if v and v < date.today():
            raise ValueError('License expiry date cannot be in the past')
        return v

class LabTechnicianUpdate(BaseModel):
    technician_name: Optional[str] = Field(None, min_length=1, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = None
    qualification: Optional[str] = Field(None, max_length=100)
    specialization: Optional[str] = Field(None, max_length=100)
    license_number: Optional[str] = Field(None, max_length=50)
    license_expiry: Optional[date] = None
    employment_type: Optional[EmploymentType] = None
    status: Optional[TechnicianStatus] = None
    remarks: Optional[str] = None

    @field_validator('license_expiry')
    @classmethod
    def validate_license_expiry(cls, v):
        if v and v < date.today():
            raise ValueError('License expiry date cannot be in the past')
        return v

class LabTechnicianResponse(BaseModel):
    id: int
    technician_code: str
    technician_name: str
    phone: Optional[str]
    email: Optional[str]
    qualification: Optional[str]
    specialization: Optional[str]
    license_number: Optional[str]
    license_expiry: Optional[date]
    employment_type: str
    status: str
    remarks: Optional[str]
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True
