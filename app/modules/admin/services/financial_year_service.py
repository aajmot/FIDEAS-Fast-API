from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.models.admin_models.financial_year_model import FinancialYear
from app.modules.shared.services.base_service import BaseService

class FinancialYearService(BaseService):
    def __init__(self, db: Session):
        super().__init__(FinancialYear, db)
    
    def get_years_paginated(self, tenant_id: int, search: str = None, offset: int = 0, limit: int = 10):
        query = self.db.query(FinancialYear).filter(FinancialYear.tenant_id == tenant_id)
        
        if search:
            query = query.filter(FinancialYear.name.ilike(f"%{search}%"))
        
        query = query.order_by(FinancialYear.start_date.desc())
        
        total = query.count()
        years = query.offset(offset).limit(limit).all()
        return years, total
    
    def create_year(self, data: Dict[str, Any], tenant_id: int, created_by: str):
        # Check for duplicate name
        existing = self.db.query(FinancialYear).filter(
            FinancialYear.tenant_id == tenant_id,
            FinancialYear.name == data["name"]
        ).first()
        
        if existing:
            raise ValueError("Financial year name already exists")
        
        # If this is set as active, unset other active years
        if data.get("is_active"):
            self.db.query(FinancialYear).filter(
                FinancialYear.tenant_id == tenant_id,
                FinancialYear.is_active == True
            ).update({"is_active": False})
        
        data.update({
            "start_date": datetime.fromisoformat(data["start_date"]),
            "end_date": datetime.fromisoformat(data["end_date"]),
            "tenant_id": tenant_id,
            "created_by": created_by
        })
        
        return self.create(data)
    
    def update_year(self, year_id: int, data: Dict[str, Any], tenant_id: int, updated_by: str):
        year = self.db.query(FinancialYear).filter(
            FinancialYear.id == year_id,
            FinancialYear.tenant_id == tenant_id
        ).first()
        
        if not year:
            return None
        
        # Check for duplicate name (excluding current record)
        if "name" in data:
            existing = self.db.query(FinancialYear).filter(
                FinancialYear.tenant_id == tenant_id,
                FinancialYear.id != year_id,
                FinancialYear.name == data.get("name")
            ).first()
            
            if existing:
                raise ValueError("Financial year name already exists")
        
        # If this is set as active, unset other active years
        if data.get("is_active") and not year.is_active:
            self.db.query(FinancialYear).filter(
                FinancialYear.tenant_id == tenant_id,
                FinancialYear.is_active == True
            ).update({"is_active": False})
        
        # Convert date strings to datetime objects
        for key in ['start_date', 'end_date']:
            if key in data and data[key]:
                data[key] = datetime.fromisoformat(data[key])
        
        data["updated_by"] = updated_by
        return self.update(year_id, data)
    
    def import_years(self, years_data: List[Dict], tenant_id: int, created_by: str):
        imported_count = 0
        
        for year_data in years_data:
            try:
                # If this is set as active, unset other active years
                if year_data.get("is_active", "false").lower() == "true":
                    self.db.query(FinancialYear).filter(
                        FinancialYear.tenant_id == tenant_id,
                        FinancialYear.is_active == True
                    ).update({"is_active": False})
                
                data = {
                    "name": year_data["name"],
                    "start_date": datetime.fromisoformat(year_data["start_date"]),
                    "end_date": datetime.fromisoformat(year_data["end_date"]),
                    "tenant_id": tenant_id,
                    "is_active": year_data.get("is_active", "true").lower() == "true",
                    "created_by": created_by
                }
                
                self.create(data)
                imported_count += 1
            except Exception:
                continue
        
        return imported_count