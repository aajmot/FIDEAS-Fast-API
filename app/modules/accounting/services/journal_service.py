from sqlalchemy.orm import Session
from app.db.models.accounting_models.journal_model import Journal
from app.modules.shared.services.base_service import BaseService

class JournalService(BaseService):
    def __init__(self, db: Session):
        super().__init__(Journal, db)