from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class TestInvoiceStatus(str, Enum):
    DRAFT = 'DRAFT'
    POSTED = 'POSTED'  
class TestInvoicePaymentStatus(str, Enum):
    PAID = 'PAID'
    UNPAID = 'UNPAID',
    PARTIAL= 'PARTIAL',


class TestInvoiceItemSchema(BaseModel):
    line_no: int = Field(..., gt=0)
    test_id: Optional[int] = None
    test_name: Optional[str] = None
    panel_id: Optional[int] = None
    panel_name: Optional[str] = None
    rate: Decimal = Field(..., ge=0)
    disc_percentage: Optional[Decimal] = Field(default=0, ge=0, le=100)
    disc_amount: Optional[Decimal] = Field(default=0, ge=0)
    taxable_amount: Decimal = Field(..., ge=0)
    cgst_rate: Optional[Decimal] = Field(default=0, ge=0)
    cgst_amount: Optional[Decimal] = Field(default=0, ge=0)
    sgst_rate: Optional[Decimal] = Field(default=0, ge=0)
    sgst_amount: Optional[Decimal] = Field(default=0, ge=0)
    igst_rate: Optional[Decimal] = Field(default=0, ge=0)
    igst_amount: Optional[Decimal] = Field(default=0, ge=0)
    cess_rate: Optional[Decimal] = Field(default=0, ge=0)
    cess_amount: Optional[Decimal] = Field(default=0, ge=0)
    total_amount: Decimal = Field(..., ge=0)
    remarks: Optional[str] = None

class TestInvoiceCreateSchema(BaseModel):
    invoice_number: str = Field(..., min_length=1, max_length=50)
    invoice_date: Optional[datetime] = None
    due_date: Optional[date] = None
    branch_id: Optional[int] = None
    test_order_id: int = Field(..., gt=0)
    patient_id: Optional[int] = None
    patient_name: str = Field(..., min_length=1, max_length=200)
    patient_phone: str = Field(..., min_length=1, max_length=20)
    subtotal_amount: Decimal = Field(..., ge=0)
    items_total_discount_amount: Optional[Decimal] = Field(default=0, ge=0)
    taxable_amount: Decimal = Field(..., ge=0)
    cgst_amount: Optional[Decimal] = Field(default=0, ge=0)
    sgst_amount: Optional[Decimal] = Field(default=0, ge=0)
    igst_amount: Optional[Decimal] = Field(default=0, ge=0)
    cess_amount: Optional[Decimal] = Field(default=0, ge=0)
    overall_disc_percentage: Optional[Decimal] = Field(default=0, ge=0, le=100)
    overall_disc_amount: Optional[Decimal] = Field(default=0, ge=0)
    roundoff: Optional[Decimal] = Field(default=0)
    final_amount: Decimal = Field(..., ge=0)
    status: Optional[str] = Field(default='DRAFT')
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    items: List[TestInvoiceItemSchema] = Field(..., min_items=1)

class TestInvoiceUpdateSchema(BaseModel):
    invoice_date: Optional[datetime] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
