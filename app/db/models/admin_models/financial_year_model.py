from sqlalchemy import Column, Integer, String, DateTime, Boolean
from app.db.models.base_model import BaseModel

class FinancialYear(BaseModel):
    __tablename__ = 'financial_years'
    
    name = Column(String(50), nullable=False)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    tenant_id = Column(Integer, nullable=False)
    is_closed = Column(Boolean, default=False)
    created_by = Column(String(100))
    updated_by = Column(String(100))