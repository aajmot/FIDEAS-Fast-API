from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum

class DepartmentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class DepartmentBase(BaseModel):
    department_code: str = Field(..., min_length=1, max_length=50)
    department_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    branch_id: Optional[int] = None
    status: Optional[DepartmentStatus] = DepartmentStatus.ACTIVE

    @field_validator('department_code', 'department_name')
    @classmethod
    def validate_not_empty(cls, v):
        if v and not v.strip():
            raise ValueError('Field cannot be empty or whitespace')
        return v.strip() if v else v

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    department_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    branch_id: Optional[int] = None
    status: Optional[DepartmentStatus] = None

class DepartmentResponse(DepartmentBase):
    id: int
    tenant_id: int
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    is_deleted: bool

    class Config:
        from_attributes = True
