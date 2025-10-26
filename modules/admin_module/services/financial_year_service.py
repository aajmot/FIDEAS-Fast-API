from core.database.connection import db_manager
from modules.admin_module.models.entities import FinancialYear
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware

class FinancialYearService:
    @ExceptionMiddleware.handle_exceptions("FinancialYearService")
    def create(self, fy_data: dict):
        with db_manager.get_session() as session:
            fy_data['tenant_id'] = session_manager.get_current_tenant_id()
            fy_data['created_by'] = session_manager.get_current_username()
            
            # Check for duplicate code
            existing = session.query(FinancialYear).filter(
                FinancialYear.code == fy_data['code'],
                FinancialYear.tenant_id == fy_data['tenant_id']
            ).first()
            if existing:
                raise ValueError(f"Financial year code '{fy_data['code']}' already exists")
            
            # If this is set as current, unset others
            if fy_data.get('is_current'):
                session.query(FinancialYear).filter(
                    FinancialYear.tenant_id == fy_data['tenant_id'],
                    FinancialYear.is_current == True
                ).update({'is_current': False})
            
            financial_year = FinancialYear(**fy_data)
            session.add(financial_year)
            session.commit()
            session.refresh(financial_year)
            return financial_year
    
    @ExceptionMiddleware.handle_exceptions("FinancialYearService")
    def get_all(self):
        with db_manager.get_session() as session:
            query = session.query(FinancialYear)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(FinancialYear.tenant_id == tenant_id)
            financial_years = query.order_by(FinancialYear.start_date.desc()).all()
            
            # Convert to simple objects to avoid DetachedInstanceError
            result = []
            for fy in financial_years:
                fy_dict = {
                    'id': fy.id,
                    'name': fy.name,
                    'code': fy.code,
                    'start_date': fy.start_date,
                    'end_date': fy.end_date,
                    'is_current': fy.is_current
                }
                result.append(type('FinancialYear', (), fy_dict)())
            
            return result
    
    @ExceptionMiddleware.handle_exceptions("FinancialYearService")
    def get_by_id(self, fy_id: int):
        with db_manager.get_session() as session:
            return session.query(FinancialYear).filter(FinancialYear.id == fy_id).first()
    
    @ExceptionMiddleware.handle_exceptions("FinancialYearService")
    def update(self, fy_id: int, fy_data: dict):
        with db_manager.get_session() as session:
            fy = session.query(FinancialYear).filter(FinancialYear.id == fy_id).first()
            if fy:
                fy_data['updated_by'] = session_manager.get_current_username()
                
                # Check for duplicate code if code is being updated
                if 'code' in fy_data and fy_data['code'] != fy.code:
                    existing = session.query(FinancialYear).filter(
                        FinancialYear.code == fy_data['code'],
                        FinancialYear.tenant_id == fy.tenant_id,
                        FinancialYear.id != fy_id
                    ).first()
                    if existing:
                        raise ValueError(f"Financial year code '{fy_data['code']}' already exists")
                
                # If this is set as current, unset others
                if fy_data.get('is_current') and not fy.is_current:
                    session.query(FinancialYear).filter(
                        FinancialYear.tenant_id == fy.tenant_id,
                        FinancialYear.is_current == True
                    ).update({'is_current': False})
                
                for key, value in fy_data.items():
                    if hasattr(fy, key):
                        setattr(fy, key, value)
                session.commit()
                session.refresh(fy)
                return fy
            return None
    
    @ExceptionMiddleware.handle_exceptions("FinancialYearService")
    def delete(self, fy_id: int):
        with db_manager.get_session() as session:
            fy = session.query(FinancialYear).filter(FinancialYear.id == fy_id).first()
            if fy:
                session.delete(fy)
                session.commit()
                return True
            return False