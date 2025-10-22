from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, Numeric, DateTime, UniqueConstraint
from app.db.models.base_model import BaseModel

class VoucherType(BaseModel):
    __tablename__ = 'voucher_types'
    
    name = Column(String(50), nullable=False)
    code = Column(String(10), nullable=False)
    prefix = Column(String(10))
    tenant_id = Column(Integer, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('code', 'tenant_id', name='uq_voucher_type_code_tenant'),
    )

class Voucher(BaseModel):
    __tablename__ = 'vouchers'
    
    voucher_number = Column(String(50), unique=True, nullable=False)
    voucher_type_id = Column(Integer, nullable=False)
    voucher_date = Column(DateTime, nullable=False)
    reference_type = Column(String(20))
    reference_id = Column(Integer)
    reference_number = Column(String(50))
    narration = Column(Text)
    total_amount = Column(Numeric(15, 2), nullable=False)
    currency_id = Column(Integer)
    exchange_rate = Column(Numeric(15, 6), default=1)
    base_currency_amount = Column(Numeric(15, 2))
    reversed_voucher_id = Column(Integer)
    reversal_voucher_id = Column(Integer)
    is_reversal = Column(Boolean, default=False)
    is_posted = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    tenant_id = Column(Integer, nullable=False)
    created_by = Column(String(100))