from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.types import Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.connection import Base


class PurchaseOrder(Base):
    __tablename__ = 'purchase_orders'
    
    id = Column(Integer, primary_key=True)
    po_number = Column(String(50), unique=True, nullable=False)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow)
    total_amount = Column(Numeric(10, 2), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    roundoff = Column(Numeric(10, 2), default=0)
    status = Column(String(20), default='pending')
    reversal_reason = Column(Text)
    reversed_at = Column(DateTime)
    reversed_by = Column(String(100))
    is_deleted = Column(Boolean, default=False)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_by = Column(String(100))
    
    supplier = relationship("Supplier")
    order_items = relationship("PurchaseOrderItem", back_populates="purchase_order")


class PurchaseOrderItem(Base):
    __tablename__ = 'purchase_order_items'
    
    id = Column(Integer, primary_key=True)
    purchase_order_id = Column(Integer, ForeignKey('purchase_orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    product_name = Column(Text)
    batch_number = Column(String(50))
    quantity = Column(Numeric(10, 2), nullable=False)
    free_quantity = Column(Numeric(10, 2), default=0)
    unit_price = Column(Numeric(10, 2), nullable=False)
    mrp = Column(Numeric(18, 2), nullable=True)
    gst_rate = Column(Numeric(5, 2), default=0)
    cgst_rate = Column(Numeric(5, 2), default=0)
    sgst_rate = Column(Numeric(5, 2), default=0)
    gst_amount = Column(Numeric(18, 2), nullable=True)
    cgst_amount = Column(Numeric(18, 2), nullable=True)
    sgst_amount = Column(Numeric(18, 2), nullable=True)
    description = Column(Text)
    discount_percent = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    total_amount = Column(Numeric(10, 2), nullable=False)
    
    purchase_order = relationship("PurchaseOrder", back_populates="order_items")
    product = relationship("Product")
