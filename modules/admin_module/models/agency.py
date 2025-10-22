from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from datetime import datetime
from core.database.connection import Base

class Agency(Base):
    __tablename__ = 'agencies'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(100))
    address = Column(Text)
    tax_id = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    modified_by = Column(String(100))
    is_delete = Column(Boolean, default=False)
