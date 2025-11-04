from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, CheckConstraint, UniqueConstraint
from sqlalchemy.types import Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.connection import Base


class StockTransfer(Base):
    """Stock Transfer Header - contains overall transfer document information"""
    __tablename__ = 'stock_transfers'
    __table_args__ = (
        UniqueConstraint('transfer_number', 'tenant_id', name='uq_transfer_number_tenant'),
        CheckConstraint("transfer_type IN ('INTERNAL', 'INTERCOMPANY', 'RETURN')", name='chk_transfer_type'),
        CheckConstraint("status IN ('DRAFT', 'APPROVED', 'IN_TRANSIT', 'COMPLETED', 'CANCELLED')", name='chk_status'),
        CheckConstraint('from_warehouse_id != to_warehouse_id', name='chk_warehouses_different'),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    
    transfer_number = Column(String(50), nullable=False)
    from_warehouse_id = Column(Integer, ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False)
    to_warehouse_id = Column(Integer, ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False)
    transfer_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    transfer_type = Column(String(20), nullable=False)  # INTERNAL, INTERCOMPANY, RETURN
    reason = Column(String(500))
    
    # Totals (auto-calculated from items)
    total_items = Column(Integer, nullable=False, default=0)
    total_quantity = Column(Numeric(15, 4), nullable=False, default=0)
    total_cost_base = Column(Numeric(15, 4), nullable=False, default=0)
    
    # Optional foreign currency
    currency_id = Column(Integer, ForeignKey('currencies.id', ondelete='SET NULL'))
    exchange_rate = Column(Numeric(15, 4), default=1)
    
    # Status & Approval
    status = Column(String(20), nullable=False, default='DRAFT')  # DRAFT, APPROVED, IN_TRANSIT, COMPLETED, CANCELLED
    approval_request_id = Column(Integer)
    approved_by = Column(String(100))
    approved_at = Column(DateTime)
    
    # Accounting
    from_voucher_id = Column(Integer, ForeignKey('vouchers.id', ondelete='SET NULL'))
    to_voucher_id = Column(Integer, ForeignKey('vouchers.id', ondelete='SET NULL'))
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    items = relationship("StockTransferItem", back_populates="transfer", cascade="all, delete-orphan")
    from_warehouse = relationship("Warehouse", foreign_keys=[from_warehouse_id])
    to_warehouse = relationship("Warehouse", foreign_keys=[to_warehouse_id])
    currency = relationship("Currency")
    from_voucher = relationship("Voucher", foreign_keys=[from_voucher_id])
    to_voucher = relationship("Voucher", foreign_keys=[to_voucher_id])


class StockTransferItem(Base):
    """Stock Transfer Line Item - individual products in the transfer document"""
    __tablename__ = 'stock_transfer_items'
    __table_args__ = (
        UniqueConstraint('transfer_id', 'line_no', name='uq_transfer_item_line'),
        CheckConstraint('quantity > 0', name='chk_quantity_positive'),
        CheckConstraint('unit_cost_base >= 0', name='chk_unit_cost_base_positive'),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    transfer_id = Column(Integer, ForeignKey('stock_transfers.id', ondelete='CASCADE'), nullable=False)
    line_no = Column(Integer, nullable=False)
    
    product_id = Column(Integer, ForeignKey('products.id', ondelete='RESTRICT'), nullable=False)
    batch_number = Column(String(50))
    
    # Quantity
    quantity = Column(Numeric(12, 4), nullable=False)
    uom = Column(String(20), nullable=False, default='NOS')
    
    # Stock Before/After (for audit)
    from_stock_before = Column(Numeric(12, 4), nullable=False, default=0)
    from_stock_after = Column(Numeric(12, 4), nullable=False, default=0)
    to_stock_before = Column(Numeric(12, 4), nullable=False, default=0)
    to_stock_after = Column(Numeric(12, 4), nullable=False, default=0)
    
    # Cost (from source warehouse)
    unit_cost_base = Column(Numeric(15, 4), nullable=False)
    total_cost_base = Column(Numeric(15, 4), nullable=False)
    
    # Optional foreign currency
    currency_id = Column(Integer, ForeignKey('currencies.id', ondelete='SET NULL'))
    unit_cost_foreign = Column(Numeric(15, 4))
    total_cost_foreign = Column(Numeric(15, 4))
    exchange_rate = Column(Numeric(15, 4), default=1)
    
    # Line reason
    reason = Column(String(500))
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    transfer = relationship("StockTransfer", back_populates="items")
    product = relationship("Product")
    currency = relationship("Currency")
