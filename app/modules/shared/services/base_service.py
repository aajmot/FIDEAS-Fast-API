from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

class BaseService:
    def __init__(self, model_class, db: Session):
        self.model_class = model_class
        self.db = db
    
    def create(self, data: Dict[str, Any]) -> Any:
        for key, value in list(data.items()):
            if value == '':
                data[key] = None
        
        entity = self.model_class(**data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def get_by_id(self, entity_id: int) -> Optional[Any]:
        return self.db.query(self.model_class).filter(self.model_class.id == entity_id).first()
    
    def get_all(self, filters: Dict[str, Any] = None) -> List[Any]:
        query = self.db.query(self.model_class)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.filter(getattr(self.model_class, key) == value)
        
        return query.all()
    
    def update(self, entity_id: int, data: Dict[str, Any]) -> Optional[Any]:
        for key, value in list(data.items()):
            if value == '':
                data[key] = None
        
        entity = self.db.query(self.model_class).filter(self.model_class.id == entity_id).first()
        if entity:
            for key, value in data.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            self.db.commit()
            self.db.refresh(entity)
            return entity
        return None
    
    def delete(self, entity_id: int) -> bool:
        entity = self.db.query(self.model_class).filter(self.model_class.id == entity_id).first()
        if entity:
            self.db.delete(entity)
            self.db.commit()
            return True
        return False