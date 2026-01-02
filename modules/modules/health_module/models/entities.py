from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Numeric, Enum, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.connection import Base
import enum

class TestPanel(Base):
    __tablename__ = 'test_panels'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category_id = Column(Integer, ForeignKey('test_categories.id'))
    cost = Column(Numeric(10, 2))
    gst = Column(Numeric(5, 2))
    cess = Column(Numeric(5, 2))
    expired_on = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100))
    is_deleted = Column(Boolean, default=False)
    
    items = relationship("TestPanelItem", back_populates="panel")

class TestPanelItem(Base):
    __tablename__ = 'test_panel_items'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    panel_id = Column(Integer, ForeignKey('test_panels.id'), nullable=False)
    test_id = Column(Integer, ForeignKey('tests.id'), nullable=False)
    test_name = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100))
    is_deleted = Column(Boolean, default=False)
    
    panel = relationship("TestPanel", back_populates="items")

class TestOrder(Base):
    __tablename__ = 'test_orders'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    test_order_number = Column(Text, unique=True, nullable=False)
    appointment_id = Column(Integer, ForeignKey('appointments.id'))
    patient_name = Column(String(200))
    patient_phone = Column(String(20))
    doctor_name = Column(String(200))
    doctor_phone = Column(String(20))
    doctor_license_number = Column(String(100))
    order_date = Column(DateTime, default=datetime.utcnow)
    status = Column(Text)
    urgency = Column(Text)
    notes = Column(Text)
    agency_id = Column(Integer, ForeignKey('agencies.id'))
    total_amount = Column(Numeric(10, 2))
    disc_percentage = Column(Numeric(5, 2))
    disc_amount = Column(Numeric(10, 2))
    roundoff = Column(Numeric(10, 2))
    final_amount = Column(Numeric(10, 2))
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100))
    is_deleted = Column(Boolean, default=False)
    
    items = relationship("TestOrderItem", back_populates="order")

class TestOrderItem(Base):
    __tablename__ = 'test_order_items'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    test_order_id = Column(Integer, ForeignKey('test_orders.id'), nullable=False)
    test_id = Column(Integer, ForeignKey('tests.id'))
    test_name = Column(String(200))
    panel_id = Column(Integer, ForeignKey('test_panels.id'))
    panel_name = Column(String(200))
    rate = Column(Numeric(10, 2))
    gst = Column(Numeric(5, 2))
    cess = Column(Numeric(5, 2))
    disc_percentage = Column(Numeric(5, 2))
    disc_amount = Column(Numeric(10, 2))
    total_amount = Column(Numeric(10, 2))
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100))
    is_deleted = Column(Boolean, default=False)
    
    order = relationship("TestOrder", back_populates="items")

class TestResult(Base):
    __tablename__ = 'test_results'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    result_number = Column(Text, unique=True)
    test_order_id = Column(Integer, ForeignKey('test_orders.id'), nullable=False)
    result_date = Column(DateTime, default=datetime.utcnow)
    overall_report = Column(Text)
    performed_by = Column(Text)
    result_type = Column(Text)
    notes = Column(Text)
    doctor_id = Column(Integer, ForeignKey('doctors.id'))
    license_number = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100))
    is_deleted = Column(Boolean, default=False)
    
    details = relationship("TestResultDetail", back_populates="result")
    files = relationship("TestResultFile", back_populates="result")

class TestResultDetail(Base):
    __tablename__ = 'test_result_details'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    test_result_id = Column(Integer, ForeignKey('test_results.id'), nullable=False)
    parameter_id = Column(Text)
    parameter_name = Column(Text)
    unit = Column(Text)
    parameter_value = Column(Text)
    reference_value = Column(Text)
    verdict = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100))
    is_deleted = Column(Boolean, default=False)
    
    result = relationship("TestResult", back_populates="details")

class TestResultFile(Base):
    __tablename__ = 'test_result_files'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    test_result_id = Column(Integer, ForeignKey('test_results.id'), nullable=False)
    file_name = Column(Text)
    file_path = Column(Text)
    file_format = Column(Text)
    file_size = Column(BigInteger)
    acquisition_date = Column(DateTime)
    description = Column(Text)
    storage_system = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100))
    is_deleted = Column(Boolean, default=False)
    
    result = relationship("TestResult", back_populates="files")
