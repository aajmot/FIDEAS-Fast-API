from pydantic import BaseModel, Field
from typing import Optional


class AccountConfigurationRequest(BaseModel):
    """Schema for creating/updating account configuration"""
    account_id: int = Field(..., gt=0, description="Account master ID to map to this configuration")
    module: Optional[str] = Field(None, max_length=30, description="Optional module-specific configuration (e.g., PURCHASE, SALES, INVENTORY)")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "account_id": 501,
                "module": "PURCHASE"
            }
        }


class AccountConfigurationResponse(BaseModel):
    """Schema for account configuration response"""
    id: int = Field(..., description="Configuration ID")
    config_key: str = Field(..., description="Configuration key code (e.g., INVENTORY, GST_OUTPUT)")
    config_name: str = Field(..., description="Human-readable configuration name")
    account_id: int = Field(..., description="Mapped account master ID")
    account_name: str = Field(..., description="Account name")
    account_code: str = Field(..., description="Account code")
    module: Optional[str] = Field(None, description="Module-specific configuration")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "config_key": "INVENTORY",
                "config_name": "Inventory Account",
                "account_id": 501,
                "account_name": "Stock Inventory",
                "account_code": "INV001",
                "module": "PURCHASE"
            }
        }


class AccountConfigurationListResponse(BaseModel):
    """Schema for list of account configurations"""
    success: bool
    message: str
    data: list[AccountConfigurationResponse]
    
    class Config:
        from_attributes = True
