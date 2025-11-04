from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

class PurchaseOrderItem(BaseModel):
    product_id: int
    product_name: str
    quantity: Decimal
    free_quantity: Decimal = Field(default=0)
    unit_price: Decimal
    mrp: Optional[Decimal] = None
    line_discount_percent: Decimal = Field(default=0)
    line_discount_amount: Decimal = Field(default=0)
    taxable_amount: Decimal
    cgst_rate: Decimal = Field(default=0)
    cgst_amount: Decimal = Field(default=0)
    sgst_rate: Decimal = Field(default=0)
    sgst_amount: Decimal = Field(default=0)
    igst_rate: Decimal = Field(default=0)
    igst_amount: Decimal = Field(default=0)
    ugst_rate: Decimal = Field(default=0)
    ugst_amount: Decimal = Field(default=0)
    cess_rate: Decimal = Field(default=0)
    cess_amount: Decimal = Field(default=0)
    total_price: Decimal
    batch_number: str = ""
    expiry_date: Optional[datetime] = None
    is_active: bool = True
    hsn_code: Optional[str] = None
    description: Optional[str] = None

    @validator('expiry_date', pre=True)
    def empty_string_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v

    class Config:
        from_attributes = True

class PurchaseOrderRequest(BaseModel):
    # Order header fields
    po_number: str
    supplier_id: int
    reference_number: Optional[str] = None
    order_date: datetime
    supplier_name: Optional[str] = None
    supplier_gstin: Optional[str] = None
    supplier_address: Optional[str] = None
    
    # Amount breakdown
    subtotal_amount: Decimal
    header_discount_percent: Decimal = Field(default=0)
    header_discount_amount: Decimal = Field(default=0)
    taxable_amount: Decimal
    cgst_amount: Decimal = Field(default=0)
    sgst_amount: Decimal = Field(default=0)
    igst_amount: Decimal = Field(default=0)
    utgst_amount: Decimal = Field(default=0)
    cess_amount: Decimal = Field(default=0)
    total_tax_amount: Optional[Decimal] = Field(default=None, exclude=True)  # GENERATED in DB - ignored if passed
    roundoff: Decimal = Field(default=0)
    net_amount: Decimal
    
    # Currency
    currency_id: int = Field(default=1)
    exchange_rate: Decimal = Field(default=1)
    net_amount_base: Optional[Decimal] = Field(default=None, exclude=True)  # GENERATED in DB - ignored if passed
    
    # Tax flags
    is_reverse_charge: bool = False
    is_tax_inclusive: bool = False
    
    # Status
    status: str = Field(default="DRAFT")
    approval_status: str = Field(default="DRAFT")
    
    # Order items
    items: List[PurchaseOrderItem]

    class Config:
        from_attributes = True

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = {'DRAFT', 'APPROVED', 'RECEIVED', 'BILLED', 'CANCELLED', 'REVERSED'}
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v
