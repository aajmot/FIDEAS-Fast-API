from sqlalchemy import Column, Integer, String, ForeignKey, Text, Numeric, DateTime, Boolean
from app.db.models.base_model import BaseModel

class Journal(BaseModel):
    __tablename__ = 'journals'
    
    voucher_id = Column(Integer, nullable=False)
    journal_date = Column(DateTime, nullable=False)
    total_debit = Column(Numeric(15, 2), nullable=False)
    total_credit = Column(Numeric(15, 2), nullable=False)
    is_balanced = Column(Boolean, default=True)
    tenant_id = Column(Integer, nullable=False)

class JournalDetail(BaseModel):
    __tablename__ = 'journal_details'
    
    journal_id = Column(Integer, nullable=False)
    account_id = Column(Integer, nullable=False)
    debit_amount = Column(Numeric(15, 2), default=0)
    credit_amount = Column(Numeric(15, 2), default=0)
    tax_id = Column(Integer)
    taxable_amount = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    cost_center_id = Column(Integer)
    narration = Column(Text)
    tenant_id = Column(Integer, nullable=False)

class Ledger(BaseModel):
    __tablename__ = 'ledgers'
    
    account_id = Column(Integer, nullable=False)
    voucher_id = Column(Integer, nullable=False)
    transaction_date = Column(DateTime, nullable=False)
    debit_amount = Column(Numeric(15, 2), default=0)
    credit_amount = Column(Numeric(15, 2), default=0)
    balance = Column(Numeric(15, 2), default=0)
    narration = Column(Text)
    tenant_id = Column(Integer, nullable=False)