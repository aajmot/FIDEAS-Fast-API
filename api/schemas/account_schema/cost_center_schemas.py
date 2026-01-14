from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

class CostCenterCategory(str, Enum):
    PRODUCTION = "PRODUCTION"
    MARKETING = "MARKETING"
    ADMIN = "ADMIN"
    NA = "NA"

class CostCenterBase(BaseModel):
    code: str = Field(..., max_length=20, description="Cost center code")
    name: str = Field(..., max_length=100, description="Cost center name")
    description: Optional[str] = Field(None, description="Cost center description")
    parent_id: Optional[int] = Field(None, description="Parent cost center ID")
    category: CostCenterCategory = Field(CostCenterCategory.NA, description="Cost center category")
    manager_id: Optional[int] = Field(None, description="Manager employee ID")
    department_id: Optional[int] = Field(None, description="Department ID")
    valid_from: date = Field(default_factory=date.today, description="Valid from date")
    valid_until: Optional[date] = Field(None, description="Valid until date")
    is_active: bool = Field(True, description="Is cost center active")
    lock_posting: bool = Field(False, description="Lock posting to this cost center")
    currency_code: Optional[str] = Field(None, max_length=3, description="Currency code")

    @validator('valid_until')
    def validate_dates(cls, v, values):
        if v and 'valid_from' in values and v <= values['valid_from']:
            raise ValueError('valid_until must be after valid_from')
        return v

class CostCenterCreate(CostCenterBase):
    legal_entity_id: Optional[int] = Field(None, description="Legal entity ID")

class CostCenterUpdate(BaseModel):
    code: Optional[str] = Field(None, max_length=20)
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    category: Optional[CostCenterCategory] = None
    manager_id: Optional[int] = None
    department_id: Optional[int] = None
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    is_active: Optional[bool] = None
    lock_posting: Optional[bool] = None
    currency_code: Optional[str] = Field(None, max_length=3)
    legal_entity_id: Optional[int] = None

class CostCenterResponse(CostCenterBase):
    id: int
    tenant_id: int
    legal_entity_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]

    class Config:
        from_attributes = True

class CostCenterListResponse(BaseModel):
    id: int
    code: str
    name: str
    category: CostCenterCategory
    parent_id: Optional[int]
    is_active: bool
    lock_posting: bool
    manager_id: Optional[int]
    department_id: Optional[int]

    class Config:
        from_attributes = True

class CostCenterImportRow(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    parent_code: Optional[str] = None
    category: Optional[str] = "NA"
    is_active: Optional[str] = "true"
    lock_posting: Optional[str] = "false"
    currency_code: Optional[str] = None