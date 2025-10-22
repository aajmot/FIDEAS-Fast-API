from sqlalchemy.orm import Session
from app.db.models.admin_models.user_model import User
from app.db.repositories.base_repository import BaseRepository
from app.core.auth.password_utils import hash_password, verify_password

class UserService:
    def __init__(self, db: Session):
        self.repository = BaseRepository(User, db)
        self.db = db
    
    def authenticate(self, username: str, password: str):
        """Authenticate user with username and password"""
        user = self.db.query(User).filter(
            User.username == username,
            User.is_active == True,
            User.is_deleted == False
        ).first()
        
        if user and verify_password(password, user.hashed_password):
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'tenant_id': user.tenant_id,
                'is_tenant_admin': user.is_tenant_admin
            }
        return None
    
    def get_user_roles(self, user_id: int):
        """Get user roles"""
        return [{'name': 'Admin'}]
    
    def create(self, data):
        if 'password' in data:
            data['hashed_password'] = hash_password(data.pop('password'))
        return self.repository.create(data)
    
    def update(self, entity_id, data):
        if 'password' in data:
            data['hashed_password'] = hash_password(data.pop('password'))
        return self.repository.update(entity_id, data)
    
    def get_by_id(self, user_id):
        return self.repository.get(user_id)
    
    def get_all(self, skip=0, limit=100):
        return self.repository.get_all(skip, limit)
    
    def delete(self, user_id):
        return self.repository.delete(user_id)