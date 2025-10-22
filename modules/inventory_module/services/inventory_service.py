from modules.inventory_module.models.entities import Inventory
from modules.admin_module.services.base_service import BaseService
from core.database.connection import db_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware
from decimal import Decimal

class InventoryService(BaseService):
    def __init__(self):
        super().__init__(Inventory)
    
    @ExceptionMiddleware.handle_exceptions()
    def update_stock(self, product_id, quantity_change):
        with db_manager.get_session() as session:
            inventory = session.query(Inventory).filter_by(product_id=product_id).first()
            if inventory:
                inventory.quantity += Decimal(str(quantity_change))
            else:
                inventory = Inventory(product_id=product_id, quantity=Decimal(str(quantity_change)))
                session.add(inventory)
            return inventory
    
    @ExceptionMiddleware.handle_exceptions()
    def get_stock(self, product_id):
        with db_manager.get_session() as session:
            inventory = session.query(Inventory).filter_by(product_id=product_id).first()
            return float(inventory.quantity) if inventory else 0
    
    @ExceptionMiddleware.handle_exceptions()
    def check_availability(self, product_id, required_quantity):
        with db_manager.get_session() as session:
            inventory = session.query(Inventory).filter_by(product_id=product_id).first()
            if inventory:
                available = inventory.quantity - inventory.reserved_quantity
                return available >= Decimal(str(required_quantity))
            return False
    
    @ExceptionMiddleware.handle_exceptions()
    def reserve_stock(self, product_id, quantity):
        with db_manager.get_session() as session:
            inventory = session.query(Inventory).filter_by(product_id=product_id).first()
            if inventory:
                inventory.reserved_quantity += Decimal(str(quantity))
                return True
            return False