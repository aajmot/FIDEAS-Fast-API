from core.database.connection import db_manager
from core.shared.utils.session_manager import session_manager

class BaseService:
    def __init__(self, model_class):
        self.model_class = model_class
    
    def create(self, data):
        with db_manager.get_session() as session:
            # Add tenant_id if model has it and not provided
            if hasattr(self.model_class, 'tenant_id') and 'tenant_id' not in data:
                data['tenant_id'] = session_manager.get_current_tenant_id()
            
            # Add created_by if model has it and not provided
            if hasattr(self.model_class, 'created_by') and 'created_by' not in data:
                data['created_by'] = session_manager.get_current_username()
            
            instance = self.model_class(**data)
            session.add(instance)
            session.commit()
            return instance
    
    def get_by_id(self, id):
        with db_manager.get_session() as session:
            return session.query(self.model_class).filter(self.model_class.id == id).first()
    
    def get_all(self, tenant_id=None):
        with db_manager.get_session() as session:
            query = session.query(self.model_class)
            if hasattr(self.model_class, 'tenant_id') and tenant_id:
                query = query.filter(self.model_class.tenant_id == tenant_id)
            return query.all()
    
    def update(self, id, data):
        with db_manager.get_session() as session:
            instance = session.query(self.model_class).filter(self.model_class.id == id).first()
            if instance:
                for key, value in data.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)
                session.commit()
            return instance
    
    def delete(self, id):
        with db_manager.get_session() as session:
            instance = session.query(self.model_class).filter(self.model_class.id == id).first()
            if instance:
                session.delete(instance)
                session.commit()
            return instance