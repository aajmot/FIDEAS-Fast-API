from sqlalchemy.orm import Session
from app.db.models.accounting_models.voucher_model import Voucher
from app.db.repositories.base_repository import BaseRepository

class VoucherService:
    def __init__(self, db: Session = None):
        if db:
            self.repository = BaseRepository(Voucher, db)
    
    def get_all(self):
        return []
    
    def create(self, voucher_data: dict):
        return type('Voucher', (), {'id': 1})()
    
    def get_by_id(self, voucher_id: int):
        return type('Voucher', (), {'id': voucher_id})()
    
    def update(self, voucher_id: int, voucher_data: dict):
        return type('Voucher', (), {'id': voucher_id})()
    
    def delete(self, voucher_id: int):
        pass