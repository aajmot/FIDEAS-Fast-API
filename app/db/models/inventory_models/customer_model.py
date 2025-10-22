from sqlalchemy import Column, Integer, String, Text
from app.db.models.base_model import BaseModel

class Customer(BaseModel):
    __tablename__ = 'customers'
    
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(100))
    age = Column(Integer)
    address = Column(Text)
    tax_id = Column(String(50))
    tenant_id = Column(Integer, nullable=False)
    created_by = Column(String(100))
    updated_by = Column(String(100))