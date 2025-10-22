from sqlalchemy.orm import Session
from app.modules.accounting.models.account import AccountMaster, AccountGroup
from app.db.repositories.base_repository import BaseRepository

class AccountService:
    def __init__(self, db: Session):
        self.repository = BaseRepository(AccountMaster, db)
        self.group_repository = BaseRepository(AccountGroup, db)
    
    def create_account(self, account_data: dict):
        return self.repository.create(account_data)
    
    def create_account_group(self, group_data: dict):
        return self.group_repository.create(group_data)
    
    def get_accounts_by_group(self, group_id: int):
        return self.repository.db.query(AccountMaster).filter(AccountMaster.account_group_id == group_id).all()