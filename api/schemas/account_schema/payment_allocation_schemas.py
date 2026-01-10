from pydantic import BaseModel, Field, validator
from typing import List
from decimal import Decimal


class AllocateInvoiceItem(BaseModel):
    """Single invoice allocation item"""
    document_type: str = Field(..., description="Document type (TEST, SALES, PURCHASE, etc.)")
    document_id: int = Field(..., gt=0, description="Invoice ID")
    allocated_amount: Decimal = Field(..., gt=0, description="Amount to allocate")
    remarks: str = Field(None, description="Allocation remarks")
    
    @validator('document_type')
    def validate_document_type(cls, v):
        allowed = ['TEST', 'SALES', 'PURCHASE', 'INVOICE', 'EXPENSE', 'BILL']
        if v.upper() not in allowed:
            raise ValueError(f"document_type must be one of {allowed}")
        return v.upper()


class AllocatePaymentRequest(BaseModel):
    """Request to allocate payment to multiple invoices"""
    allocations: List[AllocateInvoiceItem] = Field(..., min_items=1, description="List of invoice allocations")
    
    @validator('allocations')
    def validate_unique_documents(cls, v):
        # Ensure no duplicate document allocations
        seen = set()
        for item in v:
            key = (item.document_type, item.document_id)
            if key in seen:
                raise ValueError(f"Duplicate allocation for {item.document_type} ID {item.document_id}")
            seen.add(key)
        return v


class AllocatePaymentResponse(BaseModel):
    """Response after payment allocation"""
    payment_id: int
    payment_number: str
    total_allocated: Decimal
    remaining_unallocated: Decimal
    allocations: List[dict]
    
    class Config:
        from_attributes = True
