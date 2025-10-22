from core.database.connection import db_manager
from modules.inventory_module.models.entities import Supplier
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware

class SupplierService:
    @ExceptionMiddleware.handle_exceptions("SupplierService")
    def create(self, supplier_data: dict) -> int:
        with db_manager.get_session() as session:
            # Add tenant_id and audit fields
            supplier_data['tenant_id'] = session_manager.get_current_tenant_id()
            supplier_data['created_by'] = session_manager.get_current_username()
            
            supplier = Supplier(**supplier_data)
            session.add(supplier)
            session.commit()
            return supplier.id
    
    @ExceptionMiddleware.handle_exceptions("SupplierService")
    def get_all(self):
        with db_manager.get_session() as session:
            query = session.query(Supplier)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(Supplier.tenant_id == tenant_id)
            return query.all()
    
    @ExceptionMiddleware.handle_exceptions("SupplierService")
    def get_by_id(self, supplier_id: int):
        with db_manager.get_session() as session:
            return session.query(Supplier).filter(Supplier.id == supplier_id).first()
    
    @ExceptionMiddleware.handle_exceptions("SupplierService")
    def update(self, supplier_id: int, supplier_data: dict):
        with db_manager.get_session() as session:
            supplier = session.query(Supplier).filter(Supplier.id == supplier_id).first()
            if supplier:
                # Add audit fields
                supplier_data['updated_by'] = session_manager.get_current_username()
                
                for key, value in supplier_data.items():
                    if hasattr(supplier, key):
                        setattr(supplier, key, value)
                session.commit()
                return supplier
            return None
    
    @ExceptionMiddleware.handle_exceptions("SupplierService")
    def delete(self, supplier_id: int):
        with db_manager.get_session() as session:
            supplier = session.query(Supplier).filter(Supplier.id == supplier_id).first()
            if supplier:
                session.delete(supplier)
                session.commit()
                return True
            return False