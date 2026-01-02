# api/schemas/admin_schema/branch_schemas.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class BranchType(str, Enum):
    HEAD_OFFICE = "HEAD_OFFICE"
    BRANCH = "BRANCH"
    WAREHOUSE = "WAREHOUSE"
    LAB = "LAB"
    CLINIC = "CLINIC"

class BranchStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    CLOSED = "CLOSED"

class BranchBase(BaseModel):
    branch_code: str = Field(..., min_length=1, max_length=50)
    branch_name: str = Field(..., min_length=1, max_length=200)
    branch_type: Optional[BranchType] = BranchType.BRANCH
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = None
    contact_person: Optional[str] = Field(None, max_length=100)
    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field('India', max_length=100)
    gstin: Optional[str] = Field(None, max_length=20)
    pan: Optional[str] = Field(None, max_length=20)
    tan: Optional[str] = Field(None, max_length=20)
    bank_account_id: Optional[int] = None
    cost_center_id: Optional[int] = None
    profit_center_id: Optional[int] = None
    manager_id: Optional[int] = None
    manager_name: Optional[str] = Field(None, max_length=100)
    is_default: Optional[bool] = False
    status: Optional[BranchStatus] = BranchStatus.ACTIVE
    remarks: Optional[str] = None
    tags: Optional[List[str]] = None

    @field_validator('branch_code', 'branch_name')
    @classmethod
    def validate_not_empty(cls, v):
        if v and not v.strip():
            raise ValueError('Field cannot be empty or whitespace')
        return v.strip() if v else v

class BranchCreate(BranchBase):
    pass

class BranchUpdate(BaseModel):
    branch_name: Optional[str] = Field(None, min_length=1, max_length=200)
    branch_type: Optional[BranchType] = None
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = None
    contact_person: Optional[str] = Field(None, max_length=100)
    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    gstin: Optional[str] = Field(None, max_length=20)
    pan: Optional[str] = Field(None, max_length=20)
    tan: Optional[str] = Field(None, max_length=20)
    bank_account_id: Optional[int] = None
    cost_center_id: Optional[int] = None
    profit_center_id: Optional[int] = None
    manager_id: Optional[int] = None
    manager_name: Optional[str] = Field(None, max_length=100)
    is_default: Optional[bool] = None
    status: Optional[BranchStatus] = None
    remarks: Optional[str] = None
    tags: Optional[List[str]] = None

class BranchResponse(BranchBase):
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
