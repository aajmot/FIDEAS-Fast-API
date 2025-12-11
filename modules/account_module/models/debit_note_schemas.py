from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal


class DebitNoteItemRequest(BaseModel):
    """Schema for debit note line item"""
    line_no: int = Field(..., ge=1, description="Line number")
    product_id: int = Field(..., description="Product ID")
    description: Optional[str] = Field(None, description="Item description")
    hsn_code: Optional[str] = Field(None, max_length=20, description="HSN code")
    batch_number: Optional[str] = Field(None, max_length=50, description="Batch number")
    serial_numbers: Optional[str] = Field(None, description="Serial numbers (comma-separated)")
    
    # Quantity
    quantity: Decimal = Field(..., gt=0, description="Quantity")
    free_quantity: Decimal = Field(0, ge=0, description="Free/complimentary quantity")
    uom: str = Field("NOS", max_length=20, description="Unit of measurement")
    
    # Pricing (Base Currency)
    unit_price_base: Decimal = Field(..., ge=0, description="Unit price in base currency")
    discount_percent: Decimal = Field(0, ge=0, le=100, description="Discount percentage")
    discount_amount_base: Decimal = Field(0, ge=0, description="Discount amount")
    taxable_amount_base: Decimal = Field(..., ge=0, description="Taxable amount")
    
    # GST Components
    cgst_rate: Decimal = Field(0, ge=0, le=100, description="CGST rate")
    cgst_amount_base: Decimal = Field(0, ge=0, description="CGST amount")
    sgst_rate: Decimal = Field(0, ge=0, le=100, description="SGST rate")
    sgst_amount_base: Decimal = Field(0, ge=0, description="SGST amount")
    igst_rate: Decimal = Field(0, ge=0, le=100, description="IGST rate")
    igst_amount_base: Decimal = Field(0, ge=0, description="IGST amount")
    ugst_rate: Decimal = Field(0, ge=0, le=100, description="UGST rate")
    ugst_amount_base: Decimal = Field(0, ge=0, description="UGST amount")
    cess_rate: Decimal = Field(0, ge=0, le=100, description="CESS rate")
    cess_amount_base: Decimal = Field(0, ge=0, description="CESS amount")
    tax_amount_base: Decimal = Field(0, ge=0, description="Total tax amount")
    
    # Total
    total_amount_base: Decimal = Field(..., ge=0, description="Total line amount")
    
    # Foreign Currency (Optional)
    unit_price_foreign: Optional[Decimal] = Field(None, description="Unit price in foreign currency")
    discount_amount_foreign: Optional[Decimal] = Field(None, description="Discount in foreign currency")
    taxable_amount_foreign: Optional[Decimal] = Field(None, description="Taxable amount in foreign currency")
    tax_amount_foreign: Optional[Decimal] = Field(None, description="Tax in foreign currency")
    total_amount_foreign: Optional[Decimal] = Field(None, description="Total in foreign currency")
    
    class Config:
        from_attributes = True


class DebitNoteItemResponse(BaseModel):
    """Schema for debit note item response"""
    id: int
    line_no: int
    product_id: int
    description: Optional[str] = None
    hsn_code: Optional[str] = None
    batch_number: Optional[str] = None
    serial_numbers: Optional[str] = None
    quantity: Decimal
    free_quantity: Decimal
    uom: str
    unit_price_base: Decimal
    discount_percent: Decimal
    discount_amount_base: Decimal
    taxable_amount_base: Decimal
    cgst_rate: Decimal
    cgst_amount_base: Decimal
    sgst_rate: Decimal
    sgst_amount_base: Decimal
    igst_rate: Decimal
    igst_amount_base: Decimal
    ugst_rate: Decimal
    ugst_amount_base: Decimal
    cess_rate: Decimal
    cess_amount_base: Decimal
    tax_amount_base: Decimal
    total_amount_base: Decimal
    unit_price_foreign: Optional[Decimal] = None
    discount_amount_foreign: Optional[Decimal] = None
    taxable_amount_foreign: Optional[Decimal] = None
    tax_amount_foreign: Optional[Decimal] = None
    total_amount_foreign: Optional[Decimal] = None
    
    class Config:
        from_attributes = True


