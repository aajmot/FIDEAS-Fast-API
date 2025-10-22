from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Numeric
from datetime import datetime
from core.database.connection import Base
# Import related models to ensure they're available for foreign keys
from modules.admin_module.models.entities import Tenant
from modules.admin_module.models.agency import Agency

class OrderCommission(Base):
    __tablename__ = 'order_commissions'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    order_commission_number = Column(String(50))
    order_type = Column(Text, nullable=False)
    order_id = Column(Integer, nullable=False)
    order_number = Column(Text, nullable=False)
    agency_id = Column(Integer, ForeignKey('agencies.id'), nullable=True)
    agency_name = Column(Text)
    agency_phone = Column(Text)
    notes = Column(Text)
    total_amount = Column(Numeric(15, 2), default=0)
    disc_percentage = Column(Numeric(5, 2), default=0)
    disc_amount = Column(Numeric(15, 2), default=0)
    roundoff = Column(Numeric(15, 2), default=0)
    final_amount = Column(Numeric(15, 2), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100))
    is_deleted = Column(Boolean, default=False)

class OrderCommissionItem(Base):
    __tablename__ = 'order_commission_items'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    order_commission_id = Column(Integer, ForeignKey('order_commissions.id'), nullable=False)
    item_type = Column(Text, nullable=False)
    item_id = Column(Integer, nullable=False)
    item_name = Column(Text)
    item_rate = Column(Numeric(15, 2), default=0)
    commission_percentage = Column(Numeric(5, 2), default=0)
    commission_value = Column(Numeric(15, 2), default=0)
    gst_percentage = Column(Numeric(5, 2), default=0)
    gst_amount = Column(Numeric(15, 2), default=0)
    cess_percentage = Column(Numeric(5, 2), default=0)
    cess_amount = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), default=0)
    discount_percentage = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    roundoff = Column(Numeric(15, 2), default=0)
    final_amount = Column(Numeric(15, 2), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100))
    is_deleted = Column(Boolean, default=False)