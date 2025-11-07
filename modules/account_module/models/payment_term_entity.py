from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.connection import Base


class PaymentTerm(Base):
    """Payment Terms - defines credit periods for customers/suppliers"""
    __tablename__ = 'payment_terms'
    __table_args__ = (
        UniqueConstraint('code', 'tenant_id', name='uq_payment_term_code_tenant'),
        CheckConstraint("TRIM(code) <> ''", name='chk_code_not_empty'),
        CheckConstraint('days >= 0', name='chk_days_non_negative'),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    
    # Payment term details
    code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    days = Column(Integer, nullable=False)  # Credit period in days
    description = Column(Text)
    
    # Status
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
