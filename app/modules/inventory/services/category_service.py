from sqlalchemy.orm import Session
from app.db.models.inventory_models.category_model import Category
from app.db.repositories.base_repository import BaseRepository

class CategoryService:
    def __init__(self, db: Session):
        self.repository = BaseRepository(Category, db)
    
    def create(self, data):
        return self.repository.create(data)
    
    def update(self, entity_id, data):
        return self.repository.update(entity_id, data)
    
    def get_by_id(self, category_id):
        return self.repository.get(category_id)
    
    def get_all(self, skip=0, limit=100):
        return self.repository.get_all(skip, limit)
    
    def delete(self, category_id):
        return self.repository.delete(category_id)