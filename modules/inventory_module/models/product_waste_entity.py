from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.types import Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.connection import Base


class ProductWaste(Base):
    __tablename__ = 'product_waste'
    
    id = Column(Integer, primary_key=True)
    waste_number = Column(String(50), unique=True, nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    batch_number = Column(String(50))
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_cost = Column(Numeric(10, 2), nullable=False)
    total_cost = Column(Numeric(10, 2), nullable=False)
    reason = Column(String(500), nullable=False)
    waste_date = Column(DateTime, default=datetime.utcnow)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    
    product = relationship("Product")
