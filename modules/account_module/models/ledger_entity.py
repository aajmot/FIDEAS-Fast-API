from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Numeric, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from modules.inventory_module.models.entities import Base

class Ledger(Base):
    __tablename__ = 'ledgers'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    account_id = Column(Integer, ForeignKey('account_masters.id', ondelete='RESTRICT'), nullable=False)
    voucher_id = Column(Integer, ForeignKey('vouchers.id', ondelete='CASCADE'), nullable=False)
    voucher_line_id = Column(Integer, ForeignKey('voucher_lines.id', ondelete='CASCADE'))
    
    transaction_date = Column(DateTime, nullable=False)
    posting_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Base Currency Amounts
    debit_amount = Column(Numeric(15, 4), default=0)
    credit_amount = Column(Numeric(15, 4), default=0)
    
    # Foreign Currency Support
    currency_id = Column(Integer, ForeignKey('currencies.id', ondelete='RESTRICT'))
    exchange_rate = Column(Numeric(15, 6), default=1)
    debit_foreign = Column(Numeric(15, 4))
    credit_foreign = Column(Numeric(15, 4))
    
    # Running Balance
    balance = Column(Numeric(15, 4))
    
    # Reference to Source Transaction
    reference_type = Column(String(30))
    reference_id = Column(Integer)
    reference_number = Column(String(50))
    
    narration = Column(Text)
    
    # Reconciliation
    is_reconciled = Column(Boolean, default=False)
    reconciliation_date = Column(DateTime)
    reconciliation_ref = Column(String(50))
    
    # Posting Control
    is_posted = Column(Boolean, default=True)
    is_reversal = Column(Boolean, default=False)
    reversed_ledger_id = Column(Integer, ForeignKey('ledgers.id', ondelete='SET NULL'))
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    account = relationship("AccountMaster", back_populates="ledger_entries")
    voucher = relationship("Voucher")
    voucher_line = relationship("VoucherLine")
    currency = relationship("Currency")
    reversed_ledger = relationship("Ledger", remote_side=[id], foreign_keys=[reversed_ledger_id])
    
    __table_args__ = (
        CheckConstraint(
            "(debit_amount > 0 AND credit_amount = 0) OR (credit_amount > 0 AND debit_amount = 0) OR (debit_amount = 0 AND credit_amount = 0)",
            name='chk_debit_credit_exclusive'
        ),
        CheckConstraint(
            "(currency_id IS NULL AND exchange_rate = 1 AND debit_foreign IS NULL AND credit_foreign IS NULL) OR (currency_id IS NOT NULL AND exchange_rate > 0)",
            name='chk_foreign_currency_logic'
        ),
        CheckConstraint("debit_amount >= 0", name='chk_debit_positive'),
        CheckConstraint("credit_amount >= 0", name='chk_credit_positive'),
    )
