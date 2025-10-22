from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db.models.admin_models.user_role_model import UserRole
from app.db.models.admin_models.role_model import Role
from app.db.models.admin_models.user_model import User

class UserRoleService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_role_mappings_paginated(self, tenant_id: int, search: str = None, offset: int = 0, limit: int = 10):
        query = self.db.query(Role).join(UserRole).filter(
            Role.tenant_id == tenant_id
        ).distinct()
        
        if search:
            query = query.filter(or_(
                Role.name.ilike(f"%{search}%"),
                Role.description.ilike(f"%{search}%")
            ))
        
        total = query.count()
        roles = query.offset(offset).limit(limit).all()
        
        role_data = []
        for role in roles:
            user_mappings = self.db.query(UserRole, User).join(
                User, UserRole.user_id == User.id
            ).filter(UserRole.role_id == role.id).all()
            
            users = [{
                "mapping_id": mapping.UserRole.id,
                "user_id": mapping.User.id,
                "username": mapping.User.username,
                "full_name": f"{mapping.User.first_name} {mapping.User.last_name}"
            } for mapping in user_mappings]
            
            role_data.append({
                "role_id": role.id,
                "role_name": role.name,
                "role_description": role.description,
                "user_count": len(users),
                "users": users
            })
        
        return role_data, total
    
    def get_role_users(self, role_id: int):
        user_mappings = self.db.query(UserRole, User).join(
            User, UserRole.user_id == User.id
        ).filter(UserRole.role_id == role_id).all()
        
        return [{
            "user_id": mapping.User.id,
            "username": mapping.User.username,
            "full_name": f"{mapping.User.first_name} {mapping.User.last_name}"
        } for mapping in user_mappings]
    
    def create_mapping(self, user_id: int, role_id: int, tenant_id: int, created_by: str):
        existing = self.db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id
        ).first()
        
        if existing:
            return None
        
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            tenant_id=tenant_id,
            created_by=created_by
        )
        self.db.add(user_role)
        self.db.commit()
        self.db.refresh(user_role)
        return user_role
    
    def delete_mapping(self, mapping_id: int):
        mapping = self.db.query(UserRole).filter(UserRole.id == mapping_id).first()
        if mapping:
            self.db.delete(mapping)
            self.db.commit()
            return True
        return False
    
    def bulk_delete_mappings(self, mapping_ids: List[int]):
        deleted_count = self.db.query(UserRole).filter(UserRole.id.in_(mapping_ids)).delete(synchronize_session=False)
        self.db.commit()
        return deleted_count
    
    def delete_all_role_users(self, role_id: int):
        deleted_count = self.db.query(UserRole).filter(UserRole.role_id == role_id).delete()
        self.db.commit()
        return deleted_count
    
    def update_role_users(self, role_id: int, user_ids: List[int], tenant_id: int, created_by: str):
        # Delete existing mappings
        self.db.query(UserRole).filter(UserRole.role_id == role_id).delete()
        
        # Create new mappings
        for user_id in user_ids:
            user_role = UserRole(
                user_id=user_id,
                role_id=role_id,
                tenant_id=tenant_id,
                created_by=created_by
            )
            self.db.add(user_role)
        
        self.db.commit()
    
    def import_mappings(self, mappings_data: List[Dict], tenant_id: int, created_by: str):
        imported_count = 0
        
        for mapping in mappings_data:
            role_name = mapping.get("role_name", "").strip()
            usernames = [u.strip() for u in mapping.get("usernames", "").split(",") if u.strip()]
            
            if not role_name or not usernames:
                continue
            
            # Find role
            role = self.db.query(Role).filter(
                Role.name == role_name,
                Role.tenant_id == tenant_id
            ).first()
            
            if not role:
                continue
            
            # Clear existing mappings for this role
            self.db.query(UserRole).filter(UserRole.role_id == role.id).delete()
            
            # Add new mappings
            for username in usernames:
                user = self.db.query(User).filter(
                    User.username == username,
                    User.tenant_id == tenant_id
                ).first()
                
                if user:
                    user_role = UserRole(
                        user_id=user.id,
                        role_id=role.id,
                        tenant_id=tenant_id,
                        created_by=created_by
                    )
                    self.db.add(user_role)
            
            imported_count += 1
        
        self.db.commit()
        return imported_count