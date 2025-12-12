from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum

class BookType(str, Enum):
    DAILY_BOOK = "DAILY_BOOK"
    CASH_BOOK = "CASH_BOOK"
    PETTY_CASH_BOOK = "PETTY_CASH_BOOK"

class LedgerBase(BaseModel):
    account_id: int
    voucher_id: int
    transaction_date: datetime
    debit_amount: Decimal = Field(default=0, ge=0)
    credit_amount: Decimal = Field(default=0, ge=0)
    narration: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    reference_number: Optional[str] = None

class LedgerCreate(LedgerBase):
    voucher_line_id: Optional[int] = None
    currency_id: Optional[int] = None
    exchange_rate: Optional[Decimal] = Field(default=1)
    debit_foreign: Optional[Decimal] = None
    credit_foreign: Optional[Decimal] = None

class LedgerResponse(LedgerBase):
    id: int
    tenant_id: int
    posting_date: datetime
    balance: Optional[Decimal]
    is_reconciled: bool
    is_posted: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class LedgerSummary(BaseModel):
    total_debit: Decimal
    total_credit: Decimal
    closing_balance: Decimal
    opening_balance: Optional[Decimal] = 0

class LedgerFilter(BaseModel):
    account_id: Optional[int] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    voucher_type: Optional[str] = None
    is_reconciled: Optional[bool] = None
    reference_type: Optional[str] = None
