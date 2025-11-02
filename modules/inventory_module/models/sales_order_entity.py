from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.types import Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.connection import Base


class SalesOrder(Base):
    __tablename__ = 'sales_orders'
    
    id = Column(Integer, primary_key=True)
    order_number = Column(String(50), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    agency_id = Column(Integer, ForeignKey('agencies.id'))
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
    
    customer = relationship("Customer", back_populates="sales_orders")
    order_items = relationship("SalesOrderItem", back_populates="sales_order")


class SalesOrderItem(Base):
    __tablename__ = 'sales_order_items'
    
    id = Column(Integer, primary_key=True)
    sales_order_id = Column(Integer, ForeignKey('sales_orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    product_name = Column(Text)
    batch_number = Column(String(50))
    quantity = Column(Numeric(10, 2), nullable=False)
    free_quantity = Column(Numeric(10, 2), default=0)
    unit_price = Column(Numeric(10, 2), nullable=False)
    gst_rate = Column(Numeric(5, 2), default=0)
    cgst_rate = Column(Numeric(5, 2), default=0)
    sgst_rate = Column(Numeric(5, 2), default=0)
    discount_percent = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    mrp = Column(Numeric(18, 2), nullable=True)
    gst_amount = Column(Numeric(18, 2), nullable=True)
    cgst_amount = Column(Numeric(18, 2), nullable=True)
    sgst_amount = Column(Numeric(18, 2), nullable=True)
    description = Column(Text)
    total_price = Column(Numeric(10, 2), nullable=False)
    
    sales_order = relationship("SalesOrder", back_populates="order_items")
    product = relationship("Product")
