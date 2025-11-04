from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, CheckConstraint, UniqueConstraint
from sqlalchemy.types import Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.connection import Base


class StockAdjustment(Base):
    """Stock Adjustment Header - contains overall adjustment document information"""
    __tablename__ = 'stock_adjustments'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False)
    
    adjustment_number = Column(String(50), nullable=False)
    adjustment_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    adjustment_type = Column(String(20), nullable=False)  # PHYSICAL, DAMAGED, THEFT, OTHER
    reason = Column(String(500), nullable=False)
    
    # Totals (auto-calculated from items)
    total_items = Column(Integer, nullable=False, default=0)
    net_quantity_change = Column(Numeric(15, 4), nullable=False, default=0)
    total_cost_impact = Column(Numeric(15, 4), nullable=False, default=0)
    
    # Optional foreign currency
    currency_id = Column(Integer, ForeignKey('currencies.id', ondelete='SET NULL'))
    exchange_rate = Column(Numeric(15, 4), default=1)
    
    # Accounting
    voucher_id = Column(Integer, ForeignKey('vouchers.id', ondelete='SET NULL'))
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    __table_args__ = (
        UniqueConstraint('adjustment_number', 'tenant_id', name='uq_adjustment_number_tenant'),
        CheckConstraint("adjustment_type IN ('PHYSICAL', 'DAMAGED', 'THEFT', 'OTHER')", name='chk_adjustment_type'),
    )
    
    # Relationships
    items = relationship("StockAdjustmentItem", back_populates="adjustment", cascade="all, delete-orphan")
    warehouse = relationship("Warehouse")
    currency = relationship("Currency")
    voucher = relationship("Voucher")


class StockAdjustmentItem(Base):
    """Stock Adjustment Line Item - individual products in the adjustment document"""
    __tablename__ = 'stock_adjustment_items'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    adjustment_id = Column(Integer, ForeignKey('stock_adjustments.id', ondelete='CASCADE'), nullable=False)
    line_no = Column(Integer, nullable=False)
    
    product_id = Column(Integer, ForeignKey('products.id', ondelete='RESTRICT'), nullable=False)
    batch_number = Column(String(50))
    
    # Adjustment Direction & Quantity (+ve = increase, -ve = decrease)
    adjustment_qty = Column(Numeric(12, 4), nullable=False)
    uom = Column(String(20), nullable=False, default='NOS')
    
    # Current stock (before adjustment) - for audit
    stock_before = Column(Numeric(12, 4), nullable=False, default=0)
    stock_after = Column(Numeric(12, 4), nullable=False, default=0)
    
    # Cost
    unit_cost_base = Column(Numeric(15, 4), nullable=False)
    cost_impact = Column(Numeric(15, 4), nullable=False)  # = adjustment_qty * unit_cost_base
    
    # Optional foreign currency
    currency_id = Column(Integer, ForeignKey('currencies.id', ondelete='SET NULL'))
    unit_cost_foreign = Column(Numeric(15, 4))
    cost_impact_foreign = Column(Numeric(15, 4))
    exchange_rate = Column(Numeric(15, 4), default=1)
    
    # Optional line reason
    reason = Column(String(500))
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_deleted = Column(Boolean, default=False)
    
    __table_args__ = (
        UniqueConstraint('adjustment_id', 'line_no', name='uq_adj_item_line'),
        CheckConstraint('unit_cost_base >= 0', name='chk_unit_cost_base_positive'),
    )
    
    # Relationships
    adjustment = relationship("StockAdjustment", back_populates="items")
    product = relationship("Product")
    currency = relationship("Currency")
