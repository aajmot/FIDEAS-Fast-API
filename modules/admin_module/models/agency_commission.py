from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Numeric
from datetime import datetime
from core.database.connection import Base

class AgencyCommission(Base):
    __tablename__ = 'agency_commissions'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    agency_id = Column(Integer, ForeignKey('agencies.id'), nullable=False)
    product_type = Column(Text, nullable=False)
    product_id = Column(Integer, nullable=False)
    product_name = Column(Text, nullable=False)
    product_rate = Column(Numeric(10, 2))
    notes = Column(Text)
    commission_type = Column(Text)
    commission_value = Column(Numeric(10, 2))
    effective_from = Column(DateTime)
    effective_to = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100))
    is_deleted = Column(Boolean, default=False)
