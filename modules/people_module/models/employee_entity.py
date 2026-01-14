from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Date, Numeric, CheckConstraint, UniqueConstraint
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
    employee_type = Column(String(50), nullable=False, default='OTHERS')
    
    phone = Column(String(20))
    email = Column(String(100))
    
    qualification = Column(String(100))
    specialization = Column(String(100))
    license_number = Column(String(50))
    license_expiry = Column(Date)
    
    employment_type = Column(String(20), default='INTERNAL', nullable=False)
    status = Column(String(20), default='ACTIVE', nullable=False)
    remarks = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    __table_args__ = (
        UniqueConstraint('employee_code', 'tenant_id', name='uq_employee_code_tenant'),
        CheckConstraint("employee_type IN ('LAB_TECHNICIAN','DOCTOR','NURSE','ADMIN','OTHERS')", name='chk_employee_type'),
        CheckConstraint("employment_type IN ('INTERNAL','EXTERNAL','CONTRACT')", name='chk_employment_type'),
        CheckConstraint("status IN ('ACTIVE','INACTIVE','SUSPENDED')", name='chk_employee_status'),
    )

class EmployeeCostAllocation(Base):
    __tablename__ = 'employee_cost_allocations'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='SET NULL'))
    
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    cost_center_id = Column(Integer, ForeignKey('cost_centers.id'), nullable=False)
    percentage = Column(Numeric(5, 2), nullable=False)
    effective_start_date = Column(Date, nullable=False)
    effective_end_date = Column(Date)
    
    status = Column(String(20), default='ACTIVE', nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE','INACTIVE')", name='chk_allocation_status'),
        CheckConstraint("percentage <= 100", name='total_pct_check_employee_cost_allocations'),
    )
