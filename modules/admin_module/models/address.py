from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.connection import Base


class Address(Base):
    """Address entity for polymorphic relationships with customers, suppliers, warehouses, etc."""
    __tablename__ = 'addresses'
    __table_args__ = (
        UniqueConstraint('tenant_id', 'entity_type', 'entity_id', 'address_type', 'is_deleted', 
                        name='uq_entity_address', deferrable=True, initially='DEFERRED'),
        CheckConstraint(
            "entity_type IN ('CUSTOMER', 'SUPPLIER', 'WAREHOUSE', 'EMPLOYEE', 'BRANCH', 'OTHER')",
            name='chk_entity_type'
        ),
        CheckConstraint(
            "address_type IN ('BILLING', 'SHIPPING', 'WAREHOUSE', 'REGISTERED')",
            name='chk_address_type'
        ),
        CheckConstraint(
            "gstin IS NULL OR gstin ~ '^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'",
            name='chk_gstin_format'
        ),
        CheckConstraint(
            "country != 'India' OR pincode ~ '^[1-9][0-9]{5}$'",
            name='chk_pincode_india'
        ),
        CheckConstraint(
            "NOT (is_default_billing AND is_default_shipping) OR (entity_type IN ('CUSTOMER', 'SUPPLIER'))",
            name='chk_default_uniqueness'
        ),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    
    # Polymorphic link to any entity
    entity_type = Column(String(30), nullable=False)
    entity_id = Column(Integer, nullable=False)
    
    # Address Type
    address_type = Column(String(20), nullable=False, default='BILLING')
    
    # Core Address
    address_line1 = Column(String(200), nullable=False)
    address_line2 = Column(String(200))
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False, default='India')
    pincode = Column(String(20), nullable=False)
    
    # GST & Compliance
    gstin = Column(String(15))  # 15-digit GSTIN
    state_code = Column(String(2))  # e.g. '27' for MH
    is_gst_registered = Column(Boolean, default=False)
    
    # Contact
    contact_person = Column(String(100))
    phone = Column(String(20))
    email = Column(String(100))
    
    # Default Flags
    is_default_billing = Column(Boolean, default=False)
    is_default_shipping = Column(Boolean, default=False)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
