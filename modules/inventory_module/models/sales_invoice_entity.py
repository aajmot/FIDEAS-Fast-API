from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Numeric, Date, CheckConstraint, UniqueConstraint, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.connection import Base

# Import related models to ensure they're available for relationships
from modules.admin_module.models.address import Address
from modules.admin_module.models.currency import Currency
from modules.account_module.models.payment_term_entity import PaymentTerm
from modules.account_module.models.entities import Voucher


class SalesInvoice(Base):
    """Sales Invoice - records customer invoices with GST, e-Invoice and e-Way Bill support"""
    __tablename__ = 'sales_invoices'
    __table_args__ = (
        UniqueConstraint('invoice_number', 'tenant_id', name='uq_sales_invoice_number_tenant'),
        CheckConstraint(
            "(foreign_currency_id IS NULL AND exchange_rate = 1 AND subtotal_foreign IS NULL AND total_amount_foreign IS NULL) "
            "OR (foreign_currency_id IS NOT NULL AND exchange_rate > 0)",
            name='chk_currency_logic'
        ),
        CheckConstraint('due_date IS NULL OR due_date >= invoice_date', name='chk_due_date'),
        CheckConstraint(
            'tax_amount_base = cgst_amount_base + sgst_amount_base + igst_amount_base + cess_amount_base',
            name='chk_gst_sum'
        ),
        CheckConstraint(
            "status IN ('DRAFT', 'POSTED', 'PAID', 'PARTIALLY_PAID', 'CANCELLED', 'CREDIT_NOTE')",
            name='chk_status'
        ),
        CheckConstraint(
            "invoice_type IN ('TAX_INVOICE', 'BILL_OF_SUPPLY', 'EXPORT', 'CREDIT_NOTE')",
            name='chk_invoice_type'
        ),
        CheckConstraint(
            "einvoice_status IN ('PENDING', 'GENERATED', 'CANCELLED', 'FAILED')",
            name='chk_einvoice_status'
        ),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    
    # Invoice identification
    invoice_number = Column(String(50), nullable=False)
    reference_number = Column(String(50))  # Customer PO number
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date)
    
    # References
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='RESTRICT'), nullable=False)
    sales_order_id = Column(Integer, ForeignKey('sales_orders.id', ondelete='SET NULL'))
    payment_term_id = Column(Integer, ForeignKey('payment_terms.id', ondelete='SET NULL'))
    warehouse_id = Column(Integer, ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False)
    shipping_address_id = Column(Integer, ForeignKey('addresses.id', ondelete='SET NULL'))
    
    # Currency
    base_currency_id = Column(Integer, ForeignKey('currencies.id', ondelete='RESTRICT'), nullable=False)
    foreign_currency_id = Column(Integer, ForeignKey('currencies.id', ondelete='SET NULL'))
    exchange_rate = Column(Numeric(15, 6), default=1)
    
    # GST Summary (Base Currency) - Note: No UGST for sales
    cgst_amount_base = Column(Numeric(15, 4), default=0)
    sgst_amount_base = Column(Numeric(15, 4), default=0)
    igst_amount_base = Column(Numeric(15, 4), default=0)
    cess_amount_base = Column(Numeric(15, 4), default=0)
    
    # Totals (Base Currency)
    subtotal_base = Column(Numeric(15, 4), default=0)
    discount_amount_base = Column(Numeric(15, 4), default=0)
    tax_amount_base = Column(Numeric(15, 4), default=0)
    total_amount_base = Column(Numeric(15, 4), nullable=False, default=0)
    
    # Totals (Foreign Currency)
    subtotal_foreign = Column(Numeric(15, 4))
    discount_amount_foreign = Column(Numeric(15, 4))
    tax_amount_foreign = Column(Numeric(15, 4))
    total_amount_foreign = Column(Numeric(15, 4))
    
    # Payment tracking
    paid_amount_base = Column(Numeric(15, 4), default=0)
    balance_amount_base = Column(Numeric(15, 4), default=0)
    
    # Status
    status = Column(String(20), nullable=False, default='DRAFT')
    invoice_type = Column(String(20), nullable=False, default='TAX_INVOICE')
    
    # e-Invoice fields
    is_einvoice = Column(Boolean, default=False)
    einvoice_irn = Column(String(100))  # Invoice Reference Number
    einvoice_ack_no = Column(String(50))  # Acknowledgement Number
    einvoice_ack_date = Column(DateTime)
    einvoice_qr_code = Column(Text)
    einvoice_status = Column(String(20), default='PENDING')
    
    # e-Way Bill fields
    eway_bill_no = Column(String(50))
    eway_bill_date = Column(DateTime)
    eway_bill_valid_till = Column(DateTime)
    
    # Accounting
    voucher_id = Column(Integer, ForeignKey('vouchers.id', ondelete='SET NULL'))
    
    # Metadata
    notes = Column(Text)
    terms_conditions = Column(Text)
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
    sales_order = relationship("SalesOrder")
    payment_term = relationship("PaymentTerm")
    warehouse = relationship("Warehouse")
    shipping_address = relationship("Address", foreign_keys=[shipping_address_id])
    base_currency = relationship("Currency", foreign_keys=[base_currency_id])
    foreign_currency = relationship("Currency", foreign_keys=[foreign_currency_id])
    voucher = relationship("Voucher")
    invoice_items = relationship("SalesInvoiceItem", back_populates="invoice", cascade="all, delete-orphan")


