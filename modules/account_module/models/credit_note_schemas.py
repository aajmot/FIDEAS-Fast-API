from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal


class CreditNoteItemRequest(BaseModel):
    """Schema for credit note line item"""
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


class CreditNoteItemResponse(BaseModel):
    """Schema for credit note item response"""
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


class CreditNoteRequest(BaseModel):
    """Schema for creating/updating credit note"""
    note_number: str = Field(..., max_length=50, description="Credit note number")
    reference_number: Optional[str] = Field(None, max_length=50, description="Internal reference")
    note_date: date = Field(..., description="Credit note date")
    due_date: Optional[date] = Field(None, description="Due date")
    
    # References
    customer_id: int = Field(..., description="Customer ID")
    original_invoice_id: Optional[int] = Field(None, description="Original sales invoice ID")
    original_invoice_number: Optional[str] = Field(None, max_length=50, description="Original invoice number")
    
    # Currency
    base_currency_id: Optional[int] = Field(None, description="Base currency ID (defaults to INR)")
    foreign_currency_id: Optional[int] = Field(None, description="Foreign currency ID")
    exchange_rate: Decimal = Field(1, gt=0, description="Exchange rate")
    
    # GST Summary (Base Currency)
    cgst_amount_base: Decimal = Field(0, ge=0, description="Total CGST")
    sgst_amount_base: Decimal = Field(0, ge=0, description="Total SGST")
    igst_amount_base: Decimal = Field(0, ge=0, description="Total IGST")
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
    
    # Status
    status: str = Field("DRAFT", description="Credit note status")
    credit_note_type: str = Field("SALES_RETURN", description="Credit note type")
    
    # Metadata
    reason: str = Field(..., description="Reason for credit note")
    notes: Optional[str] = Field(None, description="Additional notes")
    tags: Optional[List[str]] = Field(None, description="Tags")
    
    # Items
    items: List[CreditNoteItemRequest] = Field(..., min_length=1, description="Credit note items")
    
    class Config:
        from_attributes = True
    
    @validator('status')
    def validate_status(cls, v):
        """Validate status values"""
        valid_statuses = {'DRAFT', 'POSTED', 'APPLIED', 'CANCELLED'}
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v
    
    @validator('credit_note_type')
    def validate_credit_note_type(cls, v):
        """Validate credit note type values"""
        valid_types = {'SALES_RETURN', 'PRICE_ADJUSTMENT', 'DISCOUNT', 'OTHER'}
        if v not in valid_types:
            raise ValueError(f'Credit note type must be one of: {", ".join(valid_types)}')
        return v
    
    @validator('due_date')
    def validate_due_date(cls, v, values):
        """Ensure due date is not before note date"""
        if v and 'note_date' in values and v < values['note_date']:
            raise ValueError('Due date cannot be before note date')
        return v


class CreditNoteResponse(BaseModel):
    """Schema for credit note response"""
    id: int
    note_number: str
    reference_number: Optional[str] = None
    note_date: date
    due_date: Optional[date] = None
    customer_id: int
    customer_name: Optional[str] = None
    original_invoice_id: Optional[int] = None
    original_invoice_number: Optional[str] = None
    base_currency_id: int
    foreign_currency_id: Optional[int] = None
    exchange_rate: Decimal
    cgst_amount_base: Decimal
    sgst_amount_base: Decimal
    igst_amount_base: Decimal
    cess_amount_base: Decimal
    subtotal_base: Decimal
    discount_amount_base: Decimal
    tax_amount_base: Decimal
    total_amount_base: Decimal
    subtotal_foreign: Optional[Decimal] = None
    discount_amount_foreign: Optional[Decimal] = None
    tax_amount_foreign: Optional[Decimal] = None
    total_amount_foreign: Optional[Decimal] = None
    status: str
    credit_note_type: str
    voucher_id: Optional[int] = None
    reason: str
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    is_active: bool
    is_deleted: bool
    items: List[CreditNoteItemResponse] = []
    
    class Config:
        from_attributes = True


class CreditNoteListResponse(BaseModel):
    """Schema for paginated list of credit notes"""
    total: int
    page: int
    per_page: int
    total_pages: int
    data: List[CreditNoteResponse]
    
    class Config:
        from_attributes = True