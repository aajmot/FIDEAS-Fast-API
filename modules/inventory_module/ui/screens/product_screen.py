import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from core.shared.components.base_screen import BaseScreen
from modules.inventory_module.services.product_service import ProductService
from modules.inventory_module.services.category_service import CategoryService
from core.shared.middleware.exception_handler import ExceptionMiddleware
from core.shared.components.import_mixin import ImportMixin
from core.shared.utils.dropdown_migration import create_searchable_dropdown, extract_id_from_value

class ProductScreen(BaseScreen, ImportMixin):
    def __init__(self, parent, inventory_module, **kwargs):
        self.inventory_module = inventory_module
        self.product_service = ProductService()
        self.category_service = CategoryService()
        self.selected_product = None
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        ctk.CTkLabel(header_frame, text="Product Management", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Back", command=self.back_to_dashboard, width=80).pack(side="right", padx=10, pady=10)
        
        # Form - 3 fields per row
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", padx=10, pady=5)
        
        # Row 1
        ctk.CTkLabel(form_frame, text="Name:").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.name_input = ctk.CTkEntry(form_frame, width=150)
        self.name_input.grid(row=0, column=1, padx=5, pady=3)
        
        ctk.CTkLabel(form_frame, text="Code:").grid(row=0, column=2, padx=5, pady=3, sticky="w")
        self.code_input = ctk.CTkEntry(form_frame, width=120)
        self.code_input.grid(row=0, column=3, padx=5, pady=3)
        
        ctk.CTkLabel(form_frame, text="Price:").grid(row=0, column=4, padx=5, pady=3, sticky="w")
        self.price_input = ctk.CTkEntry(form_frame, width=100)
        self.price_input.grid(row=0, column=5, padx=5, pady=3)
        
        # Row 2
        ctk.CTkLabel(form_frame, text="Category:").grid(row=1, column=0, padx=5, pady=3, sticky="w")
        self.category_combo = create_searchable_dropdown(
            form_frame, 
            values=[], 
            width=150, 
            placeholder_text="Select Category..."
        )
        self.category_combo.grid(row=1, column=1, padx=5, pady=3)
        
        ctk.CTkLabel(form_frame, text="GST %:").grid(row=1, column=2, padx=5, pady=3, sticky="w")
        self.gst_input = ctk.CTkEntry(form_frame, width=120)
        self.gst_input.grid(row=1, column=3, padx=5, pady=3)
        
        ctk.CTkLabel(form_frame, text="Unit:").grid(row=1, column=4, padx=5, pady=3, sticky="w")
        self.unit_combo = create_searchable_dropdown(
            form_frame, 
            values=[], 
            width=100, 
            placeholder_text="Select Unit..."
        )
        self.unit_combo.grid(row=1, column=5, padx=5, pady=3)
        
        # Row 3
        ctk.CTkLabel(form_frame, text="HSN Code:").grid(row=2, column=0, padx=5, pady=3, sticky="w")
        self.hsn_code_input = ctk.CTkEntry(form_frame, width=150)
        self.hsn_code_input.grid(row=2, column=1, padx=5, pady=3)
        
        ctk.CTkLabel(form_frame, text="Schedule:").grid(row=2, column=2, padx=5, pady=3, sticky="w")
        self.schedule_combo = create_searchable_dropdown(
            form_frame, 
            values=["OTC", "Schedule H", "Schedule X"], 
            width=120, 
            placeholder_text="Select Schedule..."
        )
        self.schedule_combo.grid(row=2, column=3, padx=5, pady=3)
        
        ctk.CTkLabel(form_frame, text="Discontinued:").grid(row=2, column=4, padx=5, pady=3, sticky="w")
        self.discontinued_var = ctk.BooleanVar(value=False)
        self.discontinued_checkbox = ctk.CTkCheckBox(form_frame, text="Yes", variable=self.discontinued_var)
        self.discontinued_checkbox.grid(row=2, column=5, padx=5, pady=3, sticky="w")
        
        # Row 4
        ctk.CTkLabel(form_frame, text="Tags:").grid(row=3, column=0, padx=5, pady=3, sticky="w")
        self.tags_input = ctk.CTkEntry(form_frame, width=150, placeholder_text="#tag1 #tag2")
        self.tags_input.grid(row=3, column=1, padx=5, pady=3)
        
        ctk.CTkLabel(form_frame, text="Composition:").grid(row=3, column=2, padx=5, pady=3, sticky="w")
        self.composition_input = ctk.CTkEntry(form_frame, width=120)
        self.composition_input.grid(row=3, column=3, padx=5, pady=3)
        
        ctk.CTkLabel(form_frame, text="Manufacturer:").grid(row=3, column=4, padx=5, pady=3, sticky="w")
        self.manufacturer_input = ctk.CTkEntry(form_frame, width=100)
        self.manufacturer_input.grid(row=3, column=5, padx=5, pady=3)
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        self.save_btn = ctk.CTkButton(button_frame, text="Create", command=self.save_product, height=25, font=ctk.CTkFont(size=10))
        self.save_btn.pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Clear", command=self.clear_form, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
        self.add_import_button(button_frame)
        
        # Enhanced Data Grid with checkboxes and delete
        columns = [
            {'key': 'id', 'title': 'ID', 'width': 60},
            {'key': 'name', 'title': 'Name', 'width': 150},
            {'key': 'code', 'title': 'Code', 'width': 100},
            {'key': 'category_name', 'title': 'Category', 'width': 120},
            {'key': 'price', 'title': 'Price', 'width': 100},
            {'key': 'gst_percentage', 'title': 'GST%', 'width': 80},
            {'key': 'tags', 'title': 'Tags', 'width': 150},
            {'key': 'hsn_code', 'title': 'HSN', 'width': 100},
            {'key': 'schedule', 'title': 'Schedule', 'width': 100},
            {'key': 'manufacturer', 'title': 'Manufacturer', 'width': 150},
            {'key': 'unit_name', 'title': 'Unit', 'width': 80},
            {'key': 'is_discontinued', 'title': 'Status', 'width': 80}
        ]
        
        from core.shared.components.data_grid import DataGrid
        self.data_grid = DataGrid(
            self, 
            columns, 
            on_row_select=self.on_product_select,
            on_delete=self.on_product_delete,
            items_per_page=10,
            use_enhanced=True
        )
        self.data_grid.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.load_categories()
        self.load_units()
        self.load_products()
    
    def load_categories(self):
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import Category
        from core.shared.utils.session_manager import session_manager
        
        with db_manager.get_session() as session:
            query = session.query(Category)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(Category.tenant_id == tenant_id)
            categories = query.all()
            category_values = [f"{cat.id}:{cat.name}" for cat in categories]
            self.category_combo.configure_values(category_values)
    
    def load_units(self):
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import Unit
        
        with db_manager.get_session() as session:
            units = session.query(Unit).all()
            unit_values = [f"{unit.id}:{unit.name}" for unit in units]
            self.unit_combo.configure_values(unit_values)
    
    @ExceptionMiddleware.handle_exceptions("ProductScreen")
    def load_products(self):
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import Product, Category, Unit
        from core.shared.utils.session_manager import session_manager
        
        products_data = []
        
        with db_manager.get_session() as session:
            query = session.query(Product).join(Category).join(Unit)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(Product.tenant_id == tenant_id)
            products = query.all()
            
            for product in products:
                product_data = {
                    'id': product.id,
                    'name': product.name,
                    'code': product.code or '',
                    'tags': product.tags or '',
                    'composition': product.composition or '',
                    'category_id': product.category_id,
                    'category_name': product.category.name,
                    'unit_id': product.unit_id,
                    'unit_name': product.unit.name,
                    'price': f"₹{float(product.price):.2f}",
                    'gst_percentage': f"{float(product.gst_percentage or 0):.1f}%",
                    'hsn_code': product.hsn_code or '',
                    'schedule': product.schedule or '',
                    'manufacturer': product.manufacturer or '',
                    'is_discontinued': 'Discontinued' if product.is_discontinued else 'Active'
                }
                products_data.append(product_data)
        
        self.data_grid.set_data(products_data)
    
    def on_product_select(self, product_data):
        self.selected_product = product_data
        self.name_input.delete(0, tk.END)
        self.name_input.insert(0, product_data['name'])
        self.code_input.delete(0, tk.END)
        self.code_input.insert(0, product_data['code'])
        self.tags_input.delete(0, tk.END)
        self.tags_input.insert(0, product_data['tags'])
        self.category_combo.set(f"{product_data['category_id']}:{product_data['category_name']}")
        self.price_input.delete(0, tk.END)
        self.price_input.insert(0, product_data['price'].replace('₹', ''))
        self.gst_input.delete(0, tk.END)
        self.gst_input.insert(0, product_data['gst_percentage'].replace('%', ''))
        self.composition_input.delete(0, tk.END)
        self.composition_input.insert(0, product_data['composition'])
        self.discontinued_var.set(product_data['is_discontinued'] == 'Discontinued')
        self.hsn_code_input.delete(0, tk.END)
        self.hsn_code_input.insert(0, product_data.get('hsn_code', ''))
        self.schedule_combo.set(product_data.get('schedule', 'OTC'))
        self.manufacturer_input.delete(0, tk.END)
        self.manufacturer_input.insert(0, product_data.get('manufacturer', ''))
        self.unit_combo.set(f"{product_data['unit_id']}:{product_data['unit_name']}")
        self.save_btn.configure(text="Update")
    
    @ExceptionMiddleware.handle_exceptions("ProductScreen")
    def save_product(self):
        if not all([self.name_input.get(), self.category_combo.get(), self.price_input.get()]):
            self.show_message("Please fill required fields", "error")
            return
        
        try:
            category_id = extract_id_from_value(self.category_combo.get())
            unit_id = extract_id_from_value(self.unit_combo.get()) or 1
            
            if not category_id:
                self.show_message("Please select a valid category", "error")
                return
            product_data = {
                'name': self.name_input.get(),
                'code': self.code_input.get(),
                'tags': self.tags_input.get(),
                'composition': self.composition_input.get(),
                'hsn_code': self.hsn_code_input.get(),
                'schedule': self.schedule_combo.get(),
                'manufacturer': self.manufacturer_input.get(),
                'is_discontinued': self.discontinued_var.get(),
                'category_id': category_id,
                'unit_id': unit_id,
                'price': float(self.price_input.get()),
                'gst_percentage': float(self.gst_input.get() or 0)
            }
            
            if self.selected_product:
                # Update existing product
                self.product_service.update(self.selected_product['id'], product_data)
                self.show_message("Product updated successfully")
            else:
                # Create new product
                self.product_service.create(product_data)
                self.show_message("Product created successfully")
            
            self.clear_form()
            self.load_products()
        except Exception as e:
            action = "updating" if self.selected_product else "creating"
            self.show_message(f"Error {action} product: {str(e)}", "error")
    
    def clear_form(self):
        self.selected_product = None
        self.name_input.delete(0, tk.END)
        self.code_input.delete(0, tk.END)
        self.tags_input.delete(0, tk.END)
        self.category_combo.clear()
        self.price_input.delete(0, tk.END)
        self.gst_input.delete(0, tk.END)
        self.composition_input.delete(0, tk.END)
        self.discontinued_var.set(False)
        self.hsn_code_input.delete(0, tk.END)
        self.schedule_combo.clear()
        self.manufacturer_input.delete(0, tk.END)
        self.unit_combo.clear()
        self.save_btn.configure(text="Create")
    
    def download_template(self):
        template_data = {
            'name': ['Paracetamol 500mg', 'Vitamin C Tablets', 'Cough Syrup'],
            'code': ['PAR500', 'VITC100', 'COUGH250'],
            'category': ['Pharmacy', 'Nutrition & Supplements', 'Pharmacy'],
            'unit': ['Tablet', 'Tablet', 'Bottle'],
            'price': [25.50, 150.00, 85.00],
            'gst_percentage': [12.0, 18.0, 12.0],
            'tags': ['#fever #pain', '#vitamin #immunity', '#cough #cold'],
            'composition': ['Paracetamol 500mg', 'Ascorbic Acid 100mg', 'Dextromethorphan 15mg'],
            'hsn_code': ['30049099', '21069090', '30049099'],
            'schedule': ['OTC', 'OTC', 'Schedule H'],
            'manufacturer': ['ABC Pharma', 'XYZ Health', 'MediCorp']
        }
        self.create_template_file(template_data, 'products')
    
    def import_from_excel(self):
        def process_product_row(row, index):
            name = str(row['name']).strip()
            code = str(row.get('code', '')).strip()
            category_name = str(row['category']).strip()
            unit_name = str(row['unit']).strip()
            price = float(row['price'])
            
            if not name or not category_name or not unit_name or not price:
                return False
            
            # Find category and unit by name
            from core.database.connection import db_manager
            from modules.inventory_module.models.entities import Category, Unit
            from core.shared.utils.session_manager import session_manager
            
            with db_manager.get_session() as session:
                tenant_id = session_manager.get_current_tenant_id()
                category = session.query(Category).filter(
                    Category.name == category_name,
                    Category.tenant_id == tenant_id
                ).first()
                
                if not category:
                    raise Exception(f"Category '{category_name}' not found")
                
                unit = session.query(Unit).filter(
                    Unit.name == unit_name
                ).first()
                
                if not unit:
                    raise Exception(f"Unit '{unit_name}' not found")
                
                product_data = {
                    'name': name,
                    'code': code,
                    'category_id': category.id,
                    'unit_id': unit.id,
                    'price': price,
                    'gst_percentage': float(row.get('gst_percentage', 0)),
                    'tags': str(row.get('tags', '')).strip(),
                    'composition': str(row.get('composition', '')).strip(),
                    'hsn_code': str(row.get('hsn_code', '')).strip(),
                    'schedule': str(row.get('schedule', 'OTC')).strip(),
                    'manufacturer': str(row.get('manufacturer', '')).strip()
                }
                
                self.product_service.create(product_data)
            
            return True
        
        self.process_import_file(['name', 'category', 'unit', 'price'], process_product_row, 'products')
    
    @ExceptionMiddleware.handle_exceptions("ProductScreen")
    def on_product_delete(self, products_data):
        """Handle product deletion"""
        try:
            for product_data in products_data:
                self.product_service.delete(product_data['id'])
            
            self.show_message(f"Successfully deleted {len(products_data)} product(s)")
            self.clear_form()
            return True
        except Exception as e:
            self.show_message(f"Error deleting products: {str(e)}", "error")
            return False
    
    def load_data(self):
        self.load_products()
        self.load_categories()
        self.load_units()