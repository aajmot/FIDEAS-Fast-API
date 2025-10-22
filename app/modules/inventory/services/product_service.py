from sqlalchemy.orm import Session
from app.db.models.inventory_models.product_model import Product
from app.db.repositories.base_repository import BaseRepository

class ProductService:
    def __init__(self, db: Session):
        self.repository = BaseRepository(Product, db)
    
    def create(self, data):
        commission_type = data.get('commission_type')
        if commission_type and commission_type not in [None, '', 'Percentage', 'Fixed']:
            raise ValueError("commission_type must be null/empty, 'Percentage', or 'Fixed'")
        return self.repository.create(data)
    
    def update(self, entity_id, data):
        commission_type = data.get('commission_type')
        if commission_type and commission_type not in [None, '', 'Percentage', 'Fixed']:
            raise ValueError("commission_type must be null/empty, 'Percentage', or 'Fixed'")
        return self.repository.update(entity_id, data)
    
    def get_by_id(self, product_id):
        return self.repository.get(product_id)
    
    def get_all(self, skip=0, limit=100):
        return self.repository.get_all(skip, limit)
    
    def delete(self, product_id):
        return self.repository.delete(product_id)