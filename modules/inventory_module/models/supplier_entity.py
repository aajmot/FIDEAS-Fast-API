from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from datetime import datetime
from core.database.connection import Base


class Supplier(Base):
    __tablename__ = 'suppliers'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    
    # Basic Info & Contact
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(100))
    tax_id = Column(String(50))
    address = Column(Text)
    contact_person = Column(String(100))
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Audit Fields
    created_at = Column(DateTime)
    created_by = Column(String(100))
    updated_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
