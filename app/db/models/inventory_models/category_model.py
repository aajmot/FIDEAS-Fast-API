from sqlalchemy import Column, Integer, String, Text
from app.db.models.base_model import BaseModel

class Category(BaseModel):
    __tablename__ = 'categories'
    __table_args__ = {'extend_existing': True}
    
    name = Column(String(100), nullable=False)
    description = Column(Text)
    parent_id = Column(Integer)
    tenant_id = Column(Integer, nullable=False)
    created_by = Column(String(100))
    updated_by = Column(String(100))