from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class AccountConfigurationKeyRequest(BaseModel):
    """Schema for creating/updating account configuration key"""
    code: str = Field(..., max_length=50, description="Configuration key code (unique)")
    name: str = Field(..., max_length=100, description="Configuration key name")
    description: Optional[str] = Field(None, description="Configuration key description")
    default_account_id: Optional[int] = Field(None, description="Default account ID (global fallback)")
    is_active: bool = Field(True, description="Whether configuration key is active")
    
    @validator('code')
    def validate_code(cls, v):
        """Validate code format (uppercase, alphanumeric + underscore)"""
        if not v:
            raise ValueError("Code cannot be empty")
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Code must contain only alphanumeric characters, underscores, or hyphens")
        return v.upper()
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "code": "CASH",
                "name": "Cash Account",
                "description": "Default cash account for cash transactions",
                "default_account_id": 1,
                "is_active": True
            }
        }


class AccountConfigurationKeyUpdate(BaseModel):
    """Schema for updating account configuration key (partial update)"""
    code: Optional[str] = Field(None, max_length=50, description="Configuration key code")
    name: Optional[str] = Field(None, max_length=100, description="Configuration key name")
    description: Optional[str] = Field(None, description="Configuration key description")
    default_account_id: Optional[int] = Field(None, description="Default account ID")
    is_active: Optional[bool] = Field(None, description="Whether configuration key is active")
    
    @validator('code')
    def validate_code(cls, v):
        """Validate code format if provided"""
        if v and not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Code must contain only alphanumeric characters, underscores, or hyphens")
        return v.upper() if v else v
    
    class Config:
        from_attributes = True


class AccountSimple(BaseModel):
    """Simplified account schema for nested responses"""
    id: int
    code: str
    name: str
    account_type: str
    
    class Config:
        from_attributes = True


class AccountConfigurationKeyResponse(BaseModel):
    """Schema for account configuration key response"""
    id: int
    code: str
    name: str
    description: Optional[str]
    default_account_id: Optional[int]
    default_account: Optional[AccountSimple]
    is_active: bool
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "code": "CASH",
                "name": "Cash Account",
                "description": "Default cash account for cash transactions",
                "default_account_id": 1,
                "default_account": {
                    "id": 1,
                    "code": "CASH001",
                    "name": "Cash in Hand",
                    "account_type": "ASSET"
                },
                "is_active": True,
                "created_at": "2025-01-01T00:00:00"
            }
        }


class AccountConfigurationKeyListResponse(BaseModel):
    """Schema for paginated list of configuration keys"""
    items: List[AccountConfigurationKeyResponse]
    pagination: dict = Field(..., description="Pagination metadata")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 1,
                        "code": "CASH",
                        "name": "Cash Account",
                        "description": "Default cash account",
                        "default_account_id": 1,
                        "default_account": {
                            "id": 1,
                            "code": "CASH001",
                            "name": "Cash in Hand",
                            "account_type": "ASSET"
                        },
                        "is_active": True,
                        "created_at": "2025-01-01T00:00:00"
                    }
                ],
                "pagination": {
                    "total": 13,
                    "page": 1,
                    "limit": 50,
                    "total_pages": 1
                }
            }
        }
