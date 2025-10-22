from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from app.db.base import get_db
from app.core.auth.oauth2_scheme import get_current_user
from app.core.utils.api_response import APIResponse
from app.db.models.accounting_models.accounting_model import Account, Transaction
from app.db.repositories.base_repository import BaseRepository

router = APIRouter()


class AccountCreate(BaseModel):
    name: str
    code: str
    account_type: str
    balance: float = 0


class AccountResponse(BaseModel):
    id: int
    name: str
    code: str
    account_type: str
    balance: float
    
    class Config:
        from_attributes = True


class TransactionCreate(BaseModel):
    description: str
    amount: float
    transaction_type: str
    transaction_date: datetime
    account_id: int


class TransactionResponse(BaseModel):
    id: int
    description: str
    amount: float
    transaction_type: str
    transaction_date: datetime
    account_id: int
    
    class Config:
        from_attributes = True


@router.get("/accounts", response_model=List[AccountResponse], tags=["Accounting - Accounts"])
async def get_accounts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all accounts"""
    repo = BaseRepository(Account, db)
    accounts = repo.get_all()
    return accounts


@router.post("/accounts", response_model=AccountResponse, tags=["Accounting - Accounts"])
async def create_account(
    account: AccountCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new account"""
    repo = BaseRepository(Account, db)
    created_account = repo.create(account.dict())
    return created_account


@router.get("/transactions", response_model=List[TransactionResponse], tags=["Accounting - Transactions"])
async def get_transactions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all transactions"""
    repo = BaseRepository(Transaction, db)
    transactions = repo.get_all()
    return transactions


@router.post("/transactions", response_model=TransactionResponse, tags=["Accounting - Transactions"])
async def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new transaction"""
    repo = BaseRepository(Transaction, db)
    created_transaction = repo.create(transaction.dict())
    return created_transaction