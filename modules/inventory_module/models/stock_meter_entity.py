from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.types import Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.connection import Base


class StockMeter(Base):
    __tablename__ = 'stock_meter'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    location = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    product = relationship("Product")
