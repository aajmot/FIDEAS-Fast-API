from modules.inventory_module.ui.screens.category_screen import CategoryScreen
from modules.inventory_module.ui.screens.product_screen import ProductScreen
from modules.inventory_module.ui.screens.customer_screen import CustomerScreen
from modules.inventory_module.ui.screens.inventory_screen import InventoryScreen
from modules.inventory_module.ui.screens.sales_order_screen import SalesOrderScreen
from core.shared.utils.logger import logger

class InventoryModule:
    def __init__(self, root):
        self.name = "Inventory Module"
        self.root = root
        self.current_screen = None
        
        logger.info("Inventory Module initialized", "InventoryModule")
    

    
    def show_category_screen(self):
        self.clear_current_screen()
        self.current_screen = CategoryScreen(self.root, self)
    
    def show_product_screen(self):
        self.clear_current_screen()
        self.current_screen = ProductScreen(self.root, self)
    
    def show_customer_screen(self):
        self.clear_current_screen()
        self.current_screen = CustomerScreen(self.root, self)
    
    def show_inventory_screen(self):
        self.clear_current_screen()
        self.current_screen = InventoryScreen(self.root, self)
    
    def show_supplier_screen(self):
        self.clear_current_screen()
        from modules.inventory_module.ui.screens.supplier_screen import SupplierScreen
        self.current_screen = SupplierScreen(self.root, self)
    

    
    def show_purchase_order_screen(self):
        self.clear_current_screen()
        from modules.inventory_module.ui.screens.purchase_order_screen import PurchaseOrderScreen
        self.current_screen = PurchaseOrderScreen(self.root, self)
    
    def show_sales_order_screen(self):
        self.clear_current_screen()
        from modules.inventory_module.ui.screens.sales_order_screen import SalesOrderScreen
        self.current_screen = SalesOrderScreen(self.root, self)
    
    def show_stock_tracking_screen(self):
        self.clear_current_screen()
        from modules.inventory_module.ui.screens.stock_tracking_screen import StockTrackingScreen
        self.current_screen = StockTrackingScreen(self.root, self)
    
    def show_stock_meter_screen(self):
        self.clear_current_screen()
        from modules.inventory_module.ui.screens.stock_meter_screen import StockMeterScreen
        self.current_screen = StockMeterScreen(self.root, self)
    
    def show_stock_details_screen(self):
        self.clear_current_screen()
        from modules.inventory_module.ui.screens.stock_details_screen import StockDetailsScreen
        self.current_screen = StockDetailsScreen(self.root, self)
    
    def show_product_waste_screen(self):
        self.clear_current_screen()
        from modules.inventory_module.ui.screens.product_waste_screen import ProductWasteScreen
        self.current_screen = ProductWasteScreen(self.root, self)
    
    def show_unit_screen(self):
        self.clear_current_screen()
        from modules.inventory_module.ui.screens.unit_screen import UnitScreen
        self.current_screen = UnitScreen(self.root, self)
    
    def clear_current_screen(self):
        if self.current_screen:
            self.current_screen.destroy()
        logger.info("Screen cleared", "InventoryModule")
    

    

    

    
    def initialize_data(self):
        """Initialize default data for inventory module"""
        from modules.inventory_module.services.category_service import CategoryService
        from modules.inventory_module.models.entities import Unit
        from core.database.connection import db_manager
        from core.shared.utils.session_manager import session_manager
        
        # Only initialize if we have a current user/tenant
        current_user = session_manager.get_current_user()
        if not current_user:
            return
        
        category_service = CategoryService()
        
        # Create default categories
        categories = category_service.get_all()
        if not categories:
            default_categories = [
                {'name': 'Medicine', 'description': 'Pharmaceutical products'},
                {'name': 'Supplements', 'description': 'Health supplements'},
                {'name': 'Equipment', 'description': 'Medical equipment'}
            ]
            for category_data in default_categories:
                category_service.create(category_data)
            logger.info("Default categories created", "InventoryModule")
        
        # Create default units
        # Note: Units should be created per tenant through the API, not as global defaults
        # This section is commented out to prevent tenant_id constraint violations
        # with db_manager.get_session() as session:
        #     units = session.query(Unit).all()
        #     if not units:
        #         default_units = [
        #             Unit(name='Piece', symbol='pcs', tenant_id=1),  # Requires tenant_id
        #             Unit(name='Box', symbol='box', tenant_id=1),
        #             Unit(name='Bottle', symbol='btl', tenant_id=1)
        #         ]
        #         for unit in default_units:
        #             session.add(unit)
        #         logger.info("Default units created", "InventoryModule")