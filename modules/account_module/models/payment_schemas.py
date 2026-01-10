from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from modules.account_module.models.payment_enums import (
    PaymentType, PartyType, PaymentStatus, PaymentMode, DocumentType
)


class PaymentDetailRequest(BaseModel):
    """Schema for payment detail line item"""
    line_no: int = Field(..., ge=1, description="Line number")
    payment_mode: PaymentMode = Field(..., description="Payment mode")
    bank_account_id: Optional[int] = Field(None, description="Bank account ID")
    instrument_number: Optional[str] = Field(None, max_length=50, description="Cheque/DD number")
    instrument_date: Optional[date] = Field(None, description="Instrument date")
    bank_name: Optional[str] = Field(None, max_length=100, description="Bank name")
    branch_name: Optional[str] = Field(None, max_length=100, description="Branch name")
    ifsc_code: Optional[str] = Field(None, max_length=20, description="IFSC code")
    transaction_reference: Optional[str] = Field(None, max_length=100, description="UPI/NEFT reference")
    
    # Payment Gateway (per line)
    payment_gateway: Optional[str] = Field(None, max_length=50, description="Payment gateway")
    gateway_transaction_id: Optional[str] = Field(None, max_length=100, description="Gateway transaction ID")
    gateway_status: Optional[str] = Field(None, max_length=20, description="Gateway status")
    gateway_fee_base: Decimal = Field(0, ge=0, description="Gateway fee")
    gateway_response: Optional[str] = Field(None, description="Gateway response JSON")
    
    amount_base: Decimal = Field(..., gt=0, description="Amount in base currency")
    amount_foreign: Optional[Decimal] = Field(None, description="Amount in foreign currency")
    account_id: Optional[int] = Field(None, description="Account ID (Dr/Cr)")
    description: Optional[str] = Field(None, description="Description")
    
    class Config:
        from_attributes = True


class PaymentAllocationRequest(BaseModel):
    """Schema for payment allocation to invoices/orders"""
    document_type: DocumentType = Field(..., description="Document type")
    document_id: int = Field(..., description="Document ID")
    document_number: Optional[str] = Field(None, max_length=50, description="Document number")
    allocated_amount_base: Decimal = Field(..., gt=0, description="Allocated amount")
    allocated_amount_foreign: Optional[Decimal] = Field(None, description="Allocated amount in foreign currency")
    discount_amount_base: Decimal = Field(0, ge=0, description="Discount amount")
    adjustment_amount_base: Decimal = Field(0, description="Adjustment amount")
    remarks: Optional[str] = Field(None, description="Remarks")
    
    class Config:
        from_attributes = True


class PaymentRequest(BaseModel):
    """Schema for creating/updating payment"""
    payment_number: str = Field(..., max_length=50, description="Payment number")
    payment_date: datetime = Field(..., description="Payment date")
    payment_type: PaymentType = Field(..., description="Payment type")
    party_type: PartyType = Field(..., description="Party type")
    party_id: Optional[int] = Field(None, description="Party ID")
    party_name: str = Field(..., max_length=200, description="Party name")
    party_phone: str = Field(..., max_length=20, description="Party phone")
    branch_id: Optional[int] = Field(None, description="Branch ID")
    
    source_document_type: Optional[DocumentType] = Field(None, description="Source document type")
    source_document_id: Optional[int] = Field(None, description="Source document ID")
    
    base_currency_id: int = Field(..., description="Base currency ID")
    foreign_currency_id: Optional[int] = Field(None, description="Foreign currency ID")
    exchange_rate: Decimal = Field(1, gt=0, description="Exchange rate")
    
    total_amount_base: Decimal = Field(..., ge=0, description="Total amount")
    total_amount_foreign: Optional[Decimal] = Field(None, description="Total amount in foreign currency")
    allocated_amount_base: Decimal = Field(0, ge=0, description="Allocated amount")
    unallocated_amount_base: Decimal = Field(0, ge=0, description="Unallocated amount")
    
    tds_amount_base: Decimal = Field(0, ge=0, description="TDS amount")
    advance_amount_base: Decimal = Field(0, ge=0, description="Advance amount")
    
    is_refund: bool = Field(False, description="Is refund")
    original_payment_id: Optional[int] = Field(None, description="Original payment ID for refunds")
    
    status: PaymentStatus = Field(PaymentStatus.DRAFT, description="Status")
    
    reference_number: Optional[str] = Field(None, max_length=50, description="Bank reference/UTR")
    remarks: Optional[str] = Field(None, description="Remarks")
    tags: Optional[List[str]] = Field(None, description="Tags")
    
    details: List[PaymentDetailRequest] = Field(..., min_length=1, description="Payment details")
    allocations: Optional[List[PaymentAllocationRequest]] = Field(None, description="Payment allocations")
    
    class Config:
        from_attributes = True
    
    @validator('unallocated_amount_base')
    def validate_allocation(cls, v, values):
        if 'total_amount_base' in values and 'allocated_amount_base' in values:
            total = values['total_amount_base']
            allocated = values['allocated_amount_base']
            if allocated + v > total:
                raise ValueError('Allocated + Unallocated cannot exceed total amount')
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
    payment_gateway: Optional[str] = None
    gateway_transaction_id: Optional[str] = None
    gateway_status: Optional[str] = None
    gateway_fee_base: Decimal
    gateway_response: Optional[str] = None
    amount_base: Decimal
    amount_foreign: Optional[Decimal] = None
    account_id: Optional[int] = None
    description: Optional[str] = None
    
    class Config:
        from_attributes = True


class PaymentAllocationResponse(BaseModel):
    """Schema for payment allocation response"""
    id: int
    document_type: str
    document_id: int
    document_number: Optional[str] = None
    allocated_amount_base: Decimal
    allocated_amount_foreign: Optional[Decimal] = None
    discount_amount_base: Decimal
    adjustment_amount_base: Decimal
    allocation_date: datetime
    remarks: Optional[str] = None
    
    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    """Schema for payment response"""
    id: int
    payment_number: str
    payment_date: datetime
    payment_type: str
    party_type: str
    party_id: Optional[int] = None
    party_name: str
    party_phone: str
    branch_id: Optional[int] = None
    source_document_type: Optional[str] = None
    source_document_id: Optional[int] = None
    base_currency_id: int
    foreign_currency_id: Optional[int] = None
    exchange_rate: Decimal
    total_amount_base: Decimal
    total_amount_foreign: Optional[Decimal] = None
    allocated_amount_base: Decimal
    unallocated_amount_base: Decimal
    tds_amount_base: Decimal
    advance_amount_base: Decimal
    is_refund: bool
    original_payment_id: Optional[int] = None
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
    allocations: List[PaymentAllocationResponse] = []
    
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