class SalesInvoiceItem(Base):
    """Sales Invoice Line Items - with COGS tracking"""
    __tablename__ = 'sales_invoice_items'
    __table_args__ = (
        UniqueConstraint('invoice_id', 'line_no', name='uq_sales_invoice_item_line'),
        CheckConstraint('quantity > 0', name='chk_quantity_positive'),
        CheckConstraint('unit_price_base >= 0', name='chk_unit_price_non_negative'),
        CheckConstraint('unit_cost_base >= 0', name='chk_unit_cost_non_negative'),
        CheckConstraint(
            'total_amount_base = ROUND(taxable_amount_base + tax_amount_base, 4)',
            name='chk_sales_invoice_item_line_total'
        ),
        CheckConstraint(
            "(cgst_amount_base > 0 AND sgst_amount_base > 0 AND igst_amount_base = 0) "
            "OR (igst_amount_base > 0 AND cgst_amount_base = 0 AND sgst_amount_base = 0) "
            "OR (cgst_amount_base = 0 AND sgst_amount_base = 0 AND igst_amount_base = 0)",
            name='chk_sales_invoice_item_gst_exclusivity'
        ),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    invoice_id = Column(Integer, ForeignKey('sales_invoices.id', ondelete='CASCADE'), nullable=False)
    line_no = Column(Integer, nullable=False)
    
    # Product info
    product_id = Column(Integer, ForeignKey('products.id', ondelete='RESTRICT'), nullable=False)
    description = Column(Text)
    hsn_code = Column(String(20))
    batch_number = Column(String(50))
    serial_numbers = Column(Text)
    
    # Quantity
    quantity = Column(Numeric(15, 4), nullable=False)
    uom = Column(String(20), default='NOS')
    
    # Pricing (Base Currency)
    unit_price_base = Column(Numeric(15, 4), nullable=False)
    unit_cost_base = Column(Numeric(15, 4), nullable=False)  # For COGS calculation
    discount_percent = Column(Numeric(5, 2), default=0)
    discount_amount_base = Column(Numeric(15, 4), default=0)
    taxable_amount_base = Column(Numeric(15, 4), nullable=False)
    
    # GST Components (Base Currency) - No UGST for sales
    cgst_rate = Column(Numeric(5, 2), default=0)
    cgst_amount_base = Column(Numeric(15, 4), default=0)
    sgst_rate = Column(Numeric(5, 2), default=0)
    sgst_amount_base = Column(Numeric(15, 4), default=0)
    igst_rate = Column(Numeric(5, 2), default=0)
    igst_amount_base = Column(Numeric(15, 4), default=0)
    cess_rate = Column(Numeric(5, 2), default=0)
    cess_amount_base = Column(Numeric(15, 4), default=0)
    tax_amount_base = Column(Numeric(15, 4), default=0)
    
    # Total (Base Currency)
    total_amount_base = Column(Numeric(15, 4), nullable=False)
    
    # Foreign Currency (Optional)
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
    invoice = relationship("SalesInvoice", back_populates="invoice_items")
    product = relationship("Product")
