from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Numeric, Date, CheckConstraint, UniqueConstraint, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.connection import Base

# Import to ensure bank_accounts table is available
try:
    from .bank_account_entity import BankAccount
except ImportError:
    pass  # BankAccount model not available


class Payment(Base):
    """Payments - records receipts, payments and contra entries"""
    __tablename__ = 'payments'
    __table_args__ = (
        UniqueConstraint('payment_number', 'tenant_id', name='uq_payment_number_tenant'),
        CheckConstraint("payment_type IN ('RECEIPT', 'PAYMENT', 'CONTRA')", name='chk_payment_type'),
        CheckConstraint("party_type IN ('CUSTOMER','SUPPLIER','EMPLOYEE','BANK','OTHER')", name='chk_party_type'),
        CheckConstraint(
            "(foreign_currency_id IS NULL AND total_amount_foreign IS NULL AND exchange_rate = 1) "
            "OR (foreign_currency_id IS NOT NULL AND exchange_rate > 0)",
            name='chk_currency_logic'
        ),
        CheckConstraint('total_amount_base >= 0', name='chk_positive_amount'),
        CheckConstraint("status IN ('DRAFT','POSTED','CANCELLED','RECONCILED')", name='chk_status'),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    
    # Payment identification
    payment_number = Column(String(50), nullable=False)
    payment_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Direction
    payment_type = Column(String(20), nullable=False)  # RECEIPT, PAYMENT, CONTRA
    
    # Party
    party_type = Column(String(20), nullable=False)  # CUSTOMER, SUPPLIER, EMPLOYEE, BANK, OTHER
    party_id = Column(Integer)  # FK to customers/suppliers/employees
    
    # Currency
    base_currency_id = Column(Integer, ForeignKey('currencies.id', ondelete='RESTRICT'), nullable=False)
    foreign_currency_id = Column(Integer, ForeignKey('currencies.id', ondelete='SET NULL'))
    exchange_rate = Column(Numeric(15, 6), default=1)
    
    # Amounts
    total_amount_base = Column(Numeric(15, 4), nullable=False, default=0)
    total_amount_foreign = Column(Numeric(15, 4))
    
    # TDS / Advance
    tds_amount_base = Column(Numeric(15, 4), default=0)
    advance_amount_base = Column(Numeric(15, 4), default=0)
    
    # Status
    status = Column(String(20), nullable=False, default='DRAFT')
    
    # Accounting
    voucher_id = Column(Integer, ForeignKey('vouchers.id', ondelete='SET NULL'))
    
    # Metadata
    reference_number = Column(String(50))  # Bank ref, UTR
    remarks = Column(Text)
    tags = Column(ARRAY(Text))
    
    # Reconciliation
    is_reconciled = Column(Boolean, default=False)
    reconciled_at = Column(DateTime)
    reconciled_by = Column(String(100))
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    base_currency = relationship("Currency", foreign_keys=[base_currency_id])
    foreign_currency = relationship("Currency", foreign_keys=[foreign_currency_id])
    voucher = relationship("Voucher")
    payment_details = relationship("PaymentDetail", back_populates="payment", cascade="all, delete-orphan")


class PaymentDetail(Base):
    """Payment Details - line items for each payment"""
    __tablename__ = 'payment_details'
    __table_args__ = (
        UniqueConstraint('payment_id', 'line_no', name='uq_payment_detail_line'),
        CheckConstraint('amount_base > 0', name='chk_amount_positive'),
        CheckConstraint(
            "payment_mode IN ('CASH','BANK','CARD','UPI','CHEQUE','ONLINE','WALLET')",
            name='chk_payment_mode'
        ),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    payment_id = Column(Integer, ForeignKey('payments.id', ondelete='CASCADE'), nullable=False)
    line_no = Column(Integer, nullable=False)
    
    # Payment mode
    payment_mode = Column(String(20), nullable=False)  # CASH, BANK, CARD, UPI, CHEQUE, ONLINE, WALLET
    
    # Bank / Instrument
    bank_account_id = Column(Integer, ForeignKey('bank_accounts.id', ondelete='SET NULL'))
    instrument_number = Column(String(50))
    instrument_date = Column(Date)
    bank_name = Column(String(100))
    branch_name = Column(String(100))
    ifsc_code = Column(String(20))
    transaction_reference = Column(String(100))  # UPI ID, NEFT ref
    
    # Amounts
    amount_base = Column(Numeric(15, 4), nullable=False)
    amount_foreign = Column(Numeric(15, 4))
    
    # Account (Dr/Cr) - auto-determined if not provided
    account_id = Column(Integer, ForeignKey('account_masters.id', ondelete='RESTRICT'), nullable=True)
    
    description = Column(Text)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    payment = relationship("Payment", back_populates="payment_details")
    account = relationship("AccountMaster", foreign_keys=[account_id])
