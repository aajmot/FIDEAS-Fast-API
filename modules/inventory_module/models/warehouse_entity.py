from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.connection import Base

class Warehouse(Base):
    __tablename__ = 'warehouses'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    address = Column(Text)
    contact_person = Column(String(100))
    phone = Column(String(20))
    email = Column(String(100))
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    updated_by = Column(String(100))
    
    # Relationships
    stock_locations = relationship("StockByLocation", back_populates="warehouse")
    from_transfers = relationship("StockTransfer", foreign_keys="StockTransfer.from_warehouse_id", back_populates="from_warehouse")
    to_transfers = relationship("StockTransfer", foreign_keys="StockTransfer.to_warehouse_id", back_populates="to_warehouse")

class StockByLocation(Base):
    __tablename__ = 'stock_by_location'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False, default=0)
    available_quantity = Column(Numeric(10, 2), nullable=False, default=0)
    reserved_quantity = Column(Numeric(10, 2), default=0)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = relationship("Product")
    warehouse = relationship("Warehouse", back_populates="stock_locations")

# NOTE: StockTransfer and StockTransferItem classes have been moved to stock_transfer_entity.py
# The Warehouse relationships above still work via string references