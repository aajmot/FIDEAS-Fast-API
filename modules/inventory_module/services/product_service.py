from modules.inventory_module.models.entities import Product
from modules.admin_module.services.base_service import BaseService

class ProductService(BaseService):
    def __init__(self):
        super().__init__(Product)
    
    def create(self, data):
        # Validate commission_type
        commission_type = data.get('commission_type')
        if commission_type and commission_type not in [None, '', 'Percentage', 'Fixed']:
            raise ValueError("commission_type must be null/empty, 'Percentage', or 'Fixed'")
        return super().create(data)
    
    def update(self, entity_id, data):
        # Validate commission_type
        commission_type = data.get('commission_type')
        if commission_type and commission_type not in [None, '', 'Percentage', 'Fixed']:
            raise ValueError("commission_type must be null/empty, 'Percentage', or 'Fixed'")
        return super().update(entity_id, data)