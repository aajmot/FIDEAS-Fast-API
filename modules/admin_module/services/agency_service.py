from core.database.connection import db_manager
from modules.admin_module.models.agency import Agency
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware

class AgencyService:
    @ExceptionMiddleware.handle_exceptions("AgencyService")
    def create(self, agency_data: dict) -> int:
        with db_manager.get_session() as session:
            agency_data['tenant_id'] = session_manager.get_current_tenant_id()
            agency_data['created_by'] = session_manager.get_current_username()
            agency_data['updated_by'] = session_manager.get_current_username()
            
            # Remove is_active if present (not in Agency model)
            agency_data.pop('is_active', None)
            
            agency = Agency(**agency_data)
            session.add(agency)
            session.commit()
            return agency.id
    
    @ExceptionMiddleware.handle_exceptions("AgencyService")
    def get_all(self):
        with db_manager.get_session() as session:
            query = session.query(Agency).filter(Agency.is_deleted == False)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(Agency.tenant_id == tenant_id)
            return query.all()
    
    @ExceptionMiddleware.handle_exceptions("AgencyService")
    def get_by_id(self, agency_id: int):
        with db_manager.get_session() as session:
            return session.query(Agency).filter(
                Agency.id == agency_id,
                Agency.is_deleted == False
            ).first()
    
    @ExceptionMiddleware.handle_exceptions("AgencyService")
    def update(self, agency_id: int, agency_data: dict):
        with db_manager.get_session() as session:
            agency = session.query(Agency).filter(
                Agency.id == agency_id,
                Agency.is_deleted == False
            ).first()
            if agency:
                agency_data['updated_by'] = session_manager.get_current_username()
                
                # Remove is_active if present (not in Agency model)
                agency_data.pop('is_active', None)
                
                for key, value in agency_data.items():
                    if hasattr(agency, key):
                        setattr(agency, key, value)
                session.commit()
                return agency
            return None
    
    @ExceptionMiddleware.handle_exceptions("AgencyService")
    def delete(self, agency_id: int):
        with db_manager.get_session() as session:
            agency = session.query(Agency).filter(Agency.id == agency_id).first()
            if agency:
                agency.is_deleted = True
                agency.updated_by = session_manager.get_current_username()
                session.commit()
                return True
            return False
