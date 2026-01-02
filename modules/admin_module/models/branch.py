# modules/admin_module/models/branch.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.connection import Base

class Branch(Base):
    __tablename__ = 'branches'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    
    # Branch Info
    branch_code = Column(String(50), nullable=False)
    branch_name = Column(String(200), nullable=False)
    branch_type = Column(String(20), default='BRANCH')
    
    # Contact
    phone = Column(String(20))
    email = Column(String(100))
    contact_person = Column(String(100))
    
    # Address
    address_line1 = Column(String(200))
    address_line2 = Column(String(200))
    city = Column(String(100))
    state = Column(String(100))
    pincode = Column(String(20))
    country = Column(String(100), default='India')
    
    # Tax Registration
    gstin = Column(String(20))
    pan = Column(String(20))
    tan = Column(String(20))
    
    # Banking
    bank_account_id = Column(Integer, ForeignKey('bank_accounts.id', ondelete='SET NULL'))
    
    # Accounting
    cost_center_id = Column(Integer)
    profit_center_id = Column(Integer)
    
    # Manager
    manager_id = Column(Integer)
    manager_name = Column(String(100))
    
    # Status
    is_default = Column(Boolean, default=False)
    status = Column(String(20), default='ACTIVE')
    remarks = Column(Text)
    tags = Column(ARRAY(Text))
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    tenant = relationship("Tenant")
