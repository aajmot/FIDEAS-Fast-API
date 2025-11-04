from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.types import Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.connection import Base

# Keep inventory and product batch in this file; other entities moved to separate modules

class Inventory(Base):
    __tablename__ = 'inventory'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False, default=0)
    reserved_quantity = Column(Numeric(10, 2), default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    product = relationship("Product", back_populates="inventory_items")

class ProductBatch(Base):
    __tablename__ = 'product_batches'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    batch_number = Column(String(50), nullable=False)
    expiry_date = Column(DateTime)
    mrp = Column(Numeric(10, 2), nullable=False)
    purchase_rate = Column(Numeric(10, 2), nullable=False)
    sale_rate = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    gst_percentage = Column(Numeric(5, 2), default=0)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_by = Column(String(100))
    
    product = relationship("Product")
    supplier = relationship("Supplier")

# Import the moved entities so external imports that expect them from
# this module continue to work (keeps backwards compatibility).
from .product_entity import Product
from .sales_order_entity import SalesOrder, SalesOrderItem
from .purchase_order_entity import PurchaseOrder, PurchaseOrderItem
from .customer_entity import Customer
from .supplier_entity import Supplier
from .product_waste_entity import ProductWaste
from .stock_meter_entity import StockMeter
from .category_entity import Category
from .unit_entity import Unit
from .hsn_entity import HsnCode
from .stock_entity import StockTransaction, StockBalance
from .warehouse_entity import Warehouse, StockByLocation
from .stock_transfer_entity import StockTransfer, StockTransferItem