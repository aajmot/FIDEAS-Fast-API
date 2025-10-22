from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy.types import Numeric
from app.db.models.base_model import BaseModel

class Product(BaseModel):
    __tablename__ = 'products'
    
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True)
    composition = Column(Text)
    tags = Column(Text)
    hsn_code = Column(String(20))
    schedule = Column(String(10))
    manufacturer = Column(String(200))
    is_discontinued = Column(Boolean, default=False)
    category_id = Column(Integer, nullable=False)
    unit_id = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    gst_percentage = Column(Numeric(5, 2), default=0)
    commission_type = Column(Text)
    commission_value = Column(Numeric(10, 2))
    reorder_level = Column(Numeric(10, 2), default=0)
    danger_level = Column(Numeric(10, 2), default=0)
    min_stock = Column(Numeric(10, 2), default=0)
    max_stock = Column(Numeric(10, 2), default=0)
    description = Column(Text)
    is_inventory_item = Column(Boolean, default=True)
    tenant_id = Column(Integer, nullable=False)
    created_by = Column(String(100))
    updated_by = Column(String(100))