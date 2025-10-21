from core.shared.services.base_service import BaseService
from modules.inventory_module.models.entities import Unit

class UnitService(BaseService):
    def __init__(self):
        super().__init__(Unit)