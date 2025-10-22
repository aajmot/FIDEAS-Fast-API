from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.db.models.base_model import BaseModel

class UserRole(BaseModel):
    __tablename__ = 'user_roles'
    
    user_id = Column(Integer, nullable=False)
    role_id = Column(Integer, nullable=False)
    tenant_id = Column(Integer, nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    assigned_by = Column(Integer)
    created_by = Column(String(100))