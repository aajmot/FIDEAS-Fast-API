from sqlalchemy import Column, Integer, String, Text
from app.db.models.base_model import BaseModel

class Role(BaseModel):
    __tablename__ = 'roles'
    
    name = Column(String(50), nullable=False)
    description = Column(Text)
    tenant_id = Column(Integer, nullable=False)
    created_by = Column(String(100))
    updated_by = Column(String(100))