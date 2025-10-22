from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db.models.inventory_models.customer_model import Customer
from app.modules.shared.services.base_service import BaseService

class CustomerService(BaseService):
    def __init__(self, db: Session):
        super().__init__(Customer, db)
    
    def get_customers_paginated(self, tenant_id: int, search: str = None, offset: int = 0, limit: int = 10):
        query = self.db.query(Customer).filter(Customer.tenant_id == tenant_id)
        
        if search:
            query = query.filter(or_(
                Customer.name.ilike(f"%{search}%"),
                Customer.email.ilike(f"%{search}%"),
                Customer.phone.ilike(f"%{search}%")
            ))
        
        total = query.count()
        customers = query.offset(offset).limit(limit).all()
        
        customer_data = [{
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "age": customer.age,
            "address": customer.address,
            "tax_id": customer.tax_id,
            "is_active": customer.is_active
        } for customer in customers]
        
        return customer_data, total
    
    def import_customers(self, customers_data: List[Dict], tenant_id: int, created_by: str):
        imported_count = 0
        
        for customer_data in customers_data:
            try:
                data = {
                    "name": customer_data["name"],
                    "phone": customer_data["phone"],
                    "email": customer_data.get("email", ""),
                    "address": customer_data.get("address", ""),
                    "tax_id": customer_data.get("tax_id", ""),
                    "tenant_id": tenant_id,
                    "is_active": customer_data.get("is_active", "true").lower() == "true",
                    "created_by": created_by
                }
                
                if "age" in customer_data and customer_data["age"].strip():
                    data["age"] = int(customer_data["age"])
                
                self.create(data)
                imported_count += 1
            except Exception:
                continue
        
        return imported_count