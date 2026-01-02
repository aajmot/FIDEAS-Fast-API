from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class TestOrderItemSchema(BaseModel):
    line_no: int = Field(..., gt=0)
    test_id: Optional[int] = None
    test_name: Optional[str] = None
    panel_id: Optional[int] = None
    panel_name: Optional[str] = None
    rate: Decimal = Field(..., ge=0)
    disc_percentage: Optional[Decimal] = Field(default=0, ge=0, le=100)
    disc_amount: Optional[Decimal] = Field(default=0, ge=0)
    taxable_amount: Decimal = Field(..., ge=0)
    cgst_rate: Optional[Decimal] = Field(default=0, ge=0, le=100)
    cgst_amount: Optional[Decimal] = Field(default=0, ge=0)
    sgst_rate: Optional[Decimal] = Field(default=0, ge=0, le=100)
    sgst_amount: Optional[Decimal] = Field(default=0, ge=0)
    igst_rate: Optional[Decimal] = Field(default=0, ge=0, le=100)
    igst_amount: Optional[Decimal] = Field(default=0, ge=0)
    cess_rate: Optional[Decimal] = Field(default=0, ge=0, le=100)
    cess_amount: Optional[Decimal] = Field(default=0, ge=0)
    total_amount: Decimal = Field(..., ge=0)
    item_status: Optional[str] = Field(default='PENDING')
    remarks: Optional[str] = None

    @validator('item_status')
    def validate_status(cls, v):
        allowed = ['PENDING', 'SAMPLE_COLLECTED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']
        if v and v not in allowed:
            raise ValueError(f'item_status must be one of {allowed}')
        return v

    @validator('test_id', 'panel_id')
    def validate_test_or_panel(cls, v, values):
        if 'test_id' in values and 'panel_id' in values:
            if not values.get('test_id') and not values.get('panel_id'):
                raise ValueError('Either test_id or panel_id must be provided')
            if values.get('test_id') and values.get('panel_id'):
                raise ValueError('Only one of test_id or panel_id should be provided')
        return v

class TestOrderCreateSchema(BaseModel):
    test_order_number: str = Field(..., min_length=1, max_length=50)
    order_date: Optional[datetime] = None
    patient_id: Optional[int] = Field(None, gt=0)
    patient_name: str = Field(..., min_length=1, max_length=200)
    patient_phone: str = Field(..., min_length=1, max_length=20)
    doctor_id: Optional[int] = Field(None, gt=0)
    doctor_name: str = Field(..., min_length=1, max_length=200)
    doctor_phone: Optional[str] = Field(None, max_length=20)
    doctor_license_number: Optional[str] = Field(None, max_length=100)
    appointment_id: Optional[int] = None
    agency_id: Optional[int] = None
    subtotal_amount: Decimal = Field(..., ge=0)
    items_total_discount_amount: Optional[Decimal] = Field(default=0, ge=0)
    taxable_amount: Decimal = Field(..., ge=0)
    cgst_amount: Optional[Decimal] = Field(default=0, ge=0)
    sgst_amount: Optional[Decimal] = Field(default=0, ge=0)
    igst_amount: Optional[Decimal] = Field(default=0, ge=0)
    cess_amount: Optional[Decimal] = Field(default=0, ge=0)
    overall_disc_percentage: Optional[Decimal] = Field(default=0, ge=0, le=100)
    overall_disc_amount: Optional[Decimal] = Field(default=0, ge=0)
    overall_cess_percentage: Optional[Decimal] = Field(default=0, ge=0, le=100)
    overall_cess_amount: Optional[Decimal] = Field(default=0, ge=0)
    roundoff: Optional[Decimal] = Field(default=0)
    final_amount: Decimal = Field(..., ge=0)
    urgency: Optional[str] = Field(default='ROUTINE')
    status: Optional[str] = Field(default='DRAFT')
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    items: Optional[List[TestOrderItemSchema]] = None

    @validator('urgency')
    def validate_urgency(cls, v):
        allowed = ['ROUTINE', 'URGENT', 'STAT', 'CRITICAL']
        if v and v not in allowed:
            raise ValueError(f'urgency must be one of {allowed}')
        return v

    @validator('status')
    def validate_status(cls, v):
        allowed = ['DRAFT', 'ORDERED', 'SAMPLE_COLLECTED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'REPORTED']
        if v and v not in allowed:
            raise ValueError(f'status must be one of {allowed}')
        return v

class TestOrderUpdateSchema(BaseModel):
    test_order_number: Optional[str] = Field(None, min_length=1, max_length=50)
    order_date: Optional[datetime] = None
    patient_id: Optional[int] = Field(None, gt=0)
    patient_name: Optional[str] = Field(None, min_length=1, max_length=200)
    patient_phone: Optional[str] = Field(None, min_length=1, max_length=20)
    doctor_id: Optional[int] = Field(None, gt=0)
    doctor_name: Optional[str] = Field(None, min_length=1, max_length=200)
    doctor_phone: Optional[str] = Field(None, max_length=20)
    doctor_license_number: Optional[str] = Field(None, max_length=100)
    appointment_id: Optional[int] = None
    agency_id: Optional[int] = None
    subtotal_amount: Optional[Decimal] = Field(None, ge=0)
    items_total_discount_amount: Optional[Decimal] = Field(None, ge=0)
    taxable_amount: Optional[Decimal] = Field(None, ge=0)
    cgst_amount: Optional[Decimal] = Field(None, ge=0)
    sgst_amount: Optional[Decimal] = Field(None, ge=0)
    igst_amount: Optional[Decimal] = Field(None, ge=0)
    cess_amount: Optional[Decimal] = Field(None, ge=0)
    overall_disc_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    overall_disc_amount: Optional[Decimal] = Field(None, ge=0)
    overall_cess_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    overall_cess_amount: Optional[Decimal] = Field(None, ge=0)
    roundoff: Optional[Decimal] = None
    final_amount: Optional[Decimal] = Field(None, ge=0)
    urgency: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    items: Optional[List[TestOrderItemSchema]] = Field(None, min_items=1)

    @validator('urgency')
    def validate_urgency(cls, v):
        if v:
            allowed = ['ROUTINE', 'URGENT', 'STAT', 'CRITICAL']
            if v not in allowed:
                raise ValueError(f'urgency must be one of {allowed}')
        return v

    @validator('status')
    def validate_status(cls, v):
        if v:
            allowed = ['DRAFT', 'ORDERED', 'SAMPLE_COLLECTED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'REPORTED']
            if v not in allowed:
                raise ValueError(f'status must be one of {allowed}')
        return v
