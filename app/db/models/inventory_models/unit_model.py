from sqlalchemy import Column, Integer, String, Boolean, Numeric
from app.db.models.base_model import BaseModel

class Unit(BaseModel):
    __tablename__ = 'units'
    
    name = Column(String(100), nullable=False)
    symbol = Column(String(10), nullable=False)
    parent_id = Column(Integer)
    conversion_factor = Column(Numeric(10, 4), default=1.0)
    tenant_id = Column(Integer, nullable=False)
    created_by = Column(String(100))
    updated_by = Column(String(100))