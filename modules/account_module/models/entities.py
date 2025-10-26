from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Numeric, UniqueConstraint, Date
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
    name = Column(String(200), nullable=False)
    code = Column(String(50), nullable=False)
    account_group_id = Column(Integer, ForeignKey('account_groups.id'), nullable=False)
    opening_balance = Column(Numeric(15, 2), default=0)
    current_balance = Column(Numeric(15, 2), default=0)
    is_active = Column(Boolean, default=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    
    account_group = relationship("AccountGroup", back_populates="accounts")
    journal_details = relationship("JournalDetail", back_populates="account")
    ledger_entries = relationship("Ledger", back_populates="account")
    
    __table_args__ = (
        UniqueConstraint('code', 'tenant_id', name='uq_account_master_code_tenant'),
    )

class VoucherType(Base):
    __tablename__ = 'voucher_types'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    code = Column(String(10), nullable=False)
    prefix = Column(String(10))
    is_active = Column(Boolean, default=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    
    vouchers = relationship("Voucher", back_populates="voucher_type")
    
    __table_args__ = (
        UniqueConstraint('code', 'tenant_id', name='uq_voucher_type_code_tenant'),
    )

class Voucher(Base):
    __tablename__ = 'vouchers'
    
    id = Column(Integer, primary_key=True)
    voucher_number = Column(String(50), unique=True, nullable=False)
    voucher_type_id = Column(Integer, ForeignKey('voucher_types.id'), nullable=False)
    voucher_date = Column(DateTime, nullable=False)
    reference_type = Column(String(20))  # SALES, PURCHASE, PAYMENT, RECEIPT
    reference_id = Column(Integer)  # SO/PO ID
    reference_number = Column(String(50))  # SO/PO Number
    narration = Column(Text)
    total_amount = Column(Numeric(15, 2), nullable=False)
    currency_id = Column(Integer, ForeignKey('currencies.id'))
    exchange_rate = Column(Numeric(15, 6), default=1)
    base_currency_amount = Column(Numeric(15, 2))
    reversed_voucher_id = Column(Integer, ForeignKey('vouchers.id'))
    reversal_voucher_id = Column(Integer, ForeignKey('vouchers.id'))
    is_reversal = Column(Boolean, default=False)
    is_posted = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    
    voucher_type = relationship("VoucherType", back_populates="vouchers")
    journals = relationship("Journal", back_populates="voucher")
    currency = relationship("Currency")
    reversed_voucher = relationship("Voucher", foreign_keys=[reversed_voucher_id], remote_side='Voucher.id')
    reversal_voucher = relationship("Voucher", foreign_keys=[reversal_voucher_id], remote_side='Voucher.id')

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

class Payment(Base):
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    payment_number = Column(String(50), unique=True, nullable=False)
    payment_date = Column(DateTime, nullable=False)
    payment_type = Column(String(20), nullable=False)  # CASH, BANK, CARD
    payment_mode = Column(String(20), nullable=False)  # RECEIVED, PAID
    reference_type = Column(String(20), nullable=False)  # SALES, PURCHASE
    reference_id = Column(Integer, nullable=False)
    reference_number = Column(String(50), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    account_id = Column(Integer, ForeignKey('account_masters.id'))  # Cash/Bank Account
    voucher_id = Column(Integer, ForeignKey('vouchers.id'))
    remarks = Column(Text)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    
    account = relationship("AccountMaster")
    voucher = relationship("Voucher")



class Currency(Base):
    __tablename__ = 'currencies'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(3), nullable=False, unique=True)
    name = Column(String(50), nullable=False)
    symbol = Column(String(5))
    is_base = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ExchangeRate(Base):
    __tablename__ = 'exchange_rates'
    
    id = Column(Integer, primary_key=True)
    from_currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    to_currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    rate = Column(Numeric(15, 6), nullable=False)
    effective_date = Column(Date, nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    from_currency = relationship("Currency", foreign_keys=[from_currency_id])
    to_currency = relationship("Currency", foreign_keys=[to_currency_id])
    
    __table_args__ = (
        UniqueConstraint('from_currency_id', 'to_currency_id', 'effective_date', 'tenant_id', name='uq_exchange_rate'),
    )

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