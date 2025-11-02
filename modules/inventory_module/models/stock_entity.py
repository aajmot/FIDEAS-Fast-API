from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from modules.inventory_module.models.entities import Base

class StockTransaction(Base):
    __tablename__ = 'stock_transactions'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    transaction_type = Column(String(20), nullable=False)  # 'IN' or 'OUT'
    transaction_source = Column(String(20), nullable=False)  # 'PURCHASE' or 'SALES'
    reference_id = Column(Integer, nullable=False)  # PO or SO ID
    reference_number = Column(String(50), nullable=False)  # PO or SO Number
    batch_number = Column(String(50))
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    transaction_date = Column(DateTime, default=datetime.utcnow)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    
    product = relationship("Product")

class StockBalance(Base):
    __tablename__ = 'stock_balances'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    batch_number = Column(String(50))
    available_quantity = Column(Numeric(10, 2), default=0)
    reserved_quantity = Column(Numeric(10, 2), default=0)
    total_quantity = Column(Numeric(10, 2), default=0)
    average_cost = Column(Numeric(10, 2), default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    
    product = relationship("Product")