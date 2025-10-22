from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db.models.inventory_models.supplier_model import Supplier
from app.modules.shared.services.base_service import BaseService

class SupplierService(BaseService):
    def __init__(self, db: Session):
        super().__init__(Supplier, db)
    
    def get_suppliers_paginated(self, tenant_id: int, search: str = None, offset: int = 0, limit: int = 10):
        query = self.db.query(Supplier).filter(Supplier.tenant_id == tenant_id)
        
        if search:
            query = query.filter(or_(
                Supplier.name.ilike(f"%{search}%"),
                Supplier.email.ilike(f"%{search}%"),
                Supplier.phone.ilike(f"%{search}%")
            ))
        
        total = query.count()
        suppliers = query.offset(offset).limit(limit).all()
        
        supplier_data = [{
            "id": supplier.id,
            "name": supplier.name,
            "phone": supplier.phone,
            "email": supplier.email,
            "tax_id": supplier.tax_id,
            "contact_person": supplier.contact_person,
            "address": supplier.address,
            "is_active": supplier.is_active
        } for supplier in suppliers]
        
        return supplier_data, total
    
    def import_suppliers(self, suppliers_data: List[Dict], tenant_id: int, created_by: str):
        imported_count = 0
        
        for supplier_data in suppliers_data:
            try:
                data = {
                    "name": supplier_data["name"],
                    "phone": supplier_data["phone"],
                    "email": supplier_data.get("email", ""),
                    "tax_id": supplier_data.get("tax_id", ""),
                    "contact_person": supplier_data.get("contact_person", ""),
                    "address": supplier_data.get("address", ""),
                    "tenant_id": tenant_id,
                    "is_active": supplier_data.get("is_active", "true").lower() == "true",
                    "created_by": created_by
                }
                
                self.create(data)
                imported_count += 1
            except Exception:
                continue
        
        return imported_count