from sqlalchemy import Column, Integer, String, Text
from app.db.models.base_model import BaseModel

class Tenant(BaseModel):
    __tablename__ = 'tenants'
    
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=False, unique=True)
    description = Column(Text)
    logo = Column(String(255))
    tagline = Column(String(255))
    address = Column(Text)
    business_type = Column(String(20), default='TRADING')

class TenantSetting(BaseModel):
    __tablename__ = 'tenant_settings'
    
    tenant_id = Column(Integer, nullable=False)
    setting = Column(Text, nullable=False)
    description = Column(Text)
    value_type = Column(Text, default='BOOLEAN')
    value = Column(Text, default='TRUE')
    created_by = Column(String(100))
    updated_by = Column(String(100))