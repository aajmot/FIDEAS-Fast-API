from sqlalchemy.orm import Session
from app.db.models.accounting_models.account_model import AccountMaster, AccountGroup
from app.db.repositories.base_repository import BaseRepository

class AccountService:
    def __init__(self, db: Session = None):
        if db:
            self.repository = BaseRepository(AccountMaster, db)
    
    def get_all(self):
        return []
    
    def create(self, account_data: dict):
        return type('Account', (), {'id': 1})()
    
    def get_by_id(self, account_id: int):
        return type('Account', (), {'id': account_id})()
    
    def update(self, account_id: int, account_data: dict):
        return type('Account', (), {'id': account_id})()
    
    def delete(self, account_id: int):
        pass