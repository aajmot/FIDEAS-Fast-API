from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

class AppointmentInvoiceStatus(str, Enum):
    DRAFT = 'DRAFT'
    POSTED = 'POSTED'
    CANCELLED = 'CANCELLED'

class AppointmentInvoicePaymentStatus(str, Enum):
    UNPAID = 'UNPAID'
    PARTIAL = 'PARTIAL'
    PAID = 'PAID'
    OVERPAID = 'OVERPAID'

class AppointmentInvoiceItemSchema(BaseModel):
    line_no: int = Field(..., gt=0)
    billing_master_id: Optional[int] = None
    description: str = Field(..., min_length=1)
    hsn_code: Optional[str] = None
    quantity: int = Field(default=1, gt=0)
    unit_price: Decimal = Field(..., ge=0)
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

class AppointmentInvoiceCreateSchema(BaseModel):
    invoice_number: str = Field(..., min_length=1, max_length=50)
    invoice_date: Optional[datetime] = None
    due_date: Optional[date] = None
    branch_id: Optional[int] = None
    appointment_id: int = Field(..., gt=0)
    patient_id: int = Field(..., gt=0)
    patient_name: Optional[str] = None
    patient_phone: Optional[str] = None
    patient_email: Optional[str] = None
    patient_address: Optional[str] = None
    patient_dob: Optional[date] = None
    patient_gender: Optional[str] = None
    doctor_id: int = Field(..., gt=0)
    doctor_name: Optional[str] = None
    doctor_phone: Optional[str] = None
    doctor_email: Optional[str] = None
    doctor_address: Optional[str] = None
    doctor_license_number: Optional[str] = None
    doctor_speciality: Optional[str] = None
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
    status: Optional[AppointmentInvoiceStatus] = Field(default=AppointmentInvoiceStatus.DRAFT)
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    items: List[AppointmentInvoiceItemSchema] = Field(..., min_items=1)

class AppointmentInvoiceUpdateSchema(BaseModel):
    invoice_date: Optional[datetime] = None
    due_date: Optional[date] = None
    status: Optional[AppointmentInvoiceStatus] = None
    payment_status: Optional[AppointmentInvoicePaymentStatus] = None
    paid_amount: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
