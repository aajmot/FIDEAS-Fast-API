from sqlalchemy import Column, Integer, String, Text
from app.db.models.base_model import BaseModel

class LegalEntity(BaseModel):
    __tablename__ = 'legal_entities'
    
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=False)
    registration_number = Column(String(50))
    address = Column(Text)
    logo = Column(String(255))
    admin_user_id = Column(Integer)
    tenant_id = Column(Integer, nullable=False)
    created_by = Column(String(100))
    updated_by = Column(String(100))