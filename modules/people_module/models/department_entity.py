from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, CheckConstraint, UniqueConstraint
from datetime import datetime
from core.database.connection import Base

class Department(Base):
    __tablename__ = 'departments'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='SET NULL'))
    
    department_code = Column(String(50), nullable=False)
    department_name = Column(String(200), nullable=False)
    parent_department_id = Column(Integer, ForeignKey('departments.id', ondelete='SET NULL'))
    
    description = Column(Text)
    
    default_cost_center_id = Column(Integer, ForeignKey('cost_centers.id'))
    org_unit_type = Column(String(20), default='DIVISION', nullable=False)
    
    status = Column(String(20), default='ACTIVE', nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_deleted = Column(Boolean, default=False)
    
    __table_args__ = (
        UniqueConstraint('department_code', 'tenant_id', name='uq_department_code_tenant'),
        CheckConstraint("org_unit_type IN ('DIVISION','DEPARTMENT','TEAM')", name='chk_org_unit_type'),
        CheckConstraint("status IN ('ACTIVE','INACTIVE')", name='chk_status'),
    )
