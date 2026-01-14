from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum

class DepartmentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class OrgUnitType(str, Enum):
    DIVISION = "DIVISION"
    DEPARTMENT = "DEPARTMENT"
    TEAM = "TEAM"

class DepartmentBase(BaseModel):
    department_code: str = Field(..., min_length=1, max_length=50)
    department_name: str = Field(..., min_length=1, max_length=200)
    parent_department_id: Optional[int] = None
    description: Optional[str] = None
    branch_id: Optional[int] = None
    default_cost_center_id: Optional[int] = None
    org_unit_type: OrgUnitType = OrgUnitType.DIVISION
    status: DepartmentStatus = DepartmentStatus.ACTIVE

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
    parent_department_id: Optional[int] = None
    description: Optional[str] = None
    branch_id: Optional[int] = None
    default_cost_center_id: Optional[int] = None
    org_unit_type: Optional[OrgUnitType] = None
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

class DepartmentListResponse(BaseModel):
    id: int
    department_code: str
    department_name: str
    parent_department_id: Optional[int]
    org_unit_type: OrgUnitType
    status: DepartmentStatus
    branch_id: Optional[int]
    default_cost_center_id: Optional[int]

    class Config:
        from_attributes = True

class DepartmentImportRow(BaseModel):
    department_code: str
    department_name: str
    parent_code: Optional[str] = None
    description: Optional[str] = None
    org_unit_type: Optional[str] = "DIVISION"
    status: Optional[str] = "ACTIVE"
