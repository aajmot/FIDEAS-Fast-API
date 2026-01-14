from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum
from decimal import Decimal

class EmployeeType(str, Enum):
    LAB_TECHNICIAN = "LAB_TECHNICIAN"
    DOCTOR = "DOCTOR"
    NURSE = "NURSE"
    ADMIN = "ADMIN"
    OTHERS = "OTHERS"

class EmploymentType(str, Enum):
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"
    CONTRACT = "CONTRACT"

class EmployeeStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"

class AllocationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class UserCreateData(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: str
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    role_ids: List[int] = Field(default_factory=list)

class EmployeeBase(BaseModel):
    employee_code: str = Field(..., max_length=50)
    employee_name: str = Field(..., max_length=200)
    employee_type: EmployeeType = EmployeeType.OTHERS
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = None
    qualification: Optional[str] = Field(None, max_length=100)
    specialization: Optional[str] = Field(None, max_length=100)
    license_number: Optional[str] = Field(None, max_length=50)
    license_expiry: Optional[date] = None
    employment_type: EmploymentType = EmploymentType.INTERNAL
    status: EmployeeStatus = EmployeeStatus.ACTIVE
    remarks: Optional[str] = None
    branch_id: Optional[int] = None
    department_id: Optional[int] = None

class EmployeeCreate(EmployeeBase):
    create_user: bool = Field(True, description="Create user account for employee")
    user_data: UserCreateData

class EmployeeUpdate(BaseModel):
    employee_name: Optional[str] = Field(None, max_length=200)
    employee_type: Optional[EmployeeType] = None
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = None
    qualification: Optional[str] = Field(None, max_length=100)
    specialization: Optional[str] = Field(None, max_length=100)
    license_number: Optional[str] = Field(None, max_length=50)
    license_expiry: Optional[date] = None
    employment_type: Optional[EmploymentType] = None
    status: Optional[EmployeeStatus] = None
    remarks: Optional[str] = None
    branch_id: Optional[int] = None
    department_id: Optional[int] = None

class EmployeeResponse(EmployeeBase):
    id: int
    tenant_id: int
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    is_active: bool
    is_deleted: bool

    class Config:
        from_attributes = True

class EmployeeListResponse(BaseModel):
    id: int
    employee_code: str
    employee_name: str
    employee_type: EmployeeType
    employment_type: EmploymentType
    status: EmployeeStatus
    phone: Optional[str]
    email: Optional[str]
    department_id: Optional[int]
    branch_id: Optional[int]

    class Config:
        from_attributes = True

class CostAllocationBase(BaseModel):
    employee_id: int
    cost_center_id: int
    percentage: Decimal = Field(..., ge=0, le=100)
    effective_start_date: date
    effective_end_date: Optional[date] = None
    status: AllocationStatus = AllocationStatus.ACTIVE

    @validator('effective_end_date')
    def validate_dates(cls, v, values):
        if v and 'effective_start_date' in values and v <= values['effective_start_date']:
            raise ValueError('effective_end_date must be after effective_start_date')
        return v

class CostAllocationCreate(CostAllocationBase):
    branch_id: Optional[int] = None

class CostAllocationUpdate(BaseModel):
    cost_center_id: Optional[int] = None
    percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    effective_start_date: Optional[date] = None
    effective_end_date: Optional[date] = None
    status: Optional[AllocationStatus] = None

class CostAllocationResponse(CostAllocationBase):
    id: int
    tenant_id: int
    branch_id: Optional[int]
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str

    class Config:
        from_attributes = True

class EmployeeImportRow(BaseModel):
    employee_code: str
    employee_name: str
    employee_type: Optional[str] = "OTHERS"
    phone: Optional[str] = None
    email: Optional[str] = None
    qualification: Optional[str] = None
    specialization: Optional[str] = None
    employment_type: Optional[str] = "INTERNAL"
    status: Optional[str] = "ACTIVE"