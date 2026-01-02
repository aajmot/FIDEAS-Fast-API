from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class SampleCollectionItemSchema(BaseModel):
    line_no: int = Field(..., gt=0)
    test_order_item_id: int = Field(..., gt=0)
    test_id: Optional[int] = None
    test_name: Optional[str] = None
    required_volume: Optional[Decimal] = Field(None, ge=0)
    collected_volume: Optional[Decimal] = Field(None, ge=0)
    item_status: Optional[str] = Field(default='COLLECTED')
    result_value: Optional[str] = None
    result_unit: Optional[str] = None
    reference_range: Optional[str] = None
    is_abnormal: Optional[bool] = False
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    remarks: Optional[str] = None

    @validator('item_status')
    def validate_status(cls, v):
        allowed = ['COLLECTED', 'RECEIVED', 'IN_PROGRESS', 'COMPLETED', 'REJECTED']
        if v and v not in allowed:
            raise ValueError(f'item_status must be one of {allowed}')
        return v

class SampleCollectionCreateSchema(BaseModel):
    branch_id: Optional[int] = None
    collection_number: str = Field(..., min_length=1, max_length=50)
    collection_date: Optional[datetime] = None
    test_order_id: int = Field(..., gt=0)
    patient_id: int = Field(..., gt=0)
    patient_name: str = Field(..., min_length=1, max_length=200)
    patient_phone: str = Field(..., min_length=1, max_length=20)
    referring_doctor_id: Optional[int] = None
    referring_doctor_name: Optional[str] = Field(None, max_length=100)
    referring_doctor_phone: Optional[str] = Field(None, max_length=100)
    referring_doctor_license: Optional[str] = Field(None, max_length=100)
    is_external_doctor: Optional[bool] = False
    collector_id: Optional[int] = None
    collector_name: Optional[str] = Field(None, max_length=100)
    collector_phone: Optional[str] = Field(None, max_length=20)
    is_external_collector: Optional[bool] = False
    lab_technician_id: Optional[int] = None
    lab_technician_name: Optional[str] = Field(None, max_length=100)
    lab_technician_phone: Optional[str] = Field(None, max_length=20)
    lab_technician_email: Optional[str] = Field(None, max_length=100)
    is_external_technician: Optional[bool] = False
    received_at: Optional[datetime] = None
    sample_type: str = Field(..., max_length=50)
    collection_method: Optional[str] = Field(None, max_length=50)
    collection_site: Optional[str] = Field(None, max_length=100)
    container_type: Optional[str] = Field(None, max_length=50)
    sample_volume: Optional[Decimal] = Field(None, ge=0)
    volume_unit: Optional[str] = Field(default='ml', max_length=20)
    sample_condition: Optional[str] = Field(default='NORMAL', max_length=50)
    is_fasting: Optional[bool] = False
    fasting_hours: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(default='COLLECTED', max_length=20)
    rejection_reason: Optional[str] = None
    rejected_at: Optional[datetime] = None
    remarks: Optional[str] = None
    items: Optional[List[SampleCollectionItemSchema]] = None

    @validator('sample_type')
    def validate_sample_type(cls, v):
        allowed = ['BLOOD', 'URINE', 'STOOL', 'SPUTUM', 'SWAB', 'TISSUE', 'OTHER']
        if v and v not in allowed:
            raise ValueError(f'sample_type must be one of {allowed}')
        return v

    @validator('sample_condition')
    def validate_condition(cls, v):
        allowed = ['NORMAL', 'HEMOLYZED', 'CLOTTED', 'INSUFFICIENT', 'CONTAMINATED', 'REJECTED']
        if v and v not in allowed:
            raise ValueError(f'sample_condition must be one of {allowed}')
        return v

    @validator('status')
    def validate_status(cls, v):
        allowed = ['COLLECTED', 'RECEIVED', 'PROCESSING', 'COMPLETED', 'REJECTED']
        if v and v not in allowed:
            raise ValueError(f'status must be one of {allowed}')
        return v

class SampleCollectionUpdateSchema(BaseModel):
    branch_id: Optional[int] = None
    collection_number: Optional[str] = Field(None, min_length=1, max_length=50)
    collection_date: Optional[datetime] = None
    patient_name: Optional[str] = Field(None, min_length=1, max_length=200)
    patient_phone: Optional[str] = Field(None, min_length=1, max_length=20)
    referring_doctor_id: Optional[int] = None
    referring_doctor_name: Optional[str] = Field(None, max_length=100)
    referring_doctor_phone: Optional[str] = Field(None, max_length=100)
    referring_doctor_license: Optional[str] = Field(None, max_length=100)
    is_external_doctor: Optional[bool] = None
    collector_id: Optional[int] = None
    collector_name: Optional[str] = Field(None, max_length=100)
    collector_phone: Optional[str] = Field(None, max_length=20)
    is_external_collector: Optional[bool] = None
    lab_technician_id: Optional[int] = None
    lab_technician_name: Optional[str] = Field(None, max_length=100)
    lab_technician_phone: Optional[str] = Field(None, max_length=20)
    lab_technician_email: Optional[str] = Field(None, max_length=100)
    is_external_technician: Optional[bool] = None
    received_at: Optional[datetime] = None
    sample_type: Optional[str] = Field(None, max_length=50)
    collection_method: Optional[str] = Field(None, max_length=50)
    collection_site: Optional[str] = Field(None, max_length=100)
    container_type: Optional[str] = Field(None, max_length=50)
    sample_volume: Optional[Decimal] = Field(None, ge=0)
    volume_unit: Optional[str] = Field(None, max_length=20)
    sample_condition: Optional[str] = Field(None, max_length=50)
    is_fasting: Optional[bool] = None
    fasting_hours: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None, max_length=20)
    rejection_reason: Optional[str] = None
    rejected_at: Optional[datetime] = None
    remarks: Optional[str] = None
    items: Optional[List[SampleCollectionItemSchema]] = None

    @validator('sample_type')
    def validate_sample_type(cls, v):
        if v:
            allowed = ['BLOOD', 'URINE', 'STOOL', 'SPUTUM', 'SWAB', 'TISSUE', 'OTHER']
            if v not in allowed:
                raise ValueError(f'sample_type must be one of {allowed}')
        return v

    @validator('sample_condition')
    def validate_condition(cls, v):
        if v:
            allowed = ['NORMAL', 'HEMOLYZED', 'CLOTTED', 'INSUFFICIENT', 'CONTAMINATED', 'REJECTED']
            if v not in allowed:
                raise ValueError(f'sample_condition must be one of {allowed}')
        return v

    @validator('status')
    def validate_status(cls, v):
        if v:
            allowed = ['COLLECTED', 'RECEIVED', 'PROCESSING', 'COMPLETED', 'REJECTED']
            if v not in allowed:
                raise ValueError(f'status must be one of {allowed}')
        return v
