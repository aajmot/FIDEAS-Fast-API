from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.types import Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.connection import Base


class Unit(Base):
    __tablename__ = 'units'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    symbol = Column(String(10))
    parent_id = Column(Integer, ForeignKey('units.id'))
    conversion_factor = Column(Numeric(10, 4), default=1.0)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    updated_by = Column(String(100))
    
    parent = relationship("Unit", remote_side=[id], backref="subunits")
    products = relationship("Product", back_populates="unit")
