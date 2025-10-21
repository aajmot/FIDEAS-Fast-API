from core.database.connection import db_manager
from modules.inventory_module.models.entities import ProductWaste, Product, Inventory
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware
from datetime import datetime

class ProductWasteService:
    @ExceptionMiddleware.handle_exceptions("ProductWasteService")
    def create(self, waste_data: dict):
        with db_manager.get_session() as session:
            try:
                waste_data['tenant_id'] = session_manager.get_current_tenant_id()
                waste_data['created_by'] = session_manager.get_current_username()
                
                # Calculate total cost
                waste_data['total_cost'] = float(waste_data['quantity']) * float(waste_data['unit_cost'])
                
                # Create waste record
                product_waste = ProductWaste(**waste_data)
                session.add(product_waste)
                session.flush()
                
                # Record stock transaction in same session (optional)
                try:
                    from modules.inventory_module.services.stock_service import StockService
                    stock_service = StockService()
                    stock_service.record_waste_transaction_in_session(session, product_waste)
                except (ImportError, AttributeError):
                    pass  # Stock service not available
                
                # Record accounting transaction in same session (optional)
                try:
                    self._record_accounting_transaction_in_session(session, product_waste)
                except (ImportError, AttributeError):
                    pass  # Account service not available
                
                # Commit all operations together
                session.commit()
                return product_waste.id
                
            except Exception as e:
                session.rollback()
                raise e
    
    @ExceptionMiddleware.handle_exceptions("ProductWasteService")
    def get_all(self, page=1, page_size=100):
        with db_manager.get_session() as session:
            query = session.query(ProductWaste).join(Product)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(ProductWaste.tenant_id == tenant_id)
            
            query = query.order_by(ProductWaste.waste_date.desc(), ProductWaste.created_at.desc())
            
            offset = (page - 1) * page_size
            wastes = query.offset(offset).limit(page_size).all()
            
            # Convert to simple objects
            result = []
            for waste in wastes:
                waste_dict = {
                    'id': waste.id,
                    'waste_number': waste.waste_number,
                    'product_name': waste.product.name,
                    'batch_number': waste.batch_number,
                    'quantity': waste.quantity,
                    'unit_cost': waste.unit_cost,
                    'total_cost': waste.total_cost,
                    'reason': waste.reason,
                    'waste_date': waste.waste_date
                }
                result.append(type('ProductWaste', (), waste_dict)())
            
            return result
    
    @ExceptionMiddleware.handle_exceptions("ProductWasteService")
    def get_total_count(self):
        with db_manager.get_session() as session:
            query = session.query(ProductWaste)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(ProductWaste.tenant_id == tenant_id)
            return query.count()
    

    
    def _record_accounting_transaction_in_session(self, session, product_waste):
        try:
            from modules.account_module.services.payment_service import PaymentService
            payment_service = PaymentService()
            payment_service.record_waste_transaction_in_session(
                session,
                product_waste.id,
                product_waste.waste_number,
                float(product_waste.total_cost),
                product_waste.waste_date
            )
        except ImportError:
            pass  # Account module not available