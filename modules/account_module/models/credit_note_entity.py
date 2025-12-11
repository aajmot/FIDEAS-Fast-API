from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Numeric, Date, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime
from modules.inventory_module.models.entities import Base


class CreditNote(Base):
    __tablename__ = 'credit_notes'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    
    note_number = Column(String(50), nullable=False)
    reference_number = Column(String(50))
    
    note_date = Column(Date, nullable=False)
    due_date = Column(Date)
    
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='RESTRICT'), nullable=False)
    original_invoice_id = Column(Integer, ForeignKey('sales_invoices.id', ondelete='SET NULL'))
    original_invoice_number = Column(String(50))
    
    # Currency
    base_currency_id = Column(Integer, ForeignKey('currencies.id', ondelete='RESTRICT'), nullable=False)
    foreign_currency_id = Column(Integer, ForeignKey('currencies.id', ondelete='SET NULL'))
    exchange_rate = Column(Numeric(15, 6), default=1)
    
    # GST Summary
    cgst_amount_base = Column(Numeric(15, 4), default=0)
    sgst_amount_base = Column(Numeric(15, 4), default=0)
    igst_amount_base = Column(Numeric(15, 4), default=0)
    cess_amount_base = Column(Numeric(15, 4), default=0)
    
    # Totals (Base)
    subtotal_base = Column(Numeric(15, 4), default=0)
    discount_amount_base = Column(Numeric(15, 4), default=0)
    tax_amount_base = Column(Numeric(15, 4), default=0)
    total_amount_base = Column(Numeric(15, 4), nullable=False, default=0)
    
    # Totals (Foreign)
    subtotal_foreign = Column(Numeric(15, 4))
    discount_amount_foreign = Column(Numeric(15, 4))
    tax_amount_foreign = Column(Numeric(15, 4))
    total_amount_foreign = Column(Numeric(15, 4))
    
    # Status
    status = Column(String(20), nullable=False, default='DRAFT')
    credit_note_type = Column(String(20), nullable=False, default='SALES_RETURN')
    
    # Accounting
    voucher_id = Column(Integer, ForeignKey('vouchers.id', ondelete='SET NULL'))
    
    # Metadata
    reason = Column(Text, nullable=False)
    notes = Column(Text)
    tags = Column(ARRAY(Text))
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    customer = relationship("Customer")
    original_invoice = relationship("SalesInvoice")
    base_currency = relationship("Currency", foreign_keys=[base_currency_id])
    foreign_currency = relationship("Currency", foreign_keys=[foreign_currency_id])
    voucher = relationship("Voucher")
    items = relationship("CreditNoteItem", back_populates="credit_note")
    
    __table_args__ = (
        UniqueConstraint('note_number', 'tenant_id', name='uq_credit_note_number_tenant'),
        CheckConstraint("status IN ('DRAFT','POSTED','APPLIED','CANCELLED')", name='chk_credit_note_status'),
        CheckConstraint("credit_note_type IN ('SALES_RETURN','PRICE_ADJUSTMENT','DISCOUNT','OTHER')", name='chk_credit_note_type'),
        CheckConstraint("due_date IS NULL OR due_date >= note_date", name='chk_credit_note_due_date'),
        CheckConstraint("total_amount_base >= 0", name='chk_credit_note_total_positive'),
    )


class CreditNoteItem(Base):
    __tablename__ = 'credit_note_items'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    
    credit_note_id = Column(Integer, ForeignKey('credit_notes.id', ondelete='CASCADE'), nullable=False)
    line_no = Column(Integer, nullable=False)
    
    product_id = Column(Integer, ForeignKey('products.id', ondelete='RESTRICT'), nullable=False)
    description = Column(Text)
    hsn_code = Column(String(20))
    batch_number = Column(String(50))
    serial_numbers = Column(Text)
    
    # Quantity
    quantity = Column(Numeric(15, 4), nullable=False)
    free_quantity = Column(Numeric(15, 4), default=0)
    uom = Column(String(20), default='NOS')
    
    # Pricing (Base)
    unit_price_base = Column(Numeric(15, 4), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0)
    discount_amount_base = Column(Numeric(15, 4), default=0)
    taxable_amount_base = Column(Numeric(15, 4), nullable=False)
    
    # GST
    cgst_rate = Column(Numeric(5, 2), default=0)
    cgst_amount_base = Column(Numeric(15, 4), default=0)
    sgst_rate = Column(Numeric(5, 2), default=0)
    sgst_amount_base = Column(Numeric(15, 4), default=0)
    igst_rate = Column(Numeric(5, 2), default=0)
    igst_amount_base = Column(Numeric(15, 4), default=0)
    cess_rate = Column(Numeric(5, 2), default=0)
    cess_amount_base = Column(Numeric(15, 4), default=0)
    tax_amount_base = Column(Numeric(15, 4), default=0)
    
    # Total
    total_amount_base = Column(Numeric(15, 4), nullable=False)
    
    # Foreign Currency
    unit_price_foreign = Column(Numeric(15, 4))
    discount_amount_foreign = Column(Numeric(15, 4))
    taxable_amount_foreign = Column(Numeric(15, 4))
    tax_amount_foreign = Column(Numeric(15, 4))
    total_amount_foreign = Column(Numeric(15, 4))
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    credit_note = relationship("CreditNote", back_populates="items")
    product = relationship("Product")
    
    __table_args__ = (
        UniqueConstraint('credit_note_id', 'line_no', name='uq_credit_note_item_line'),
        CheckConstraint("quantity > 0", name='chk_credit_note_item_quantity'),
        CheckConstraint("unit_price_base >= 0", name='chk_credit_note_item_price'),
        CheckConstraint("total_amount_base = ROUND(taxable_amount_base + tax_amount_base, 4)", name='chk_credit_note_item_total'),
    )