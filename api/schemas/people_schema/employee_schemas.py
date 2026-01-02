from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, date
from enum import Enum

class EmployeeType(str, Enum):
    LAB_TECHNICIAN = "LAB_TECHNICIAN"
    DOCTOR = "DOCTOR"
    NURSE = "NURSE"
    ADMIN = "ADMIN"
    OTHER = "OTHER"

class EmploymentType(str, Enum):
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"
    CONTRACT = "CONTRACT"

class EmployeeStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"

class EmployeeBase(BaseModel):
    employee_code: str = Field(..., min_length=1, max_length=50)
    employee_name: str = Field(..., min_length=1, max_length=200)
    employee_type: EmployeeType
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    qualification: Optional[str] = Field(None, max_length=100)
    specialization: Optional[str] = Field(None, max_length=100)
    license_number: Optional[str] = Field(None, max_length=50)
    license_expiry: Optional[date] = None
    branch_id: Optional[int] = None
    department_id: Optional[int] = None
    employment_type: Optional[EmploymentType] = EmploymentType.INTERNAL
    status: Optional[EmployeeStatus] = EmployeeStatus.ACTIVE
    remarks: Optional[str] = None

    @field_validator('employee_code', 'employee_name')
    @classmethod
    def validate_not_empty(cls, v):
        if v and not v.strip():
            raise ValueError('Field cannot be empty or whitespace')
        return v.strip() if v else v

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    employee_name: Optional[str] = Field(None, min_length=1, max_length=200)
    employee_type: Optional[EmployeeType] = None
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    qualification: Optional[str] = Field(None, max_length=100)
    specialization: Optional[str] = Field(None, max_length=100)
    license_number: Optional[str] = Field(None, max_length=50)
    license_expiry: Optional[date] = None
    branch_id: Optional[int] = None
    department_id: Optional[int] = None
    employment_type: Optional[EmploymentType] = None
    status: Optional[EmployeeStatus] = None
    remarks: Optional[str] = None

class EmployeeResponse(EmployeeBase):
    id: int
    tenant_id: int
    is_active: bool
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    is_deleted: bool

    class Config:
        from_attributes = True
