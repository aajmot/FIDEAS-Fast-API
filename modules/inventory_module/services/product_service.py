from modules.inventory_module.models.entities import Product
from modules.admin_module.services.base_service import BaseService


class ProductService(BaseService):
    def __init__(self):
        super().__init__(Product)

    def _normalize_commission_type(self, commission_type):
        if commission_type is None:
            return None
        if isinstance(commission_type, str):
            ct = commission_type.strip().upper()
            if ct == 'PERCENTAGE':
                return 'PERCENTAGE'
            if ct == 'FIXED':
                return 'FIXED'
        return commission_type

    def create(self, data):
        # Normalize/validate commission_type to match DB enum values (FIXED/PERCENTAGE)
        commission_type = data.get('commission_type')
        if commission_type:
            ct = self._normalize_commission_type(commission_type)
            if ct not in ['FIXED', 'PERCENTAGE']:
                raise ValueError("commission_type must be 'FIXED' or 'PERCENTAGE'")
            data['commission_type'] = ct

        # Accept legacy 'price' / 'gst_percentage' fields by mapping them to new names if present
        if 'price' in data and 'selling_price' not in data:
            data['selling_price'] = data.pop('price')
        if 'gst_percentage' in data and 'gst_rate' not in data:
            data['gst_rate'] = data.pop('gst_percentage')

        return super().create(data)

    def update(self, entity_id, data):
        commission_type = data.get('commission_type')
        if commission_type:
            ct = self._normalize_commission_type(commission_type)
            if ct not in ['FIXED', 'PERCENTAGE']:
                raise ValueError("commission_type must be 'FIXED' or 'PERCENTAGE'")
            data['commission_type'] = ct

        # Map legacy fields when updating
        if 'price' in data and 'selling_price' not in data:
            data['selling_price'] = data.pop('price')
        if 'gst_percentage' in data and 'gst_rate' not in data:
            data['gst_rate'] = data.pop('gst_percentage')

        return super().update(entity_id, data)