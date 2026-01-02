from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Date
from datetime import datetime
from core.database.connection import Base

class Employee(Base):
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='SET NULL'))
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='SET NULL'))
    
    employee_code = Column(String(50), nullable=False)
    employee_name = Column(String(200), nullable=False)
    employee_type = Column(String(50), nullable=False)
    
    phone = Column(String(20))
    email = Column(String(100))
    
    qualification = Column(String(100))
    specialization = Column(String(100))
    license_number = Column(String(50))
    license_expiry = Column(Date)
    
    employment_type = Column(String(20), default='INTERNAL')
    status = Column(String(20), default='ACTIVE')
    remarks = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
