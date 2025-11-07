from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Numeric, UniqueConstraint, Date, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from modules.inventory_module.models.entities import Base

class AccountGroup(Base):
    __tablename__ = 'account_groups'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=False)
    parent_id = Column(Integer, ForeignKey('account_groups.id'))
    account_type = Column(String(20), nullable=False)  # ASSET, LIABILITY, EQUITY, INCOME, EXPENSE
    is_active = Column(Boolean, default=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    parent = relationship("AccountGroup", remote_side=[id])
    children = relationship("AccountGroup", overlaps="parent")
    accounts = relationship("AccountMaster", back_populates="account_group")
    
    __table_args__ = (
        UniqueConstraint('code', 'tenant_id', name='uq_account_group_code_tenant'),
    )

class AccountMaster(Base):
    __tablename__ = 'account_masters'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    parent_id = Column(Integer, ForeignKey('account_masters.id', ondelete='SET NULL'))
    account_group_id = Column(Integer, ForeignKey('account_groups.id', ondelete='RESTRICT'), nullable=False)
    
    # Core
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Account Type
    account_type = Column(String(20), nullable=False)  # ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE
    normal_balance = Column(String(1), nullable=False, default='D')  # D or C
    
    # System Account
    is_system_account = Column(Boolean, default=False)
    system_code = Column(String(50))
    
    # Hierarchy
    level = Column(Integer, nullable=False, default=1)
    path = Column(Text)
    
    # Balances
    opening_balance = Column(Numeric(15, 4), default=0)
    current_balance = Column(Numeric(15, 4), default=0)
    is_reconciled = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    
    # Relationships
    parent = relationship("AccountMaster", remote_side=[id], foreign_keys=[parent_id])
    children = relationship("AccountMaster", back_populates="parent", foreign_keys=[parent_id])
    account_group = relationship("AccountGroup", back_populates="accounts")
    journal_details = relationship("JournalDetail", back_populates="account")
    ledger_entries = relationship("Ledger", back_populates="account")
    
    __table_args__ = (
        UniqueConstraint('code', 'tenant_id', name='uq_account_code_tenant'),
        CheckConstraint("account_type IN ('ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE')", name='chk_account_type'),
        CheckConstraint("normal_balance IN ('D', 'C')", name='chk_normal_balance'),
        CheckConstraint("level >= 1", name='chk_level_positive'),
        CheckConstraint("parent_id IS NULL OR parent_id != id", name='chk_parent_not_self'),
    )

class VoucherType(Base):
    __tablename__ = 'voucher_types'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    code = Column(String(50), nullable=False)
    prefix = Column(String(50))
    allow_multi_currency = Column(Boolean, default=True)
    allow_tax = Column(Boolean, default=True)
    allow_commission = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_deleted = Column(Boolean, default=False)
    
    vouchers = relationship("Voucher", back_populates="voucher_type")
    
    __table_args__ = (
        UniqueConstraint('code', 'tenant_id', name='uq_voucher_type_code_tenant'),
    )

class Voucher(Base):
    __tablename__ = 'vouchers'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    
    voucher_number = Column(String(50), nullable=False)
    voucher_type_id = Column(Integer, ForeignKey('voucher_types.id'), nullable=False)
    voucher_date = Column(DateTime, nullable=False)
    
    # Currency
    base_currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    foreign_currency_id = Column(Integer, ForeignKey('currencies.id'))
    exchange_rate = Column(Numeric(15, 4), default=1)
    
    # Base Currency Totals (Always Required)
    base_total_amount = Column(Numeric(15, 4), nullable=False, default=0)
    base_total_debit = Column(Numeric(15, 4), nullable=False, default=0)
    base_total_credit = Column(Numeric(15, 4), nullable=False, default=0)
    
    # Foreign Currency Totals (Optional)
    foreign_total_amount = Column(Numeric(15, 4))
    foreign_total_debit = Column(Numeric(15, 4))
    foreign_total_credit = Column(Numeric(15, 4))
    
    # References
    reference_type = Column(String(20))
    reference_id = Column(Integer)
    reference_number = Column(String(50))
    
    narration = Column(Text)
    
    # Posting & Reversal
    is_posted = Column(Boolean, default=True)
    reversed_voucher_id = Column(Integer, ForeignKey('vouchers.id'))
    reversal_voucher_id = Column(Integer, ForeignKey('vouchers.id'))
    is_reversal = Column(Boolean, default=False)
    
    # Approval
    approval_status = Column(String(20))
    approval_request_id = Column(Integer)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Text, default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(Text, default='system')
    is_deleted = Column(Boolean, default=False)
    
    __table_args__ = (
        UniqueConstraint('voucher_number', 'tenant_id', name='uq_voucher_number_tenant'),
    )
    
    voucher_type = relationship("VoucherType", back_populates="vouchers")
    journals = relationship("Journal", back_populates="voucher")
    voucher_lines = relationship("VoucherLine", back_populates="voucher")
    base_currency = relationship("Currency", foreign_keys=[base_currency_id])
    foreign_currency = relationship("Currency", foreign_keys=[foreign_currency_id])
    reversed_voucher = relationship("Voucher", foreign_keys=[reversed_voucher_id], remote_side='Voucher.id')
    reversal_voucher = relationship("Voucher", foreign_keys=[reversal_voucher_id], remote_side='Voucher.id')


class VoucherLine(Base):
    __tablename__ = 'voucher_lines'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    
    voucher_id = Column(Integer, ForeignKey('vouchers.id', ondelete='CASCADE'), nullable=False)
    line_no = Column(Integer, nullable=False)
    
    account_id = Column(Integer, ForeignKey('account_masters.id'), nullable=False)
    description = Column(Text)
    
    # Base Currency Amounts
    debit_base = Column(Numeric(15, 4), default=0)
    credit_base = Column(Numeric(15, 4), default=0)
    
    # Foreign Currency Amounts
    debit_foreign = Column(Numeric(15, 4))
    credit_foreign = Column(Numeric(15, 4))
    
    # Tax
    tax_id = Column(Integer, ForeignKey('tax_masters.id'))
    tax_amount_base = Column(Numeric(15, 4), default=0)
    tax_amount_foreign = Column(Numeric(15, 4))
    
    # Commission
    commission_id = Column(Integer)  # References commissions table (not created yet)
    commission_base = Column(Numeric(15, 4), default=0)
    commission_foreign = Column(Numeric(15, 4))
    
    # Line Reference
    reference_type = Column(String(30))
    reference_id = Column(Integer)
    reference_line_no = Column(Integer)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_deleted = Column(Boolean, default=False)
    
    __table_args__ = (
        UniqueConstraint('voucher_id', 'line_no', 'tenant_id', name='uq_voucher_line_tenant'),
    )
    
    voucher = relationship("Voucher", back_populates="voucher_lines")
    account = relationship("AccountMaster")
    tax = relationship("TaxMaster")

class Journal(Base):
    __tablename__ = 'journals'
    
    id = Column(Integer, primary_key=True)
    voucher_id = Column(Integer, ForeignKey('vouchers.id'), nullable=False)
    journal_date = Column(DateTime, nullable=False)
    total_debit = Column(Numeric(15, 2), nullable=False)
    total_credit = Column(Numeric(15, 2), nullable=False)
    is_balanced = Column(Boolean, default=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    voucher = relationship("Voucher", back_populates="journals")
    journal_details = relationship("JournalDetail", back_populates="journal")

class JournalDetail(Base):
    __tablename__ = 'journal_details'
    
    id = Column(Integer, primary_key=True)
    journal_id = Column(Integer, ForeignKey('journals.id'), nullable=False)
    account_id = Column(Integer, ForeignKey('account_masters.id'), nullable=False)
    debit_amount = Column(Numeric(15, 2), default=0)
    credit_amount = Column(Numeric(15, 2), default=0)
    tax_id = Column(Integer, ForeignKey('tax_masters.id'))
    taxable_amount = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    cost_center_id = Column(Integer, ForeignKey('cost_centers.id'))
    narration = Column(Text)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    
    journal = relationship("Journal", back_populates="journal_details")
    account = relationship("AccountMaster", back_populates="journal_details")
    tax = relationship("TaxMaster")
    cost_center = relationship("CostCenter")

class Ledger(Base):
    __tablename__ = 'ledgers'
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('account_masters.id'), nullable=False)
    voucher_id = Column(Integer, ForeignKey('vouchers.id'), nullable=False)
    transaction_date = Column(DateTime, nullable=False)
    debit_amount = Column(Numeric(15, 2), default=0)
    credit_amount = Column(Numeric(15, 2), default=0)
    balance = Column(Numeric(15, 2), default=0)
    narration = Column(Text)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    account = relationship("AccountMaster", back_populates="ledger_entries")
    voucher = relationship("Voucher")

# Import Payment and PaymentDetail classes
from .payment_entity import Payment, PaymentDetail

class TaxMaster(Base):
    __tablename__ = 'tax_masters'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    tax_type = Column(String(20), nullable=False)  # GST, VAT, SALES_TAX
    rate = Column(Numeric(5, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('name', 'tenant_id', name='uq_tax_master_name_tenant'),
    )

class BankReconciliation(Base):
    __tablename__ = 'bank_reconciliations'
    
    id = Column(Integer, primary_key=True)
    bank_account_id = Column(Integer, ForeignKey('account_masters.id'), nullable=False)
    statement_date = Column(Date, nullable=False)
    statement_balance = Column(Numeric(15, 2), nullable=False)
    book_balance = Column(Numeric(15, 2), nullable=False)
    reconciled_balance = Column(Numeric(15, 2), default=0)
    status = Column(String(20), default='DRAFT')  # DRAFT, RECONCILED
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    
    bank_account = relationship("AccountMaster")
    items = relationship("BankReconciliationItem", back_populates="reconciliation")

class BankReconciliationItem(Base):
    __tablename__ = 'bank_reconciliation_items'
    
    id = Column(Integer, primary_key=True)
    reconciliation_id = Column(Integer, ForeignKey('bank_reconciliations.id'), nullable=False)
    ledger_id = Column(Integer, ForeignKey('ledgers.id'))
    statement_amount = Column(Numeric(15, 2), nullable=False)
    statement_date = Column(Date, nullable=False)
    statement_reference = Column(String(100))
    is_matched = Column(Boolean, default=False)
    match_type = Column(String(20))  # AUTO, MANUAL
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    
    reconciliation = relationship("BankReconciliation", back_populates="items")
    ledger = relationship("Ledger")

class CostCenter(Base):
    __tablename__ = 'cost_centers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=False)
    parent_id = Column(Integer, ForeignKey('cost_centers.id'))
    is_active = Column(Boolean, default=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    parent = relationship("CostCenter", remote_side=[id])
    children = relationship("CostCenter", overlaps="parent")
    
    __table_args__ = (
        UniqueConstraint('code', 'tenant_id', name='uq_cost_center_code_tenant'),
    )

class Budget(Base):
    __tablename__ = 'budgets'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    fiscal_year_id = Column(Integer, ForeignKey('financial_years.id'), nullable=False)
    account_id = Column(Integer, ForeignKey('account_masters.id'), nullable=False)
    cost_center_id = Column(Integer, ForeignKey('cost_centers.id'))
    budget_amount = Column(Numeric(15, 2), nullable=False)
    actual_amount = Column(Numeric(15, 2), default=0)
    variance = Column(Numeric(15, 2), default=0)
    status = Column(String(20), default='DRAFT')  # DRAFT, APPROVED, CLOSED
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    
    # fiscal_year relationship removed - import from admin module if needed
    account = relationship("AccountMaster")
    cost_center = relationship("CostCenter")
    
    __table_args__ = (
        UniqueConstraint('fiscal_year_id', 'account_id', 'cost_center_id', 'tenant_id', name='uq_budget'),
    )

class Integration(Base):
    __tablename__ = 'integrations'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    integration_type = Column(String(50), nullable=False)  # PAYMENT_GATEWAY, ERP, CRM, BANK
    provider = Column(String(50), nullable=False)
    api_key = Column(String(255))
    api_secret = Column(String(255))
    webhook_url = Column(String(255))
    config = Column(Text)  # JSON config
    is_active = Column(Boolean, default=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('integration_type', 'provider', 'tenant_id', name='uq_integration'),
    )

# Import PaymentTerm for backward compatibility
from .payment_term_entity import PaymentTerm