from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.models.base_model import BaseModel

class AccountGroup(BaseModel):
    __tablename__ = 'account_groups'
    
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=False)
    parent_id = Column(Integer, ForeignKey('account_groups.id'))
    account_type = Column(String(20), nullable=False)
    tenant_id = Column(Integer, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('code', 'tenant_id', name='uq_account_group_code_tenant'),
    )

class AccountMaster(BaseModel):
    __tablename__ = 'account_masters'
    
    name = Column(String(200), nullable=False)
    code = Column(String(50), nullable=False)
    account_group_id = Column(Integer, nullable=False)
    opening_balance = Column(Numeric(15, 2), default=0)
    current_balance = Column(Numeric(15, 2), default=0)
    tenant_id = Column(Integer, nullable=False)
    created_by = Column(String(100))
    
    __table_args__ = (
        UniqueConstraint('code', 'tenant_id', name='uq_account_master_code_tenant'),
    )