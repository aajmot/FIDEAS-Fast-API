from typing import Optional, List
from modules.admin_module.models.entities import User, UserRole, Role
from modules.admin_module.services.base_service import BaseService
from core.database.connection import db_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware

class UserService(BaseService):
    def __init__(self):
        super().__init__(User)
    
    @ExceptionMiddleware.handle_exceptions("UserService")
    def authenticate(self, username: str, password: str) -> Optional[dict]:
        with db_manager.get_session() as session:
            user = session.query(User).filter(
                User.username == username,
                User.is_active == True
            ).first()
            
            if user and user.check_password(password):
                # Return user data as dict to avoid session issues
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
    
    @ExceptionMiddleware.handle_exceptions("UserService")
    def get_user_roles(self, user_id: int) -> List[dict]:
        with db_manager.get_session() as session:
            roles = session.query(Role).join(UserRole).filter(
                UserRole.user_id == user_id
            ).all()
            # Return role data as dictionaries to avoid session issues
            return [{
                'id': role.id,
                'name': role.name,
                'description': role.description
            } for role in roles]
    
    @ExceptionMiddleware.handle_exceptions("UserService")
    def create(self, data: dict) -> int:
        from core.shared.utils.session_manager import session_manager
        # Work on a copy to avoid mutating the caller's dict (route relies on it)
        payload = dict(data)

        # Extract and handle password and role_ids separately
        password = payload.pop('password', None)
        payload.pop('role_ids', None)

        # Add tenant and user tracking to the payload if missing
        if 'tenant_id' not in payload:
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                payload['tenant_id'] = tenant_id

        if 'created_by' not in payload:
            username = session_manager.get_current_username()
            if username:
                payload['created_by'] = username

        with db_manager.get_session() as session:
            user = User(**payload)
            if password:
                user.set_password(password)
            session.add(user)
            session.flush()
            user_id = user.id
            return user_id
    
    @ExceptionMiddleware.handle_exceptions("UserService")
    def assign_role(self, user_id: int, role_id: int, assigned_by: int) -> bool:
        from core.shared.utils.session_manager import session_manager
        
        with db_manager.get_session() as session:
            existing = session.query(UserRole).filter(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id
            ).first()
            
            if not existing:
                user_role = UserRole(
                    user_id=user_id,
                    role_id=role_id,
                    tenant_id=session_manager.get_current_tenant_id() or 1,
                    assigned_by=assigned_by,
                    created_by=session_manager.get_current_username() or 'system'
                )
                session.add(user_role)
                return True
            return False