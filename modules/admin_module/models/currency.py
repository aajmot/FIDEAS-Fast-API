
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Numeric, UniqueConstraint, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from modules.inventory_module.models.entities import Base

class Currency(Base):
    __tablename__ = 'currencies'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(3), nullable=False, unique=True)
    name = Column(String(50), nullable=False)
    symbol = Column(String(5))
    is_base = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ExchangeRate(Base):
    __tablename__ = 'exchange_rates'
    
    id = Column(Integer, primary_key=True)
    from_currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    to_currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    rate = Column(Numeric(15, 6), nullable=False)
    effective_date = Column(Date, nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    from_currency = relationship("Currency", foreign_keys=[from_currency_id])
    to_currency = relationship("Currency", foreign_keys=[to_currency_id])
    
    __table_args__ = (
        UniqueConstraint('from_currency_id', 'to_currency_id', 'effective_date', 'tenant_id', name='uq_exchange_rate'),
    )
