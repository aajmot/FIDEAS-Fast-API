from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Numeric, Date, CheckConstraint, UniqueConstraint, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.connection import Base

try:
    from .bank_account_entity import BankAccount
except ImportError:
    pass


class Payment(Base):
    """Payments - records receipts, payments and contra entries"""
    __tablename__ = 'payments'
    __table_args__ = (
        UniqueConstraint('payment_number', 'tenant_id', name='uq_payment_number_tenant'),
        CheckConstraint("payment_type IN ('RECEIPT', 'PAYMENT', 'CONTRA')", name='chk_payment_type'),
        CheckConstraint("party_type IN ('CUSTOMER','SUPPLIER','EMPLOYEE','BANK','PATIENT','OTHER')", name='chk_party_type'),
        CheckConstraint(
            "(foreign_currency_id IS NULL AND total_amount_foreign IS NULL AND exchange_rate = 1) "
            "OR (foreign_currency_id IS NOT NULL AND exchange_rate > 0)",
            name='chk_currency_logic'
        ),
        CheckConstraint('total_amount_base >= 0', name='chk_positive_amount'),
        CheckConstraint('allocated_amount_base + unallocated_amount_base <= total_amount_base', name='chk_allocation_logic'),
        CheckConstraint("status IN ('DRAFT','POSTED','CANCELLED','RECONCILED')", name='chk_status'),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='SET NULL'))
    
    payment_number = Column(String(50), nullable=False)
    payment_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    payment_type = Column(String(20), nullable=False)
    party_type = Column(String(20), nullable=False)
    party_id = Column(Integer)
    
    source_document_type = Column(String(20))
    source_document_id = Column(Integer)
    
    base_currency_id = Column(Integer, ForeignKey('currencies.id', ondelete='RESTRICT'), nullable=False)
    foreign_currency_id = Column(Integer, ForeignKey('currencies.id', ondelete='SET NULL'))
    exchange_rate = Column(Numeric(15, 6), default=1)
    
    total_amount_base = Column(Numeric(15, 4), nullable=False, default=0)
    total_amount_foreign = Column(Numeric(15, 4))
    
    allocated_amount_base = Column(Numeric(15, 4), default=0)
    unallocated_amount_base = Column(Numeric(15, 4), default=0)
    
    tds_amount_base = Column(Numeric(15, 4), default=0)
    advance_amount_base = Column(Numeric(15, 4), default=0)
    
    is_refund = Column(Boolean, default=False)
    original_payment_id = Column(Integer, ForeignKey('payments.id', ondelete='SET NULL'))
    
    status = Column(String(20), nullable=False, default='DRAFT')
    voucher_id = Column(Integer, ForeignKey('vouchers.id', ondelete='SET NULL'))
    
    reference_number = Column(String(50))
    remarks = Column(Text)
    tags = Column(ARRAY(Text))
    
    is_reconciled = Column(Boolean, default=False)
    reconciled_at = Column(DateTime)
    reconciled_by = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    base_currency = relationship("Currency", foreign_keys=[base_currency_id])
    foreign_currency = relationship("Currency", foreign_keys=[foreign_currency_id])
    voucher = relationship("Voucher")
    payment_details = relationship("PaymentDetail", back_populates="payment", cascade="all, delete-orphan")
    payment_allocations = relationship("PaymentAllocation", back_populates="payment", cascade="all, delete-orphan")


class PaymentDetail(Base):
    """Payment Details - line items for each payment"""
    __tablename__ = 'payment_details'
    __table_args__ = (
        UniqueConstraint('payment_id', 'line_no', name='uq_payment_detail_line'),
        CheckConstraint('amount_base > 0', name='chk_amount_positive'),
        CheckConstraint(
            "payment_mode IN ('CASH','BANK','CARD','UPI','CHEQUE','ONLINE','WALLET','NEFT','RTGS','IMPS')",
            name='chk_payment_mode'
        ),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='SET NULL'))
    payment_id = Column(Integer, ForeignKey('payments.id', ondelete='CASCADE'), nullable=False)
    line_no = Column(Integer, nullable=False)
    
    payment_mode = Column(String(20), nullable=False)
    
    bank_account_id = Column(Integer, ForeignKey('bank_accounts.id', ondelete='SET NULL'))
    instrument_number = Column(String(50))
    instrument_date = Column(Date)
    bank_name = Column(String(100))
    branch_name = Column(String(100))
    ifsc_code = Column(String(20))
    transaction_reference = Column(String(100))
    
    # Payment Gateway (per line item)
    payment_gateway = Column(String(50))
    gateway_transaction_id = Column(String(100))
    gateway_status = Column(String(20))
    gateway_fee_base = Column(Numeric(15, 4), default=0)
    gateway_response = Column(JSONB)
    
    amount_base = Column(Numeric(15, 4), nullable=False)
    amount_foreign = Column(Numeric(15, 4))
    
    account_id = Column(Integer, ForeignKey('account_masters.id', ondelete='RESTRICT'))
    description = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_deleted = Column(Boolean, default=False)
    
    payment = relationship("Payment", back_populates="payment_details")
    account = relationship("AccountMaster", foreign_keys=[account_id])


class PaymentAllocation(Base):
    """Payment Allocations - tracks which invoices/orders a payment is applied to"""
    __tablename__ = 'payment_allocations'
    __table_args__ = (
        UniqueConstraint('payment_id', 'document_type', 'document_id', name='uq_payment_allocation'),
        CheckConstraint('allocated_amount_base > 0', name='chk_allocated_positive'),
        CheckConstraint(
            "document_type IN ('ORDER','INVOICE','EXPENSE','BILL','ADVANCE','DEBIT_NOTE','CREDIT_NOTE')",
            name='chk_document_type'
        ),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='SET NULL'))
    payment_id = Column(Integer, ForeignKey('payments.id', ondelete='CASCADE'), nullable=False)
    
    document_type = Column(String(20), nullable=False)
    document_id = Column(Integer, nullable=False)
    document_number = Column(String(50))
    
    allocated_amount_base = Column(Numeric(15, 4), nullable=False)
    allocated_amount_foreign = Column(Numeric(15, 4))
    
    discount_amount_base = Column(Numeric(15, 4), default=0)
    adjustment_amount_base = Column(Numeric(15, 4), default=0)
    
    allocation_date = Column(DateTime, default=datetime.utcnow)
    remarks = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_deleted = Column(Boolean, default=False)
    
    payment = relationship("Payment", back_populates="payment_allocations")
