from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Numeric, CheckConstraint, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.connection import Base


class SalesOrder(Base):
    __tablename__ = 'sales_orders'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    
    # Order Info
    order_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    order_number = Column(String(50), unique=True, nullable=False)
    reference_number = Column(String(100))  # Invoice/PO reference
    
    # Customer
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    customer_name = Column(String(200))
    customer_phone = Column(String(20))
    agency_id = Column(Integer, ForeignKey('agencies.id'))
    
    # === AMOUNT BREAKDOWN (Critical for Journal) ===
    subtotal_amount = Column(Numeric(12, 4), nullable=False, default=0)  # Sum of line total_price (before discount)
    header_discount_percent = Column(Numeric(5, 2), default=0)
    header_discount_amount = Column(Numeric(12, 4), default=0)
    
    taxable_amount = Column(Numeric(12, 4), nullable=False, default=0)  # After all discounts
    cgst_amount = Column(Numeric(12, 4), default=0)
    sgst_amount = Column(Numeric(12, 4), default=0)
    igst_amount = Column(Numeric(12, 4), default=0)
    utgst_amount = Column(Numeric(12, 4), default=0)
    
    # total_tax_amount - computed in DB but can be set manually
    total_tax_amount = Column(Numeric(12, 4), default=0)
    
    agent_commission_percent = Column(Numeric(5, 2))
    agent_commission_amount = Column(Numeric(12, 4), default=0)
    
    roundoff = Column(Numeric(12, 4), default=0)
    net_amount = Column(Numeric(12, 4), nullable=False)  # Final payable = taxable + tax + roundoff
    
    # === MULTI-CURRENCY ===
    currency_id = Column(Integer, ForeignKey('currencies.id'), default=1)  # 1 = Base (INR)
    exchange_rate = Column(Numeric(12, 6), default=1.000000)
    # net_amount_base - computed in DB but can be set manually
    net_amount_base = Column(Numeric(12, 4), default=0)
    
    # Status & Reversal
    status = Column(String(20), default='DRAFT')
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
        CheckConstraint("status IN ('DRAFT','ORDERED','APPROVED','INVOICED','CANCELLED','REVERSED')", name='check_so_status'),
    )
    
    customer = relationship("Customer", back_populates="sales_orders")
    order_items = relationship("SalesOrderItem", back_populates="sales_order")


class SalesOrderItem(Base):
    __tablename__ = 'sales_order_items'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    
    sales_order_id = Column(Integer, ForeignKey('sales_orders.id', ondelete='CASCADE'), nullable=False)
    
    # Product
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    product_name = Column(String(200), nullable=False)
    batch_number = Column(String(100))
    expiry_date = Column(Date)
    
    # Quantity
    quantity = Column(Numeric(10, 2), nullable=False, default=0)
    free_quantity = Column(Numeric(10, 2), default=0)
    
    # Pricing
    mrp_price = Column(Numeric(12, 4))
    unit_price = Column(Numeric(12, 4), nullable=False)  # After line discount
    line_discount_percent = Column(Numeric(5, 2), default=0)
    line_discount_amount = Column(Numeric(12, 4), default=0)
    
    # === TAX BREAKDOWN (Per Line) ===
    taxable_amount = Column(Numeric(12, 4), nullable=False)  # (qty * unit_price) - line_discount
    cgst_rate = Column(Numeric(5, 2), default=0)
    cgst_amount = Column(Numeric(12, 4), default=0)
    sgst_rate = Column(Numeric(5, 2), default=0)
    sgst_amount = Column(Numeric(12, 4), default=0)
    igst_rate = Column(Numeric(5, 2), default=0)
    igst_amount = Column(Numeric(12, 4), default=0)
    utgst_rate = Column(Numeric(5, 2), default=0)
    utgst_amount = Column(Numeric(12, 4), default=0)
    
    agent_commission_percent = Column(Numeric(5, 2))
    agent_commission_amount = Column(Numeric(12, 4), default=0)
    
    total_price = Column(Numeric(12, 4), nullable=False)  # taxable + tax
    
    # Narration (optional)
    narration = Column(Text)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_deleted = Column(Boolean, default=False)
    
    sales_order = relationship("SalesOrder", back_populates="order_items")
    product = relationship("Product")
