from typing import Optional
from core.shared.utils.session_manager import SessionManager
from core.database.connection import db_manager
from modules.admin_module.models.entities import User, UserRole, Role
from sqlalchemy import and_, or_

class AuthUtils:
    
    @staticmethod
    def is_admin_user(user_id: Optional[int] = None, tenant_id: Optional[int] = None) -> bool:
        """Check if current or specified user is admin"""
        if not user_id or not tenant_id:
            session_data = SessionManager.get_session_data()
            user_id = user_id or session_data.get('user_id')
            tenant_id = tenant_id or session_data.get('tenant_id')
        
        if not user_id or not tenant_id:
            return False
        
        try:
            with db_manager.get_session() as session:
                # Get user roles
                user_roles = session.query(UserRole).filter_by(
                    user_id=user_id, 
                    tenant_id=tenant_id
                ).all()
                
                if not user_roles:
                    return False
                
                role_ids = [ur.role_id for ur in user_roles]
                
                # Check if any role is admin
                admin_roles = session.query(Role).filter(
                    and_(
                        Role.id.in_(role_ids),
                        or_(
                            Role.name.ilike('%admin%'),
                            Role.name.ilike('admin'),
                            Role.name == 'Admin'
                        ),
                        Role.tenant_id == tenant_id
                    )
                ).all()
                
                return len(admin_roles) > 0
        except Exception:
            return False
    
    @staticmethod
    def get_current_user_id() -> Optional[int]:
        """Get current user ID from session"""
        session_data = SessionManager.get_session_data()
        return session_data.get('user_id')
    
    @staticmethod
    def get_current_tenant_id() -> Optional[int]:
        """Get current tenant ID from session"""
        session_data = SessionManager.get_session_data()
        return session_data.get('tenant_id')