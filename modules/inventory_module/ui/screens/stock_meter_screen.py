import customtkinter as ctk
import tkinter as tk
from core.shared.components.base_screen import BaseScreen
from core.shared.components.searchable_dropdown import SearchableDropdown
from modules.inventory_module.services.stock_service import StockService
from core.shared.middleware.exception_handler import ExceptionMiddleware
from core.shared.components.import_mixin import ImportMixin

class StockMeterScreen(BaseScreen, ImportMixin):
    def __init__(self, parent, inventory_module, **kwargs):
        self.inventory_module = inventory_module
        self.stock_service = StockService()
        self.selected_stock = None
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        ctk.CTkLabel(header_frame, text="Stock Meter & Settings", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Back", command=self.back_to_dashboard, width=80).pack(side="right", padx=10, pady=10)
        
        # Form - Stock Settings (similar to Product master form)
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", padx=10, pady=5)
        
        # Row 1
        ctk.CTkLabel(form_frame, text="Product:").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.product_combo = SearchableDropdown(
            form_frame, 
            values=[], 
            width=200, 
            placeholder_text="Search product...",
            command=self.on_product_select
        )
        self.product_combo.grid(row=0, column=1, padx=5, pady=3)
        
        ctk.CTkLabel(form_frame, text="Reorder Level:").grid(row=0, column=2, padx=5, pady=3, sticky="w")
        self.reorder_level_input = ctk.CTkEntry(form_frame, width=120)
        self.reorder_level_input.grid(row=0, column=3, padx=5, pady=3)
        
        ctk.CTkLabel(form_frame, text="Danger Level:").grid(row=0, column=4, padx=5, pady=3, sticky="w")
        self.danger_level_input = ctk.CTkEntry(form_frame, width=120)
        self.danger_level_input.grid(row=0, column=5, padx=5, pady=3)
        
        # Row 2
        ctk.CTkLabel(form_frame, text="Min Stock:").grid(row=1, column=0, padx=5, pady=3, sticky="w")
        self.min_stock_input = ctk.CTkEntry(form_frame, width=120)
        self.min_stock_input.grid(row=1, column=1, padx=5, pady=3)
        
        ctk.CTkLabel(form_frame, text="Max Stock:").grid(row=1, column=2, padx=5, pady=3, sticky="w")
        self.max_stock_input = ctk.CTkEntry(form_frame, width=120)
        self.max_stock_input.grid(row=1, column=3, padx=5, pady=3)
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(button_frame, text="Save Settings", command=self.save_settings, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Clear", command=self.clear_form, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
        self.add_import_button(button_frame)
        ctk.CTkButton(button_frame, text="Refresh", command=self.load_stock_levels, height=25, font=ctk.CTkFont(size=10)).pack(side="right", padx=5, pady=5)
        
        # Data Grid (similar to Product master)
        columns = [
            {'key': 'id', 'title': 'ID', 'width': 60},
            {'key': 'name', 'title': 'Product', 'width': 200},
            {'key': 'current_stock', 'title': 'Current Stock', 'width': 120},
            {'key': 'reorder_level', 'title': 'Reorder Level', 'width': 120},
            {'key': 'danger_level', 'title': 'Danger Level', 'width': 120},
            {'key': 'min_stock', 'title': 'Min Stock', 'width': 100},
            {'key': 'max_stock', 'title': 'Max Stock', 'width': 100},
            {'key': 'status', 'title': 'Status', 'width': 100}
        ]
        
        from core.shared.components.data_grid import DataGrid
        self.data_grid = DataGrid(
            self, 
            columns, 
            on_row_select=self.on_stock_select,
            on_delete=self.on_stock_delete,
            items_per_page=15,
            use_enhanced=True
        )
        self.data_grid.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.load_products()
        self.load_stock_levels()
    
    def load_products(self):
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import Product
        from core.shared.utils.session_manager import session_manager
        
        with db_manager.get_session() as session:
            query = session.query(Product)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(Product.tenant_id == tenant_id)
            
            products = query.all()
            product_values = [f"{prod.id}:{prod.name}" for prod in products]
            self.product_combo.configure_values(product_values)
    
    def load_stock_levels(self):
        try:
            from core.database.connection import db_manager
            from modules.inventory_module.models.entities import Product
            from modules.inventory_module.models.stock_entities import StockBalance
            from core.shared.utils.session_manager import session_manager
            from sqlalchemy import func
            
            stock_data = []
            
            with db_manager.get_session() as session:
                # Get products with their stock levels and settings
                # Only show items with qty > 0 or having stock settings configured
                query = session.query(
                    Product.id,
                    Product.name,
                    func.coalesce(func.sum(StockBalance.total_quantity), 0).label('current_stock'),
                    Product.reorder_level,
                    Product.danger_level,
                    Product.min_stock,
                    Product.max_stock
                ).outerjoin(StockBalance).filter(
                    Product.tenant_id == session_manager.get_current_tenant_id()
                ).group_by(Product.id, Product.name, Product.reorder_level, Product.danger_level, Product.min_stock, Product.max_stock).having(
                    (func.coalesce(func.sum(StockBalance.total_quantity), 0) > 0) |
                    (Product.reorder_level > 0) |
                    (Product.danger_level > 0) |
                    (Product.min_stock > 0) |
                    (Product.max_stock > 0)
                )
                
                products = query.all()
                
                for product in products:
                    current_stock = float(product.current_stock or 0)
                    reorder_level = float(product.reorder_level or 0)
                    danger_level = float(product.danger_level or 0)
                    
                    # Determine status
                    if current_stock <= danger_level and danger_level > 0:
                        status = "DANGER"
                    elif current_stock <= reorder_level and reorder_level > 0:
                        status = "LOW"
                    else:
                        status = "OK"
                    
                    stock_item = {
                        'id': product.id,
                        'name': product.name,
                        'current_stock': f"{current_stock:.2f}",
                        'reorder_level': f"{reorder_level:.2f}",
                        'danger_level': f"{danger_level:.2f}",
                        'min_stock': f"{float(product.min_stock or 0):.2f}",
                        'max_stock': f"{float(product.max_stock or 0):.2f}",
                        'status': status
                    }
                    stock_data.append(stock_item)
            
            self.data_grid.set_data(stock_data)
        
        except Exception as e:
            self.show_message(f"Error loading stock levels: {str(e)}", "error")
    
    def on_product_select(self, value):
        if value and ':' in value:
            product_id = int(value.split(':')[0])
            self.load_product_settings(product_id)
    
    def load_product_settings(self, product_id):
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import Product
        
        with db_manager.get_session() as session:
            product = session.query(Product).filter(Product.id == product_id).first()
            if product:
                self.reorder_level_input.delete(0, tk.END)
                self.reorder_level_input.insert(0, str(float(product.reorder_level or 0)))
                
                self.danger_level_input.delete(0, tk.END)
                self.danger_level_input.insert(0, str(float(product.danger_level or 0)))
                
                self.min_stock_input.delete(0, tk.END)
                self.min_stock_input.insert(0, str(float(product.min_stock or 0)))
                
                self.max_stock_input.delete(0, tk.END)
                self.max_stock_input.insert(0, str(float(product.max_stock or 0)))
    
    @ExceptionMiddleware.handle_exceptions("StockMeterScreen")
    def save_settings(self):
        if not self.product_combo.get().strip():
            self.show_message("Please select a product", "error")
            return
        
        try:
            product_id = int(self.product_combo.get().split(':')[0])
            
            from core.database.connection import db_manager
            from modules.inventory_module.models.entities import Product
            from core.shared.utils.session_manager import session_manager
            
            with db_manager.get_session() as session:
                product = session.query(Product).filter(Product.id == product_id).first()
                if product:
                    product.reorder_level = float(self.reorder_level_input.get() or 0)
                    product.danger_level = float(self.danger_level_input.get() or 0)
                    product.min_stock = float(self.min_stock_input.get() or 0)
                    product.max_stock = float(self.max_stock_input.get() or 0)
                    product.updated_by = session_manager.get_current_username()
                    
                    session.commit()
                    self.show_message("Stock settings saved successfully")
                    self.load_stock_levels()
                    self.load_alerts()
        
        except Exception as e:
            self.show_message(f"Error saving settings: {str(e)}", "error")
    
    def on_stock_select(self, stock_data):
        """Handle stock item selection from data grid"""
        self.selected_stock = stock_data
        self.product_combo.set(f"{stock_data['id']}:{stock_data['name']}")
        self.reorder_level_input.delete(0, tk.END)
        self.reorder_level_input.insert(0, stock_data['reorder_level'])
        self.danger_level_input.delete(0, tk.END)
        self.danger_level_input.insert(0, stock_data['danger_level'])
        self.min_stock_input.delete(0, tk.END)
        self.min_stock_input.insert(0, stock_data['min_stock'])
        self.max_stock_input.delete(0, tk.END)
        self.max_stock_input.insert(0, stock_data['max_stock'])
    
    def clear_form(self):
        """Clear the form fields"""
        self.selected_stock = None
        self.product_combo.clear()
        self.reorder_level_input.delete(0, tk.END)
        self.danger_level_input.delete(0, tk.END)
        self.min_stock_input.delete(0, tk.END)
        self.max_stock_input.delete(0, tk.END)
    
    def download_template(self):
        template_data = {
            'Product Name': ['Paracetamol 500mg', 'Vitamin C Tablets', 'Cough Syrup'],
            'Reorder Level': [50, 30, 25],
            'Danger Level': [10, 5, 5],
            'Min Stock': [5, 2, 2],
            'Max Stock': [200, 100, 100]
        }
        self.create_template_file(template_data, 'stock_settings')
    
    def import_from_excel(self):
        def process_stock_row(row, index):
            product_name = str(row['Product Name']).strip()
            reorder_level = float(row.get('Reorder Level', 0))
            danger_level = float(row.get('Danger Level', 0))
            min_stock = float(row.get('Min Stock', 0))
            max_stock = float(row.get('Max Stock', 0))
            
            if not product_name:
                return False
            
            # Find product by name
            from core.database.connection import db_manager
            from modules.inventory_module.models.entities import Product
            from core.shared.utils.session_manager import session_manager
            
            with db_manager.get_session() as session:
                tenant_id = session_manager.get_current_tenant_id()
                product = session.query(Product).filter(
                    Product.name == product_name,
                    Product.tenant_id == tenant_id
                ).first()
                
                if not product:
                    raise Exception(f"Product '{product_name}' not found")
                
                # Update stock settings
                product.reorder_level = reorder_level
                product.danger_level = danger_level
                product.min_stock = min_stock
                product.max_stock = max_stock
                product.updated_by = session_manager.get_current_username()
                
                session.commit()
            
            return True
        
        self.process_import_file(['Product Name'], process_stock_row, 'stock_settings')
    
    @ExceptionMiddleware.handle_exceptions("StockMeterScreen")
    def on_stock_delete(self, stock_data_list):
        """Handle stock settings deletion (reset to zero)"""
        try:
            from core.database.connection import db_manager
            from modules.inventory_module.models.entities import Product
            from core.shared.utils.session_manager import session_manager
            
            with db_manager.get_session() as session:
                for stock_data in stock_data_list:
                    product = session.query(Product).filter(Product.id == stock_data['id']).first()
                    if product:
                        # Reset stock settings to zero
                        product.reorder_level = 0
                        product.danger_level = 0
                        product.min_stock = 0
                        product.max_stock = 0
                        product.updated_by = session_manager.get_current_username()
                
                session.commit()
            
            self.show_message(f"Successfully reset stock settings for {len(stock_data_list)} product(s)")
            self.clear_form()
            return True
        except Exception as e:
            self.show_message(f"Error resetting stock settings: {str(e)}", "error")
            return False
    
    def load_data(self):
        self.load_products()
        self.load_stock_levels()