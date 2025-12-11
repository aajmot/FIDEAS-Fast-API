from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from decimal import Decimal

class ContraVoucherCreate(BaseModel):
    from_account_id: int = Field(..., description="Source account ID (cash/bank)")
    to_account_id: int = Field(..., description="Destination account ID (cash/bank)")
    amount: Decimal = Field(..., gt=0, description="Transfer amount")
    date: str = Field(..., description="Transaction date in ISO format")
    narration: Optional[str] = Field(None, description="Transaction description")
    voucher_number: Optional[str] = Field(None, description="Voucher number (auto-generated if not provided)")
    
    @validator('date')
    def validate_date(cls, v):
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError('Date must be in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)')
    
    @validator('from_account_id', 'to_account_id')
    def validate_account_ids(cls, v):
        if v <= 0:
            raise ValueError('Account ID must be positive')
        return v
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than zero')
        return v

class ContraVoucherResponse(BaseModel):
    id: int
    voucher_number: str
    date: str
    amount: float
    narration: Optional[str]
    
    class Config:
        from_attributes = True