from sqlalchemy import Column, Integer, String, Text
from app.db.models.base_model import BaseModel

class Supplier(BaseModel):
    __tablename__ = 'suppliers'
    
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(100))
    tax_id = Column(String(50))
    contact_person = Column(String(100))
    address = Column(Text)
    tenant_id = Column(Integer, nullable=False)
    created_by = Column(String(100))
    updated_by = Column(String(100))