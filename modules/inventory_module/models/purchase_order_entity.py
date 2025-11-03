from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Numeric, CheckConstraint, Computed
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from core.database.connection import Base


class PurchaseOrder(Base):
    __tablename__ = 'purchase_orders'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    
    # PO Info
    po_number = Column(String(50), unique=True, nullable=False)
    reference_number = Column(String(100))  # Supplier PO/Quote
    order_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Supplier
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    supplier_name = Column(String(200))
    supplier_gstin = Column(String(15))
    
    # === AMOUNT BREAKDOWN ===
    subtotal_amount = Column(Numeric(12, 4), nullable=False, default=0)  # Sum of line total_price
    header_discount_percent = Column(Numeric(5, 2), default=0)
    header_discount_amount = Column(Numeric(12, 4), default=0)
    
    taxable_amount = Column(Numeric(12, 4), nullable=False, default=0)  # After all discounts
    cgst_amount = Column(Numeric(12, 4), default=0)
    sgst_amount = Column(Numeric(12, 4), default=0)
    igst_amount = Column(Numeric(12, 4), default=0)
    cess_amount = Column(Numeric(12, 4), default=0)
    
    # total_tax_amount - GENERATED column in DB, computed by database
    total_tax_amount = Column(Numeric(12, 4), Computed("cgst_amount + sgst_amount + igst_amount + cess_amount", persisted=True))
    
    roundoff = Column(Numeric(12, 4), default=0)
    net_amount = Column(Numeric(12, 4), nullable=False)  # Final payable
    
    # === MULTI-CURRENCY ===
    currency_id = Column(Integer, ForeignKey('currencies.id'), default=1)
    exchange_rate = Column(Numeric(12, 6), default=1.000000)
    # net_amount_base - GENERATED column in DB, computed by database
    net_amount_base = Column(Numeric(12, 4), Computed("net_amount * exchange_rate", persisted=True))
    
    # === TAX & RCM ===
    is_reverse_charge = Column(Boolean, default=False)
    is_tax_inclusive = Column(Boolean, default=False)  # Purchase price includes GST?
    
    # Status
    status = Column(String(20), default='DRAFT')
    approval_status = Column(String(20), default='DRAFT')
    approval_request_id = Column(Integer)
    
    # Reversal
    reversal_reason = Column(Text)
    reversed_at = Column(DateTime)
    reversed_by = Column(String(100))
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_deleted = Column(Boolean, default=False)
    
    __table_args__ = (
        CheckConstraint("status IN ('DRAFT','APPROVED','RECEIVED','BILLED','CANCELLED','REVERSED')", name='check_po_status'),
    )
    
    supplier = relationship("Supplier")
    order_items = relationship("PurchaseOrderItem", back_populates="purchase_order")


class PurchaseOrderItem(Base):
    __tablename__ = 'purchase_order_items'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    
    purchase_order_id = Column(Integer, ForeignKey('purchase_orders.id', ondelete='CASCADE'), nullable=False)
    
    # Product
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    product_name = Column(String(200), nullable=False)
    hsn_code = Column(String(20))
    description = Column(Text)
    
    # Quantity
    quantity = Column(Numeric(10, 2), nullable=False, default=0)
    free_quantity = Column(Numeric(10, 2), default=0)
    
    # Pricing
    mrp = Column(Numeric(12, 4))
    unit_price = Column(Numeric(12, 4), nullable=False)  # After line discount
    line_discount_percent = Column(Numeric(5, 2), default=0)
    line_discount_amount = Column(Numeric(12, 4), default=0)
    
    # === TAX BREAKDOWN (Per Line) ===
    taxable_amount = Column(Numeric(12, 4), nullable=False)  # (qty * unit_price) - discount
    cgst_rate = Column(Numeric(5, 2), default=0)
    cgst_amount = Column(Numeric(12, 4), default=0)
    sgst_rate = Column(Numeric(5, 2), default=0)
    sgst_amount = Column(Numeric(12, 4), default=0)
    igst_rate = Column(Numeric(5, 2), default=0)
    igst_amount = Column(Numeric(12, 4), default=0)
    cess_rate = Column(Numeric(5, 2), default=0)
    cess_amount = Column(Numeric(12, 4), default=0)
    
    total_price = Column(Numeric(12, 4), nullable=False)  # taxable + tax
    
    # Batch & Tracking
    batch_number = Column(String(50))
    expiry_date = Column(DateTime)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_deleted = Column(Boolean, default=False)
    
    purchase_order = relationship("PurchaseOrder", back_populates="order_items")
    product = relationship("Product")
