from sqlalchemy.orm import Session
from app.db.models.accounting_models.account_model import AccountMaster
from app.modules.shared.services.base_service import BaseService

class AccountMasterService(BaseService):
    def __init__(self, db: Session):
        super().__init__(AccountMaster, db)