class DebitNoteRequest(BaseModel):
    """Schema for creating/updating debit note"""
    note_number: str = Field(..., max_length=50, description="Debit note number")
    reference_number: Optional[str] = Field(None, max_length=50, description="Internal reference")
    note_date: date = Field(..., description="Debit note date")
    due_date: Optional[date] = Field(None, description="Due date")
    
    # References
    supplier_id: int = Field(..., description="Supplier ID")
    original_invoice_id: Optional[int] = Field(None, description="Original purchase invoice ID")
    original_invoice_number: Optional[str] = Field(None, max_length=50, description="Original invoice number")
    payment_term_id: Optional[int] = Field(None, description="Payment term ID")
    
    # Currency
    base_currency_id: Optional[int] = Field(None, description="Base currency ID (defaults to INR)")
    foreign_currency_id: Optional[int] = Field(None, description="Foreign currency ID")
    exchange_rate: Decimal = Field(1, gt=0, description="Exchange rate")
    
    # GST Summary (Base Currency)
    cgst_amount_base: Decimal = Field(0, ge=0, description="Total CGST")
    sgst_amount_base: Decimal = Field(0, ge=0, description="Total SGST")
    igst_amount_base: Decimal = Field(0, ge=0, description="Total IGST")
    ugst_amount_base: Decimal = Field(0, ge=0, description="Total UGST")
    cess_amount_base: Decimal = Field(0, ge=0, description="Total CESS")
    
    # Totals (Base Currency)
    subtotal_base: Decimal = Field(0, ge=0, description="Subtotal")
    discount_amount_base: Decimal = Field(0, ge=0, description="Discount amount")
    tax_amount_base: Decimal = Field(0, ge=0, description="Total tax")
    total_amount_base: Decimal = Field(..., ge=0, description="Total amount")
    
    # Totals (Foreign Currency)
    subtotal_foreign: Optional[Decimal] = Field(None, description="Subtotal in foreign currency")
    discount_amount_foreign: Optional[Decimal] = Field(None, description="Discount in foreign currency")
    tax_amount_foreign: Optional[Decimal] = Field(None, description="Tax in foreign currency")
    total_amount_foreign: Optional[Decimal] = Field(None, description="Total in foreign currency")
    
    # Payment
    paid_amount_base: Decimal = Field(0, ge=0, description="Paid amount")
    balance_amount_base: Decimal = Field(0, ge=0, description="Balance amount")
    
    # Status
    status: str = Field("DRAFT", description="Debit note status")
    
    # Metadata
    reason: Optional[str] = Field(None, description="Reason for debit note")
    notes: Optional[str] = Field(None, description="Additional notes")
    tags: Optional[List[str]] = Field(None, description="Tags")
    
    # Items
    items: List[DebitNoteItemRequest] = Field(..., min_length=1, description="Debit note items")
    
    class Config:
        from_attributes = True
    
    @validator('status')
    def validate_status(cls, v):
        """Validate status values"""
        valid_statuses = {'DRAFT', 'POSTED', 'PAID', 'PARTIALLY_PAID', 'CANCELLED'}
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v
    
    @validator('due_date')
    def validate_due_date(cls, v, values):
        """Ensure due date is not before note date"""
        if v and 'note_date' in values and v < values['note_date']:
            raise ValueError('Due date cannot be before note date')
        return v


class DebitNoteResponse(BaseModel):
    """Schema for debit note response"""
    id: int
    note_number: str
    reference_number: Optional[str] = None
    note_date: date
    due_date: Optional[date] = None
    supplier_id: int
    supplier_name: Optional[str] = None
    original_invoice_id: Optional[int] = None
    original_invoice_number: Optional[str] = None
    payment_term_id: Optional[int] = None
    base_currency_id: int
    foreign_currency_id: Optional[int] = None
    exchange_rate: Decimal
    cgst_amount_base: Decimal
    sgst_amount_base: Decimal
    igst_amount_base: Decimal
    ugst_amount_base: Decimal
    cess_amount_base: Decimal
    subtotal_base: Decimal
    discount_amount_base: Decimal
    tax_amount_base: Decimal
    total_amount_base: Decimal
    subtotal_foreign: Optional[Decimal] = None
    discount_amount_foreign: Optional[Decimal] = None
    tax_amount_foreign: Optional[Decimal] = None
    total_amount_foreign: Optional[Decimal] = None
    paid_amount_base: Decimal
    balance_amount_base: Decimal
    status: str
    voucher_id: Optional[int] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    is_active: bool
    is_deleted: bool
    items: List[DebitNoteItemResponse] = []
    
    class Config:
        from_attributes = True


class DebitNoteListResponse(BaseModel):
    """Schema for paginated list of debit notes"""
    total: int
    page: int
    per_page: int
    total_pages: int
    data: List[DebitNoteResponse]
    
    class Config:
        from_attributes = True