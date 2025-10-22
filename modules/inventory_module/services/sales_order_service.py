from core.database.connection import db_manager
from modules.inventory_module.models.entities import SalesOrder, SalesOrderItem
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware
from datetime import datetime

class SalesOrderService:
    @ExceptionMiddleware.handle_exceptions("SalesOrderService")
    def create_with_items(self, order_data: dict, items_data: list):
        with db_manager.get_session() as session:
            try:
                # Add tenant_id and audit fields to order
                order_data['tenant_id'] = session_manager.get_current_tenant_id()
                order_data['created_by'] = session_manager.get_current_username()
                
                # Create sales order
                sales_order = SalesOrder(**order_data)
                session.add(sales_order)
                session.flush()  # Get the order ID
                
                # Create order items
                order_items = []
                for item_data in items_data:
                    item_data['sales_order_id'] = sales_order.id
                    order_item = SalesOrderItem(**item_data)
                    session.add(order_item)
                    order_items.append(order_item)
                
                # Record stock transactions in same session (optional)
                try:
                    from modules.inventory_module.services.stock_service import StockService
                    stock_service = StockService()
                    stock_service.record_sales_transaction_in_session(session, sales_order, order_items)
                except (ImportError, AttributeError):
                    pass  # Stock service not available
                
                # Record accounting transaction in same session (optional)
                try:
                    from modules.account_module.services.payment_service import PaymentService
                    payment_service = PaymentService()
                    
                    # Calculate COGS from order items
                    cogs_amount = sum(float(item.quantity * (item.cost_price or 0)) for item in order_items)
                    
                    payment_service.record_sales_transaction_in_session(
                        session,
                        sales_order.id, 
                        sales_order.order_number, 
                        float(sales_order.total_amount),
                        sales_order.order_date,
                        cogs_amount
                    )
                except (ImportError, AttributeError):
                    pass  # Payment service not available
                
                # Commit all operations together
                session.commit()
                return sales_order.id
                
            except Exception as e:
                session.rollback()
                raise e
    
    @ExceptionMiddleware.handle_exceptions("SalesOrderService")
    def get_all(self, page=1, page_size=100):
        from sqlalchemy.orm import joinedload
        from modules.inventory_module.models.entities import Customer
        from modules.admin_module.models.agency import Agency
        
        with db_manager.get_session() as session:
            query = session.query(SalesOrder).options(joinedload(SalesOrder.customer))
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(SalesOrder.tenant_id == tenant_id)
            
            # Order by date desc (most recent first)
            query = query.order_by(SalesOrder.order_date.desc(), SalesOrder.created_at.desc())
            
            # Apply pagination
            offset = (page - 1) * page_size
            orders = query.offset(offset).limit(page_size).all()
            
            # Convert to dict to avoid DetachedInstanceError
            result = []
            for order in orders:
                agency_name = None
                if order.agency_id:
                    agency = session.query(Agency).filter(Agency.id == order.agency_id).first()
                    if agency:
                        agency_name = f"{agency.name} | {agency.phone}"
                
                order_dict = {
                    'id': order.id,
                    'order_number': order.order_number,
                    'total_amount': order.total_amount,
                    'status': order.status,
                    'order_date': order.order_date,
                    'customer_name': order.customer.name if order.customer else '',
                    'agency_id': order.agency_id,
                    'agency_name': agency_name
                }
                result.append(type('SalesOrder', (), order_dict)())
            
            return result
    
    @ExceptionMiddleware.handle_exceptions("SalesOrderService")
    def get_total_count(self):
        with db_manager.get_session() as session:
            query = session.query(SalesOrder)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(SalesOrder.tenant_id == tenant_id)
            return query.count()
    
    @ExceptionMiddleware.handle_exceptions("SalesOrderService")
    def get_by_id(self, order_id: int):
        with db_manager.get_session() as session:
            return session.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    
    @ExceptionMiddleware.handle_exceptions("SalesOrderService")
    def update(self, order_id: int, order_data: dict):
        with db_manager.get_session() as session:
            order = session.query(SalesOrder).filter(SalesOrder.id == order_id).first()
            if order:
                order_data['updated_by'] = session_manager.get_current_username()
                
                for key, value in order_data.items():
                    if hasattr(order, key):
                        setattr(order, key, value)
                session.commit()
                return order
            return None
    
    @ExceptionMiddleware.handle_exceptions("SalesOrderService")
    def reverse_order(self, order_id: int, reason: str):
        """Reverse a sales order - reverses stock and accounting transactions"""
        with db_manager.get_session() as session:
            try:
                order = session.query(SalesOrder).filter(SalesOrder.id == order_id).first()
                if not order:
                    raise ValueError("Order not found")
                
                if order.status == 'reversed':
                    raise ValueError("Order is already reversed")
                
                # Get order items
                items = session.query(SalesOrderItem).filter(SalesOrderItem.sales_order_id == order_id).all()
                
                # Reverse stock transactions
                from modules.inventory_module.services.stock_service import StockService
                stock_service = StockService()
                stock_service.reverse_sales_transaction_in_session(session, order, items)
                
                # Reverse accounting transactions
                from modules.account_module.services.payment_service import PaymentService
                payment_service = PaymentService()
                payment_service.reverse_sales_transaction_in_session(
                    session, order.id, order.order_number, float(order.total_amount), order.order_date
                )
                
                # Update order status and reason
                order.status = 'reversed'
                order.reversal_reason = reason
                order.reversed_at = datetime.now()
                order.reversed_by = session_manager.get_current_username()
                order.updated_by = session_manager.get_current_username()
                
                session.commit()
                return True
                
            except Exception as e:
                session.rollback()
                raise e
    
    @ExceptionMiddleware.handle_exceptions("SalesOrderService")
    def delete(self, order_id: int):
        with db_manager.get_session() as session:
            order = session.query(SalesOrder).filter(SalesOrder.id == order_id).first()
            if order:
                # Delete order items first
                session.query(SalesOrderItem).filter(SalesOrderItem.sales_order_id == order_id).delete()
                # Delete order
                session.delete(order)
                session.commit()
                return True
            return False