from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class PaymentTermRequest(BaseModel):
    """Schema for creating/updating payment term"""
    code: str = Field(..., max_length=20, description="Unique code for payment term")
    name: str = Field(..., max_length=100, description="Payment term name")
    days: int = Field(..., ge=0, description="Credit period in days")
    description: Optional[str] = Field(None, description="Additional description")
    is_default: bool = Field(False, description="Is this the default payment term")
    is_active: bool = Field(True, description="Active status")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "code": "NET30",
                "name": "Net 30 Days",
                "days": 30,
                "description": "Payment due in 30 days",
                "is_default": False,
                "is_active": True
            }
        }
    
    @validator('code')
    def validate_code(cls, v):
        """Ensure code is not empty after trimming"""
        if not v or not v.strip():
            raise ValueError('Code cannot be empty')
        return v.strip().upper()
    
    @validator('name')
    def validate_name(cls, v):
        """Ensure name is not empty after trimming"""
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()


class PaymentTermResponse(BaseModel):
    """Schema for payment term response"""
    id: int
    code: str
    name: str
    days: int
    description: Optional[str] = None
    is_default: bool
    is_active: bool
    is_deleted: bool
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    
    class Config:
        from_attributes = True


class PaymentTermListResponse(BaseModel):
    """Schema for paginated list of payment terms"""
    total: int
    page: int
    per_page: int
    total_pages: int
    data: list[PaymentTermResponse]
    
    class Config:
        from_attributes = True
