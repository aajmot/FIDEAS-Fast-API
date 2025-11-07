from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class AccountMasterRequest(BaseModel):
    """Schema for creating/updating account master"""
    code: str = Field(..., max_length=50, description="Account code (unique per tenant)")
    name: str = Field(..., max_length=200, description="Account name")
    description: Optional[str] = Field(None, description="Account description")
    
    # References
    parent_id: Optional[int] = Field(None, description="Parent account ID for hierarchy")
    account_group_id: int = Field(..., description="Account group ID")
    
    # Account Type
    account_type: str = Field(..., description="Account type: ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE")
    normal_balance: str = Field("D", max_length=1, description="Normal balance: D (Debit) or C (Credit)")
    
    # System Account
    is_system_account: bool = Field(False, description="Whether this is a system account")
    system_code: Optional[str] = Field(None, max_length=50, description="System code for protected accounts")
    
    # Hierarchy
    level: int = Field(1, ge=1, description="Hierarchy level (1 = top level)")
    path: Optional[str] = Field(None, description="Path for tree queries")
    
    # Balances
    opening_balance: Decimal = Field(0, description="Opening balance")
    current_balance: Decimal = Field(0, description="Current balance")
    is_reconciled: bool = Field(False, description="Whether account is reconciled (for bank accounts)")
    
    # Status
    is_active: bool = Field(True, description="Whether account is active")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "code": "CASH001",
                "name": "Cash in Hand",
                "description": "Petty cash account",
                "account_group_id": 1,
                "account_type": "ASSET",
                "normal_balance": "D",
                "is_system_account": False,
                "level": 1,
                "opening_balance": 10000.00,
                "current_balance": 10000.00,
                "is_active": True
            }
        }
    
    @validator('account_type')
    def validate_account_type(cls, v):
        """Validate account type"""
        valid_types = {'ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE'}
        if v not in valid_types:
            raise ValueError(f'Account type must be one of: {", ".join(valid_types)}')
        return v
    
    @validator('normal_balance')
    def validate_normal_balance(cls, v):
        """Validate normal balance"""
        if v not in ('D', 'C'):
            raise ValueError('Normal balance must be D (Debit) or C (Credit)')
        return v
    
    @validator('system_code')
    def validate_system_code(cls, v, values):
        """Validate system code is provided for system accounts"""
        if values.get('is_system_account') and not v:
            raise ValueError('System code is required for system accounts')
        return v


class AccountMasterResponse(BaseModel):
    """Schema for account master response"""
    id: int
    tenant_id: int
    parent_id: Optional[int] = None
    account_group_id: int
    
    # Core
    code: str
    name: str
    description: Optional[str] = None
    
    # Account Type
    account_type: str
    normal_balance: str
    
    # System Account
    is_system_account: bool
    system_code: Optional[str] = None
    
    # Hierarchy
    level: int
    path: Optional[str] = None
    
    # Balances
    opening_balance: Decimal
    current_balance: Decimal
    is_reconciled: bool
    
    # Status
    is_active: bool
    is_deleted: bool
    
    # Audit
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "tenant_id": 1,
                "parent_id": None,
                "account_group_id": 1,
                "code": "CASH001",
                "name": "Cash in Hand",
                "description": "Petty cash account",
                "account_type": "ASSET",
                "normal_balance": "D",
                "is_system_account": False,
                "system_code": None,
                "level": 1,
                "path": None,
                "opening_balance": 10000.00,
                "current_balance": 15500.50,
                "is_reconciled": False,
                "is_active": True,
                "is_deleted": False,
                "created_at": "2025-01-01T00:00:00",
                "created_by": "admin",
                "updated_at": "2025-01-15T10:30:00",
                "updated_by": "admin"
            }
        }


class AccountMasterListResponse(BaseModel):
    """Schema for paginated list of account masters"""
    total: int
    page: int
    per_page: int
    total_pages: int
    data: List[AccountMasterResponse]
    
    class Config:
        from_attributes = True
