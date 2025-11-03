from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Computed
from sqlalchemy.types import Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.connection import Base


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)

    # Core Info
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True)
    description = Column(Text)
    composition = Column(Text)
    tags = Column(Text)
    hsn_code = Column(String(20))
    schedule = Column(String(10))
    manufacturer = Column(String(200))
    is_discontinued = Column(Boolean, default=False)

    # Category / Unit
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    unit_id = Column(Integer, ForeignKey('units.id'), nullable=False)

    # Pricing
    mrp_price = Column(Numeric(12, 4), nullable=False)
    selling_price = Column(Numeric(12, 4), nullable=False)
    cost_price = Column(Numeric(12, 4), nullable=False, default=0)
    is_tax_inclusive = Column(Boolean, default=False)

    # Tax configuration
    hsn_id = Column(Integer, ForeignKey('hsn_codes.id'))
    gst_rate = Column(Numeric(5, 2), default=0.00)
    # cgst/sgst are stored/generated columns in DB: computed as gst_rate / 2 (persisted/stored)
    cgst_rate = Column(Numeric(5, 2), Computed("gst_rate / 2", persisted=True))
    sgst_rate = Column(Numeric(5, 2), Computed("gst_rate / 2", persisted=True))
    igst_rate = Column(Numeric(5, 2), default=0.00)
    cess_rate = Column(Numeric(5, 2), default=0.00)
    is_reverse_charge = Column(Boolean, default=False)
    is_composite = Column(Boolean, default=False)

    # Inventory
    is_inventory_item = Column(Boolean, default=True)
    reorder_level = Column(Numeric(10, 2), default=0)
    danger_level = Column(Numeric(10, 2), default=0)
    min_stock = Column(Numeric(10, 2), default=0)
    max_stock = Column(Numeric(10, 2), default=0)

    # Commission/Discount
    commission_type = Column(String(20), default='FIXED')
    commission_value = Column(Numeric(10, 2), default=0.00)
    max_discount_percent = Column(Numeric(5, 2), default=100.00)

    # Tracking
    barcode = Column(String(100))
    is_serialized = Column(Boolean, default=False)
    warranty_months = Column(Integer)

    # Status & multi-currency
    is_active = Column(Boolean, default=True)
    currency_id = Column(Integer, ForeignKey('currencies.id'), default=1)
    exchange_rate = Column(Numeric(12, 6), default=1.000000)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_deleted = Column(Boolean, default=False)

    category = relationship("Category", back_populates="products")
    unit = relationship("Unit", back_populates="products")

    inventory_items = relationship("Inventory", back_populates="product")
