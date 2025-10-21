from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.connection import Base

class TestCategory(Base):
    __tablename__ = 'test_categories'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100))
    is_deleted = Column(Boolean, default=False)
    
    tests = relationship("Test", back_populates="category")

class Test(Base):
    __tablename__ = 'tests'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    name = Column(String(200), nullable=False)
    category_id = Column(Integer, ForeignKey('test_categories.id'))
    body_part = Column(String(100))
    description = Column(Text)
    typical_duration = Column(String(50))
    preparation_instruction = Column(Text)
    rate = Column(Numeric(10, 2))
    hsn_code = Column(String(20))
    gst = Column(Numeric(5, 2))
    cess = Column(Numeric(5, 2))
    commission_type = Column(Text)
    commission_value = Column(Numeric(10, 2))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100))
    is_deleted = Column(Boolean, default=False)
    
    category = relationship("TestCategory", back_populates="tests")
    parameters = relationship("TestParameter", back_populates="test")

class TestParameter(Base):
    __tablename__ = 'test_parameters'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    test_id = Column(Integer, ForeignKey('tests.id'), nullable=False)
    name = Column(String(200), nullable=False)
    unit = Column(String(50))
    normal_range = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100))
    is_deleted = Column(Boolean, default=False)
    
    test = relationship("Test", back_populates="parameters")
