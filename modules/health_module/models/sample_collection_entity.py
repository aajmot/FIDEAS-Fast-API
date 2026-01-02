from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.connection import Base

class SampleCollection(Base):
    __tablename__ = 'sample_collections'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    branch_id = Column(Integer, ForeignKey('branches.id'))
    
    collection_number = Column(String(50), nullable=False)
    collection_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    test_order_id = Column(Integer, ForeignKey('test_orders.id'), nullable=False)
    
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    patient_name = Column(String(200), nullable=False)
    patient_phone = Column(String(20), nullable=False)
    
    referring_doctor_id = Column(Integer, ForeignKey('doctors.id'))
    referring_doctor_name = Column(String(100))
    referring_doctor_phone = Column(String(100))
    referring_doctor_license = Column(String(100))
    is_external_doctor = Column(Boolean, default=False)
    
    collector_id = Column(Integer, ForeignKey('employees.id'))
    collector_name = Column(String(100))
    collector_phone = Column(String(20))
    is_external_collector = Column(Boolean, default=False)
    
    lab_technician_id = Column(Integer, ForeignKey('employees.id'))
    lab_technician_name = Column(String(100))
    lab_technician_phone = Column(String(20))
    lab_technician_email = Column(String(100))
    is_external_technician = Column(Boolean, default=False)
    received_at = Column(DateTime)
    
    sample_type = Column(String(50), nullable=False)
    collection_method = Column(String(50))
    collection_site = Column(String(100))
    container_type = Column(String(50))
    sample_volume = Column(Numeric(10, 2))
    volume_unit = Column(String(20), default='ml')
    
    sample_condition = Column(String(50), default='NORMAL')
    
    is_fasting = Column(Boolean, default=False)
    fasting_hours = Column(Integer)
    
    status = Column(String(20), default='COLLECTED')
    
    rejection_reason = Column(Text)
    rejected_at = Column(DateTime)
    
    remarks = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_deleted = Column(Boolean, default=False)
    
    items = relationship("SampleCollectionItem", back_populates="collection")

class SampleCollectionItem(Base):
    __tablename__ = 'sample_collection_items'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    collection_id = Column(Integer, ForeignKey('sample_collections.id'), nullable=False)
    line_no = Column(Integer, nullable=False)
    
    test_order_item_id = Column(Integer, ForeignKey('test_order_items.id'), nullable=False)
    
    test_id = Column(Integer, ForeignKey('tests.id'))
    test_name = Column(String(200))
    
    required_volume = Column(Numeric(10, 2))
    collected_volume = Column(Numeric(10, 2))
    
    item_status = Column(String(20), default='COLLECTED')
    
    result_value = Column(Text)
    result_unit = Column(String(50))
    reference_range = Column(String(100))
    is_abnormal = Column(Boolean, default=False)
    
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    verified_at = Column(DateTime)
    verified_by = Column(String(100))
    
    remarks = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_deleted = Column(Boolean, default=False)
    
    collection = relationship("SampleCollection", back_populates="items")
