from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.types import Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.connection import Base

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey('categories.id'))
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_by = Column(String(100))
    
    parent = relationship("Category", remote_side=[id], backref="subcategories")
    products = relationship("Product", back_populates="category")

class Subcategory(Base):
    __tablename__ = 'subcategories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    category = relationship("Category")
    products = relationship("Product", back_populates="subcategory")

class Unit(Base):
    __tablename__ = 'units'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    symbol = Column(String(10))
    parent_id = Column(Integer, ForeignKey('units.id'))
    conversion_factor = Column(Numeric(10, 4), default=1.0)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    updated_by = Column(String(100))
    
    parent = relationship("Unit", remote_side=[id], backref="subunits")
    products = relationship("Product", back_populates="unit")

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)  # Brand or generic name
    code = Column(String(50), unique=True)
    composition = Column(Text)  # Salt composition
    tags = Column(Text)  # Store as comma-separated tags
    hsn_code = Column(String(20))  # HSN for GST
    schedule = Column(String(10))  # Schedule H, X, OTC etc.
    manufacturer = Column(String(200))  # Manufacturer name
    is_discontinued = Column(Boolean, default=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    subcategory_id = Column(Integer, ForeignKey('subcategories.id'))
    unit_id = Column(Integer, ForeignKey('units.id'), nullable=False)

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
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_by = Column(String(100))
    
    category = relationship("Category", back_populates="products")
    subcategory = relationship("Subcategory", back_populates="products")
    unit = relationship("Unit", back_populates="products")

    inventory_items = relationship("Inventory", back_populates="product")

class Customer(Base):
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(100))
    age = Column(Integer)
    address = Column(Text)
    tax_id = Column(String(50))
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_by = Column(String(100))
    
    sales_orders = relationship("SalesOrder", back_populates="customer")

class Supplier(Base):
    __tablename__ = 'suppliers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(100))
    tax_id = Column(String(50))
    address = Column(Text)
    contact_person = Column(String(100))
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_by = Column(String(100))

class Inventory(Base):
    __tablename__ = 'inventory'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False, default=0)
    reserved_quantity = Column(Numeric(10, 2), default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    product = relationship("Product", back_populates="inventory_items")

class SalesOrder(Base):
    __tablename__ = 'sales_orders'
    
    id = Column(Integer, primary_key=True)
    order_number = Column(String(50), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    agency_id = Column(Integer, ForeignKey('agencies.id'))
    order_date = Column(DateTime, default=datetime.utcnow)
    total_amount = Column(Numeric(10, 2), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    roundoff = Column(Numeric(10, 2), default=0)
    status = Column(String(20), default='pending')
    reversal_reason = Column(Text)
    reversed_at = Column(DateTime)
    reversed_by = Column(String(100))
    is_deleted = Column(Boolean, default=False)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_by = Column(String(100))
    
    customer = relationship("Customer", back_populates="sales_orders")
    order_items = relationship("SalesOrderItem", back_populates="sales_order")

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

class PurchaseOrder(Base):
    __tablename__ = 'purchase_orders'
    
    id = Column(Integer, primary_key=True)
    po_number = Column(String(50), unique=True, nullable=False)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow)
    total_amount = Column(Numeric(10, 2), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    roundoff = Column(Numeric(10, 2), default=0)
    status = Column(String(20), default='pending')
    reversal_reason = Column(Text)
    reversed_at = Column(DateTime)
    reversed_by = Column(String(100))
    is_deleted = Column(Boolean, default=False)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_by = Column(String(100))
    
    supplier = relationship("Supplier")
    order_items = relationship("PurchaseOrderItem", back_populates="purchase_order")

class PurchaseOrderItem(Base):
    __tablename__ = 'purchase_order_items'
    
    id = Column(Integer, primary_key=True)
    purchase_order_id = Column(Integer, ForeignKey('purchase_orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    batch_number = Column(String(50))
    quantity = Column(Numeric(10, 2), nullable=False)
    free_quantity = Column(Numeric(10, 2), default=0)
    unit_price = Column(Numeric(10, 2), nullable=False)
    mrp = Column(Numeric(10, 2), nullable=False)
    gst_rate = Column(Numeric(5, 2), default=0)
    cgst_rate = Column(Numeric(5, 2), default=0)
    sgst_rate = Column(Numeric(5, 2), default=0)
    discount_percent = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    total_amount = Column(Numeric(10, 2), nullable=False)
    
    purchase_order = relationship("PurchaseOrder", back_populates="order_items")
    product = relationship("Product")

class SalesOrderItem(Base):
    __tablename__ = 'sales_order_items'
    
    id = Column(Integer, primary_key=True)
    sales_order_id = Column(Integer, ForeignKey('sales_orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    batch_number = Column(String(50))
    quantity = Column(Numeric(10, 2), nullable=False)
    free_quantity = Column(Numeric(10, 2), default=0)
    unit_price = Column(Numeric(10, 2), nullable=False)
    gst_rate = Column(Numeric(5, 2), default=0)
    cgst_rate = Column(Numeric(5, 2), default=0)
    sgst_rate = Column(Numeric(5, 2), default=0)
    discount_percent = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    total_price = Column(Numeric(10, 2), nullable=False)
    
    sales_order = relationship("SalesOrder", back_populates="order_items")
    product = relationship("Product")

class ProductWaste(Base):
    __tablename__ = 'product_waste'
    
    id = Column(Integer, primary_key=True)
    waste_number = Column(String(50), unique=True, nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    batch_number = Column(String(50))
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_cost = Column(Numeric(10, 2), nullable=False)
    total_cost = Column(Numeric(10, 2), nullable=False)
    reason = Column(String(500), nullable=False)
    waste_date = Column(DateTime, default=datetime.utcnow)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    
    product = relationship("Product")

class StockMeter(Base):
    __tablename__ = 'stock_meter'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    location = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    product = relationship("Product")