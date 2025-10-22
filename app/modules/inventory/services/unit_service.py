from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db.models.inventory_models.unit_model import Unit
from app.modules.shared.services.base_service import BaseService

class UnitService(BaseService):
    def __init__(self, db: Session):
        super().__init__(Unit, db)
    
    def get_units_paginated(self, tenant_id: int, search: str = None, offset: int = 0, limit: int = 10):
        query = self.db.query(Unit).filter(Unit.tenant_id == tenant_id)
        
        if search:
            query = query.filter(or_(
                Unit.name.ilike(f"%{search}%"),
                Unit.symbol.ilike(f"%{search}%")
            ))
        
        total = query.count()
        units = query.offset(offset).limit(limit).all()
        
        unit_data = [{
            "id": unit.id,
            "name": unit.name,
            "symbol": unit.symbol,
            "parent_id": unit.parent_id,
            "conversion_factor": float(unit.conversion_factor) if unit.conversion_factor else 1.0,
            "is_active": unit.is_active
        } for unit in units]
        
        return unit_data, total
    
    def import_units(self, units_data: List[Dict], tenant_id: int, created_by: str):
        imported_count = 0
        
        for unit_data in units_data:
            try:
                name_value = unit_data.get("name", "").strip().lower()
                if name_value in ["name", "unit name", "unit"] or not name_value:
                    continue
                
                data = {
                    "name": unit_data["name"],
                    "symbol": unit_data["symbol"],
                    "tenant_id": tenant_id,
                    "is_active": unit_data.get("is_active", "true").lower() == "true",
                    "created_by": created_by
                }
                
                self.create(data)
                imported_count += 1
            except Exception:
                continue
        
        return imported_count