from sqlalchemy.orm import Session
from app.db.models.diagnostics_models.test_model import TestPanel
from app.db.repositories.base_repository import BaseRepository

class TestPanelService:
    def __init__(self, db: Session):
        self.repository = BaseRepository(TestPanel, db)
    
    def create(self, data):
        return self.repository.create(data)
    
    def update(self, entity_id, data):
        return self.repository.update(entity_id, data)
    
    def get_by_id(self, panel_id):
        return self.repository.get(panel_id)
    
    def get_all(self, skip=0, limit=100):
        return self.repository.get_all(skip, limit)
    
    def delete(self, panel_id):
        return self.repository.delete(panel_id)