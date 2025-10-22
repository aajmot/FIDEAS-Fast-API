from sqlalchemy import Column, Integer, String, Boolean, Text
from sqlalchemy.types import Numeric
from app.db.models.base_model import BaseModel

class TestPanel(BaseModel):
    __tablename__ = 'test_panels'
    
    tenant_id = Column(Integer, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category_id = Column(Integer)
    cost = Column(Numeric(10, 2))
    gst = Column(Numeric(5, 2))
    cess = Column(Numeric(5, 2))
    created_by = Column(String(100))
    updated_by = Column(String(100))
    is_deleted = Column(Boolean, default=False)

class TestPanelItem(BaseModel):
    __tablename__ = 'test_panel_items'
    
    tenant_id = Column(Integer, nullable=False)
    panel_id = Column(Integer, nullable=False)
    test_id = Column(Integer, nullable=False)
    test_name = Column(String(200))
    created_by = Column(String(100))
    updated_by = Column(String(100))
    is_deleted = Column(Boolean, default=False)