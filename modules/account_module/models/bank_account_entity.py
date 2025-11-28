from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, Date, ForeignKey
from datetime import datetime
from core.database.connection import Base

class BankAccount(Base):
    __tablename__ = 'bank_accounts'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    account_number = Column(String(50), nullable=False)
    account_name = Column(String(100), nullable=False)
    bank_name = Column(String(100), nullable=False)
    branch_name = Column(String(100))
    ifsc_code = Column(String(20))
    swift_code = Column(String(20))
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    opening_balance = Column(Numeric(15,4), default=0)
    opening_date = Column(Date)
    account_id = Column(Integer, ForeignKey('account_masters.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_deleted = Column(Boolean, default=False)