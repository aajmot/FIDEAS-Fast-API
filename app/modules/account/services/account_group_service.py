from sqlalchemy.orm import Session
from app.db.models.accounting_models.account_model import AccountGroup
from app.modules.shared.services.base_service import BaseService

class AccountGroupService(BaseService):
    def __init__(self, db: Session):
        super().__init__(AccountGroup, db)