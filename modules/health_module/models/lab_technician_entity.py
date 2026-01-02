from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Date
from datetime import datetime
from core.database.connection import Base

class LabTechnician(Base):
    __tablename__ = 'lab_technicians'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    technician_code = Column(String(50), nullable=False)
    technician_name = Column(String(200), nullable=False)
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
