from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from core.database.connection import db_manager
from core.shared.utils.logger import logger
from core.shared.middleware.exception_handler import ExceptionMiddleware

class BaseService(ABC):
    def __init__(self, model_class):
        self.model_class = model_class
        self.module_name = self.__class__.__name__
    
    @ExceptionMiddleware.handle_exceptions()
    def create(self, data: Dict[str, Any]) -> Any:
        from core.shared.utils.session_manager import session_manager
        
        # Convert empty strings to None for nullable integer fields
        for key, value in list(data.items()):
            if value == '':
                data[key] = None
        
        # Add tenant and user tracking if columns exist
        if hasattr(self.model_class, 'tenant_id') and 'tenant_id' not in data:
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                data['tenant_id'] = tenant_id
        
        if hasattr(self.model_class, 'created_by'):
            username = session_manager.get_current_username()
            if username:
                data['created_by'] = username
        
        with db_manager.get_session() as session:
            entity = self.model_class(**data)
            session.add(entity)
            session.flush()
            session.refresh(entity)
            # Access id to ensure it's loaded before session closes
            entity_id = entity.id
            logger.info(f"Created {self.model_class.__name__} with ID: {entity_id}", self.module_name)
            return entity
    
    @ExceptionMiddleware.handle_exceptions()
    def get_by_id(self, entity_id: int) -> Optional[Any]:
        with db_manager.get_session() as session:
            entity = session.query(self.model_class).filter(self.model_class.id == entity_id).first()
            if entity:
                logger.info(f"Retrieved {self.model_class.__name__} with ID: {entity_id}", self.module_name)
            return entity
    
    @ExceptionMiddleware.handle_exceptions()
    def get_all(self, filters: Dict[str, Any] = None) -> List[Any]:
        from core.shared.utils.session_manager import session_manager
        
        with db_manager.get_session() as session:
            query = session.query(self.model_class)
            
            # Auto-filter by tenant if column exists
            if hasattr(self.model_class, 'tenant_id'):
                tenant_id = session_manager.get_current_tenant_id()
                if tenant_id:
                    query = query.filter(self.model_class.tenant_id == tenant_id)
            
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model_class, key):
                        query = query.filter(getattr(self.model_class, key) == value)
            entities = query.all()
            logger.info(f"Retrieved {len(entities)} {self.model_class.__name__} records", self.module_name)
            return entities
    
    @ExceptionMiddleware.handle_exceptions()
    def update(self, entity_id: int, data: Dict[str, Any]) -> Optional[Any]:
        from core.shared.utils.session_manager import session_manager
        
        # Convert empty strings to None for nullable integer fields
        for key, value in list(data.items()):
            if value == '':
                data[key] = None
        
        # Add user tracking for updates
        if hasattr(self.model_class, 'updated_by'):
            username = session_manager.get_current_username()
            if username:
                data['updated_by'] = username
        
        with db_manager.get_session() as session:
            entity = session.query(self.model_class).filter(self.model_class.id == entity_id).first()
            if entity:
                for key, value in data.items():
                    if hasattr(entity, key):
                        setattr(entity, key, value)
                session.flush()
                session.refresh(entity)
                logger.info(f"Updated {self.model_class.__name__} with ID: {entity_id}", self.module_name)
                return entity
            return None
    
    @ExceptionMiddleware.handle_exceptions()
    def delete(self, entity_id: int) -> bool:
        with db_manager.get_session() as session:
            entity = session.query(self.model_class).filter(self.model_class.id == entity_id).first()
            if entity:
                session.delete(entity)
                logger.info(f"Deleted {self.model_class.__name__} with ID: {entity_id}", self.module_name)
                return True
            return False