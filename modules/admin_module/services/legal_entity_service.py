from modules.admin_module.models.entities import LegalEntity
from modules.admin_module.services.base_service import BaseService

class LegalEntityService(BaseService):
    def __init__(self):
        super().__init__(LegalEntity)