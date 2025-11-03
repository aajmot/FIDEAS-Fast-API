from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, UniqueConstraint
from datetime import datetime
from core.database.connection import Base


class HsnCode(Base):
    __tablename__ = 'hsn_codes'
    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_hsn_tenant_code'),
    )

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<HsnCode id={self.id} code={self.code} tenant={self.tenant_id}>"
