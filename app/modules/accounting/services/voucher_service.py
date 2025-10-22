from sqlalchemy.orm import Session
from app.db.models.accounting_models.voucher_model import Voucher
from app.modules.shared.services.base_service import BaseService

class VoucherService(BaseService):
    def __init__(self, db: Session):
        super().__init__(Voucher, db)