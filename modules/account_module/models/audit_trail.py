"""
Audit Trail Models for Accounting Module
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from datetime import datetime
from modules.inventory_module.models.entities import Base

class AuditTrail(Base):
    __tablename__ = 'audit_trail'
    
    id = Column(Integer, primary_key=True)
    entity_type = Column(String(50), nullable=False)  # VOUCHER, LEDGER, ACCOUNT, PAYMENT
    entity_id = Column(Integer, nullable=False)
    action = Column(String(20), nullable=False)  # CREATE, UPDATE, DELETE, POST, UNPOST, REVERSE
    old_value = Column(JSON)
    new_value = Column(JSON)
    user_id = Column(Integer, ForeignKey('users.id'))
    username = Column(String(100))
    ip_address = Column(String(50))
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    remarks = Column(Text)
