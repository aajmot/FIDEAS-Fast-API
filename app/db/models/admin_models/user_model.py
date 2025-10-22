from sqlalchemy import Column, String, Integer, Boolean
from app.db.models.base_model import BaseModel


class User(BaseModel):
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    tenant_id = Column(Integer, nullable=False)
    is_tenant_admin = Column(Boolean, default=False)