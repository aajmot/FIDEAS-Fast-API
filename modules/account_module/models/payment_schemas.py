from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal


class PaymentDetailRequest(BaseModel):
    """Schema for payment detail line item"""
    line_no: int = Field(..., ge=1, description="Line number")
    payment_mode: str = Field(..., description="Payment mode")
    bank_account_id: Optional[int] = Field(None, description="Bank account ID")
    instrument_number: Optional[str] = Field(None, max_length=50, description="Cheque/DD number")
    instrument_date: Optional[date] = Field(None, description="Instrument date")
    bank_name: Optional[str] = Field(None, max_length=100, description="Bank name")
    branch_name: Optional[str] = Field(None, max_length=100, description="Branch name")
    ifsc_code: Optional[str] = Field(None, max_length=20, description="IFSC code")
    transaction_reference: Optional[str] = Field(None, max_length=100, description="UPI/NEFT reference")
    amount_base: Decimal = Field(..., gt=0, description="Amount in base currency")
    amount_foreign: Optional[Decimal] = Field(None, description="Amount in foreign currency")
    account_id: Optional[int] = Field(None, description="Account ID (Dr/Cr) - auto-determined if not provided")
    description: Optional[str] = Field(None, description="Description")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "line_no": 1,
                "payment_mode": "BANK",
                "bank_account_id": 1,
                "transaction_reference": "NEFT123456",
                "amount_base": 10000.00,
                "account_id": 1,
                "description": "Payment via bank transfer"
            }
        }
    
    @validator('payment_mode')
    def validate_payment_mode(cls, v):
        """Validate payment mode"""
        valid_modes = {'CASH', 'BANK', 'CARD', 'UPI', 'CHEQUE', 'ONLINE', 'WALLET'}
        if v not in valid_modes:
            raise ValueError(f'Payment mode must be one of: {", ".join(valid_modes)}')
        return v


class PaymentDetailResponse(BaseModel):
    """Schema for payment detail response"""
    id: int
    line_no: int
    payment_mode: str
    bank_account_id: Optional[int] = None
    instrument_number: Optional[str] = None
    instrument_date: Optional[date] = None
    bank_name: Optional[str] = None
    branch_name: Optional[str] = None
    ifsc_code: Optional[str] = None
    transaction_reference: Optional[str] = None
    amount_base: Decimal
    amount_foreign: Optional[Decimal] = None
    account_id: int
    description: Optional[str] = None
    
    class Config:
        from_attributes = True


class PaymentRequest(BaseModel):
    """Schema for creating/updating payment"""
    payment_number: str = Field(..., max_length=50, description="Payment number")
    payment_date: datetime = Field(..., description="Payment date")
    payment_type: str = Field(..., description="Payment type: RECEIPT, PAYMENT, CONTRA")
    party_type: str = Field(..., description="Party type: CUSTOMER, SUPPLIER, EMPLOYEE, BANK, OTHER")
    party_id: Optional[int] = Field(None, description="Party ID (customer/supplier/employee)")
    
    # Currency
    base_currency_id: int = Field(..., description="Base currency ID")
    foreign_currency_id: Optional[int] = Field(None, description="Foreign currency ID")
    exchange_rate: Decimal = Field(1, gt=0, description="Exchange rate")
    
    # Amounts
    total_amount_base: Decimal = Field(..., ge=0, description="Total amount in base currency")
    total_amount_foreign: Optional[Decimal] = Field(None, description="Total amount in foreign currency")
    
    # TDS / Advance
    tds_amount_base: Decimal = Field(0, ge=0, description="TDS amount")
    advance_amount_base: Decimal = Field(0, ge=0, description="Advance amount")
    
    # Status
    status: str = Field("DRAFT", description="Status: DRAFT, POSTED, CANCELLED, RECONCILED")
    
    # Metadata
    reference_number: Optional[str] = Field(None, max_length=50, description="Bank reference/UTR")
    remarks: Optional[str] = Field(None, description="Remarks")
    tags: Optional[List[str]] = Field(None, description="Tags")
    
    # Payment details
    details: List[PaymentDetailRequest] = Field(..., min_length=1, description="Payment details")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "payment_number": "PAY-2025-001",
                "payment_date": "2025-01-15T10:00:00",
                "payment_type": "PAYMENT",
                "party_type": "SUPPLIER",
                "party_id": 1,
                "base_currency_id": 1,
                "exchange_rate": 1,
                "total_amount_base": 10000.00,
                "tds_amount_base": 100.00,
                "status": "DRAFT",
                "reference_number": "NEFT123456",
                "remarks": "Payment for purchase",
                "details": [
                    {
                        "line_no": 1,
                        "payment_mode": "BANK",
                        "bank_account_id": 1,
                        "transaction_reference": "NEFT123456",
                        "amount_base": 10000.00,
                        "account_id": 1,
                        "description": "Bank transfer"
                    }
                ]
            }
        }
    
    @validator('payment_type')
    def validate_payment_type(cls, v):
        """Validate payment type"""
        valid_types = {'RECEIPT', 'PAYMENT', 'CONTRA'}
        if v not in valid_types:
            raise ValueError(f'Payment type must be one of: {", ".join(valid_types)}')
        return v
    
    @validator('party_type')
    def validate_party_type(cls, v):
        """Validate party type"""
        valid_types = {'CUSTOMER', 'SUPPLIER', 'EMPLOYEE', 'BANK', 'OTHER'}
        if v not in valid_types:
            raise ValueError(f'Party type must be one of: {", ".join(valid_types)}')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        """Validate status"""
        valid_statuses = {'DRAFT', 'POSTED', 'CANCELLED', 'RECONCILED'}
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v
    
    @validator('foreign_currency_id')
    def validate_foreign_currency(cls, v, values):
        """Validate foreign currency logic"""
        if v is None:
            if values.get('exchange_rate', 1) != 1:
                raise ValueError('Exchange rate must be 1 when no foreign currency')
        else:
            if values.get('exchange_rate', 0) <= 0:
                raise ValueError('Exchange rate must be positive when foreign currency is set')
        return v


class PaymentResponse(BaseModel):
    """Schema for payment response"""
    id: int
    payment_number: str
    payment_date: datetime
    payment_type: str
    party_type: str
    party_id: Optional[int] = None
    base_currency_id: int
    foreign_currency_id: Optional[int] = None
    exchange_rate: Decimal
    total_amount_base: Decimal
    total_amount_foreign: Optional[Decimal] = None
    tds_amount_base: Decimal
    advance_amount_base: Decimal
    status: str
    voucher_id: Optional[int] = None
    reference_number: Optional[str] = None
    remarks: Optional[str] = None
    tags: Optional[List[str]] = None
    is_reconciled: bool
    reconciled_at: Optional[datetime] = None
    reconciled_by: Optional[str] = None
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    is_active: bool
    is_deleted: bool
    details: List[PaymentDetailResponse] = []
    
    class Config:
        from_attributes = True


class PaymentListResponse(BaseModel):
    """Schema for paginated list of payments"""
    total: int
    page: int
    per_page: int
    total_pages: int
    data: List[PaymentResponse]
    
    class Config:
        from_attributes = True


class ReconcilePaymentRequest(BaseModel):
    """Schema for reconciling payment"""
    payment_id: int = Field(..., description="Payment ID to reconcile")
    reconciled_at: Optional[datetime] = Field(None, description="Reconciliation date")
    
    class Config:
        from_attributes = True
