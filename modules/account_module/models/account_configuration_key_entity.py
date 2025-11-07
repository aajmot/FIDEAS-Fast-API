from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from modules.inventory_module.models.entities import Base

class AccountConfigurationKey(Base):
    """
    Global configuration keys for account mappings.
    These are system-wide configuration options (e.g., CASH, BANK, INVENTORY, GST_OUTPUT).
    Each tenant can map these keys to their specific accounts via AccountConfiguration.
    """
    __tablename__ = 'account_configuration_keys'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Default account (global fallback)
    default_account_id = Column(Integer, ForeignKey('account_masters.id', ondelete='SET NULL'))
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    default_account = relationship("AccountMaster", foreign_keys=[default_account_id])
    # configurations = relationship("AccountConfiguration", back_populates="config_key")
    
    def __repr__(self):
        return f"<AccountConfigurationKey(id={self.id}, code='{self.code}', name='{self.name}')>"
