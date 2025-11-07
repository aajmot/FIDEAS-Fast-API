from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from modules.inventory_module.models.entities import Base

class AccountConfiguration(Base):
    """
    Tenant-specific account configurations.
    Maps global configuration keys to tenant-specific accounts.
    """
    __tablename__ = 'account_configurations'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    config_key_id = Column(Integer, ForeignKey('account_configuration_keys.id', ondelete='RESTRICT'), nullable=False)
    account_id = Column(Integer, ForeignKey('account_masters.id', ondelete='RESTRICT'), nullable=False)
    
    # Optional: Module-specific (e.g. PURCHASE, SALES, INVENTORY)
    module = Column(String(30))
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    # config_key = relationship("AccountConfigurationKey", foreign_keys=[config_key_id])
    # account = relationship("AccountMaster", foreign_keys=[account_id])
    
    def __repr__(self):
        return f"<AccountConfiguration(id={self.id}, tenant_id={self.tenant_id}, config_key_id={self.config_key_id}, account_id={self.account_id})>"
