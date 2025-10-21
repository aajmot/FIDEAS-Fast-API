from datetime import datetime
from typing import List, Optional, Dict, Any
from core.database.connection import db_manager
from modules.account_module.models.entities import FiscalYear
from sqlalchemy import and_

class FiscalYearService:
    def __init__(self):
        self.session_manager = db_manager.get_session_manager()
    
    def get_all(self, include_deleted: bool = False) -> List[FiscalYear]:
        with db_manager.get_session() as session:
            query = session.query(FiscalYear).filter(
                FiscalYear.tenant_id == self.session_manager.tenant_id
            )
            if not include_deleted:
                query = query.filter(FiscalYear.is_deleted == False)
            return query.order_by(FiscalYear.start_date.desc()).all()
    
    def get_by_id(self, fiscal_year_id: int) -> Optional[FiscalYear]:
        with db_manager.get_session() as session:
            return session.query(FiscalYear).filter(
                and_(
                    FiscalYear.id == fiscal_year_id,
                    FiscalYear.tenant_id == self.session_manager.tenant_id,
                    FiscalYear.is_deleted == False
                )
            ).first()
    
    def get_active(self) -> Optional[FiscalYear]:
        with db_manager.get_session() as session:
            return session.query(FiscalYear).filter(
                and_(
                    FiscalYear.tenant_id == self.session_manager.tenant_id,
                    FiscalYear.is_active == True,
                    FiscalYear.is_deleted == False
                )
            ).first()
    
    def create(self, data: Dict[str, Any]) -> FiscalYear:
        with db_manager.get_session() as session:
            # If this is set as active, deactivate all others
            if data.get('is_active', False):
                session.query(FiscalYear).filter(
                    FiscalYear.tenant_id == self.session_manager.tenant_id
                ).update({'is_active': False})
            
            fiscal_year = FiscalYear(
                name=data['name'],
                start_date=datetime.fromisoformat(data['start_date']).date(),
                end_date=datetime.fromisoformat(data['end_date']).date(),
                is_active=data.get('is_active', False),
                is_closed=data.get('is_closed', False),
                tenant_id=self.session_manager.tenant_id,
                created_by=self.session_manager.username
            )
            session.add(fiscal_year)
            session.flush()
            fiscal_year_id = fiscal_year.id
            session.commit()
            return self.get_by_id(fiscal_year_id)
    
    def update(self, fiscal_year_id: int, data: Dict[str, Any]) -> FiscalYear:
        with db_manager.get_session() as session:
            fiscal_year = session.query(FiscalYear).filter(
                and_(
                    FiscalYear.id == fiscal_year_id,
                    FiscalYear.tenant_id == self.session_manager.tenant_id,
                    FiscalYear.is_deleted == False
                )
            ).first()
            
            if not fiscal_year:
                raise ValueError("Fiscal year not found")
            
            # If setting as active, deactivate all others
            if data.get('is_active', False) and not fiscal_year.is_active:
                session.query(FiscalYear).filter(
                    FiscalYear.tenant_id == self.session_manager.tenant_id
                ).update({'is_active': False})
            
            if 'name' in data:
                fiscal_year.name = data['name']
            if 'start_date' in data:
                fiscal_year.start_date = datetime.fromisoformat(data['start_date']).date()
            if 'end_date' in data:
                fiscal_year.end_date = datetime.fromisoformat(data['end_date']).date()
            if 'is_active' in data:
                fiscal_year.is_active = data['is_active']
            if 'is_closed' in data:
                fiscal_year.is_closed = data['is_closed']
            
            fiscal_year.updated_at = datetime.now()
            fiscal_year.updated_by = self.session_manager.username
            
            session.commit()
            return self.get_by_id(fiscal_year_id)
    
    def soft_delete(self, fiscal_year_id: int) -> bool:
        with db_manager.get_session() as session:
            fiscal_year = session.query(FiscalYear).filter(
                and_(
                    FiscalYear.id == fiscal_year_id,
                    FiscalYear.tenant_id == self.session_manager.tenant_id,
                    FiscalYear.is_deleted == False
                )
            ).first()
            
            if not fiscal_year:
                raise ValueError("Fiscal year not found")
            
            if fiscal_year.is_active:
                raise ValueError("Cannot delete active fiscal year")
            
            fiscal_year.is_deleted = True
            fiscal_year.updated_at = datetime.now()
            fiscal_year.updated_by = self.session_manager.username
            
            session.commit()
            return True
    
    def close_fiscal_year(self, fiscal_year_id: int) -> FiscalYear:
        with db_manager.get_session() as session:
            fiscal_year = session.query(FiscalYear).filter(
                and_(
                    FiscalYear.id == fiscal_year_id,
                    FiscalYear.tenant_id == self.session_manager.tenant_id,
                    FiscalYear.is_deleted == False
                )
            ).first()
            
            if not fiscal_year:
                raise ValueError("Fiscal year not found")
            
            if fiscal_year.is_closed:
                raise ValueError("Fiscal year is already closed")
            
            fiscal_year.is_closed = True
            fiscal_year.is_active = False
            fiscal_year.updated_at = datetime.now()
            fiscal_year.updated_by = self.session_manager.username
            
            session.commit()
            return self.get_by_id(fiscal_year_id)
