from core.database.connection import db_manager
from modules.inventory_module.models.entities import Customer
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware

class CustomerService:
    @ExceptionMiddleware.handle_exceptions("CustomerService")
    def create(self, customer_data: dict) -> int:
        with db_manager.get_session() as session:
            # Add tenant_id and audit fields
            customer_data['tenant_id'] = session_manager.get_current_tenant_id()
            customer_data['created_by'] = session_manager.get_current_username()
            
            customer = Customer(**customer_data)
            session.add(customer)
            session.commit()
            return customer.id
    
    @ExceptionMiddleware.handle_exceptions("CustomerService")
    def get_all(self):
        with db_manager.get_session() as session:
            query = session.query(Customer)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(Customer.tenant_id == tenant_id)
            return query.all()
    
    @ExceptionMiddleware.handle_exceptions("CustomerService")
    def get_by_id(self, customer_id: int):
        with db_manager.get_session() as session:
            return session.query(Customer).filter(Customer.id == customer_id).first()
    
    @ExceptionMiddleware.handle_exceptions("CustomerService")
    def update(self, customer_id: int, customer_data: dict):
        with db_manager.get_session() as session:
            customer = session.query(Customer).filter(Customer.id == customer_id).first()
            if customer:
                # Add audit fields
                customer_data['updated_by'] = session_manager.get_current_username()
                
                for key, value in customer_data.items():
                    if hasattr(customer, key):
                        setattr(customer, key, value)
                session.commit()
                return customer
            return None
    
    @ExceptionMiddleware.handle_exceptions("CustomerService")
    def delete(self, customer_id: int):
        with db_manager.get_session() as session:
            customer = session.query(Customer).filter(Customer.id == customer_id).first()
            if customer:
                session.delete(customer)
                session.commit()
                return True
            return False