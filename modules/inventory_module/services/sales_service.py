from modules.inventory_module.models.entities import SalesOrder, SalesOrderItem, Inventory
from modules.admin_module.services.base_service import BaseService
from core.database.connection import db_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware
from decimal import Decimal
import datetime

class SalesService(BaseService):
    def __init__(self):
        super().__init__(SalesOrder)
    
    @ExceptionMiddleware.handle_exceptions()
    def create_sales_order(self, customer_id, items):
        from core.shared.utils.session_manager import session_manager
        
        with db_manager.get_session() as session:
            # Generate order number
            order_number = f"SO{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Calculate total
            total_amount = sum(Decimal(str(item['quantity'])) * Decimal(str(item['unit_price'])) for item in items)
            
            # Create sales order with tenant and user tracking
            sales_order = SalesOrder(
                order_number=order_number,
                customer_id=customer_id,
                total_amount=total_amount,
                tenant_id=session_manager.get_current_tenant_id(),
                created_by=session_manager.get_current_username()
            )
            session.add(sales_order)
            session.flush()
            
            # Create order items and update inventory
            for item in items:
                order_item = SalesOrderItem(
                    sales_order_id=sales_order.id,
                    product_id=item['product_id'],
                    quantity=Decimal(str(item['quantity'])),
                    unit_price=Decimal(str(item['unit_price'])),
                    total_price=Decimal(str(item['quantity'])) * Decimal(str(item['unit_price']))
                )
                session.add(order_item)
                
                # Update inventory
                inventory = session.query(Inventory).filter_by(product_id=item['product_id']).first()
                if inventory:
                    inventory.quantity -= Decimal(str(item['quantity']))
                else:
                    # Create inventory record if doesn't exist
                    inventory = Inventory(
                        product_id=item['product_id'],
                        quantity=-Decimal(str(item['quantity']))
                    )
                    session.add(inventory)
            
            return sales_order