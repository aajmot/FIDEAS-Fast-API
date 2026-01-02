from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from datetime import datetime
from core.database.connection import Base

class Department(Base):
    __tablename__ = 'departments'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='SET NULL'))
    
    department_code = Column(String(50), nullable=False)
    department_name = Column(String(200), nullable=False)
    description = Column(Text)
    
    status = Column(String(20), default='ACTIVE')
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_deleted = Column(Boolean, default=False)
