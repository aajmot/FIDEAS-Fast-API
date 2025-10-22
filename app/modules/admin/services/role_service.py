from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db.models.admin_models.role_model import Role
from app.modules.shared.services.base_service import BaseService

class RoleService(BaseService):
    def __init__(self, db: Session):
        super().__init__(Role, db)
    
    def get_roles_paginated(self, tenant_id: int, search: str = None, offset: int = 0, limit: int = 10):
        query = self.db.query(Role).filter(Role.tenant_id == tenant_id)
        
        if search:
            query = query.filter(or_(
                Role.name.ilike(f"%{search}%"),
                Role.description.ilike(f"%{search}%")
            ))
        
        total = query.count()
        roles = query.offset(offset).limit(limit).all()
        return roles, total
    
    def import_roles(self, roles_data: List[Dict], tenant_id: int, created_by: str):
        imported_count = 0
        
        for role_data in roles_data:
            try:
                role_data["tenant_id"] = tenant_id
                role_data["created_by"] = created_by
                role_data["is_active"] = role_data.get("is_active", "true").lower() == "true"
                self.create(role_data)
                imported_count += 1
            except Exception:
                continue
        
        return imported_count