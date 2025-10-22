from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db.models.admin_models.legal_entity_model import LegalEntity
from app.db.models.admin_models.user_model import User
from app.modules.shared.services.base_service import BaseService

class LegalEntityService(BaseService):
    def __init__(self, db: Session):
        super().__init__(LegalEntity, db)
    
    def get_entities_paginated(self, tenant_id: int, search: str = None, offset: int = 0, limit: int = 10):
        query = self.db.query(LegalEntity).filter(LegalEntity.tenant_id == tenant_id)
        
        if search:
            query = query.filter(or_(
                LegalEntity.name.ilike(f"%{search}%"),
                LegalEntity.code.ilike(f"%{search}%"),
                LegalEntity.registration_number.ilike(f"%{search}%")
            ))
        
        total = query.count()
        entities = query.offset(offset).limit(limit).all()
        
        entity_data = []
        for entity in entities:
            admin_user = self.db.query(User).filter(User.id == entity.admin_user_id).first() if entity.admin_user_id else None
            entity_data.append({
                "id": entity.id,
                "name": entity.name,
                "code": entity.code,
                "registration_number": entity.registration_number,
                "address": entity.address,
                "logo": entity.logo,
                "admin_user_id": entity.admin_user_id,
                "admin_user_name": f"{admin_user.first_name} {admin_user.last_name}" if admin_user else None,
                "is_active": entity.is_active
            })
        
        return entity_data, total
    
    def import_entities(self, entities_data: List[Dict], tenant_id: int, created_by: str):
        imported_count = 0
        
        for entity_data in entities_data:
            try:
                # Skip header rows
                name_value = entity_data.get("name", "").strip().lower()
                if name_value in ["name", "entity name", "legal entity name", "company name"] or not name_value:
                    continue
                
                admin_user = None
                if entity_data.get("admin_username"):
                    admin_user = self.db.query(User).filter(
                        User.username == entity_data["admin_username"],
                        User.tenant_id == tenant_id
                    ).first()
                
                data = {
                    "name": entity_data["name"],
                    "code": entity_data["code"],
                    "registration_number": entity_data.get("registration_number"),
                    "address": entity_data.get("address"),
                    "logo": entity_data.get("logo"),
                    "admin_user_id": admin_user.id if admin_user else None,
                    "tenant_id": tenant_id,
                    "is_active": entity_data.get("is_active", "true").lower() == "true",
                    "created_by": created_by
                }
                
                self.create(data)
                imported_count += 1
            except Exception:
                continue
        
        return imported_count