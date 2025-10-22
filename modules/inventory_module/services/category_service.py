from modules.inventory_module.models.entities import Category
from modules.admin_module.services.base_service import BaseService

class CategoryService(BaseService):
    def __init__(self):
        super().__init__(Category)