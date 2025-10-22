from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.models.base_model import BaseModel


class Account(BaseModel):
    __tablename__ = "accounts"
    
    name = Column(String(100), nullable=False)
    code = Column(String(20))
    account_type = Column(String(50), nullable=False)
    balance = Column(Numeric(15, 2))
    tenant_id = Column(Integer, ForeignKey('tenants.id'))
    
    # Relationship
    transactions = relationship("Transaction", back_populates="account")


class Transaction(BaseModel):
    __tablename__ = "transactions"
    
    description = Column(String(255), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    transaction_type = Column(String(10), nullable=False)
    transaction_date = Column(DateTime, nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    tenant_id = Column(Integer, ForeignKey('tenants.id'))
    
    # Relationship
    account = relationship("Account", back_populates="transactions")