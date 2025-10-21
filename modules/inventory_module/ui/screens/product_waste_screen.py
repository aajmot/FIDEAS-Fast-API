import customtkinter as ctk
import tkinter as tk
from datetime import datetime
from core.shared.components.base_screen import BaseScreen
from core.shared.components.searchable_dropdown import SearchableDropdown
from modules.inventory_module.services.product_waste_service import ProductWasteService
from core.shared.middleware.exception_handler import ExceptionMiddleware

class ProductWasteScreen(BaseScreen):
    def __init__(self, parent, inventory_module, **kwargs):
        self.inventory_module = inventory_module
        self.product_waste_service = ProductWasteService()
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        ctk.CTkLabel(header_frame, text="Product Waste Management", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Back", command=self.back_to_dashboard, width=80).pack(side="right", padx=10, pady=10)
        
        # Form
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", padx=10, pady=5)
        
        # Row 1
        ctk.CTkLabel(form_frame, text="Waste Number:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.waste_number_entry = ctk.CTkEntry(form_frame, width=200)
        self.waste_number_entry.grid(row=0, column=1, padx=5, pady=5)
        self.generate_waste_number()
        
        ctk.CTkLabel(form_frame, text="Date:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.date_entry = ctk.CTkEntry(form_frame, width=150, placeholder_text="YYYY-MM-DD")
        self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.date_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # Row 2
        ctk.CTkLabel(form_frame, text="Product:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.product_combo = SearchableDropdown(
            form_frame, 
            values=[], 
            width=200, 
            placeholder_text="Search product...",
            command=self.on_product_select
        )
        self.product_combo.grid(row=1, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Batch Number:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.batch_entry = ctk.CTkEntry(form_frame, width=150)
        self.batch_entry.grid(row=1, column=3, padx=5, pady=5)
        
        # Row 3
        ctk.CTkLabel(form_frame, text="Quantity:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.quantity_entry = ctk.CTkEntry(form_frame, width=200)
        self.quantity_entry.bind("<KeyRelease>", self.calculate_total)
        self.quantity_entry.grid(row=2, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Unit Cost:").grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.unit_cost_entry = ctk.CTkEntry(form_frame, width=150)
        self.unit_cost_entry.bind("<KeyRelease>", self.calculate_total)
        self.unit_cost_entry.grid(row=2, column=3, padx=5, pady=5)
        
        # Row 4
        ctk.CTkLabel(form_frame, text="Total Cost:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.total_cost_label = ctk.CTkLabel(form_frame, text="₹0.00", font=ctk.CTkFont(weight="bold"))
        self.total_cost_label.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(form_frame, text="Reason:").grid(row=3, column=2, padx=5, pady=5, sticky="w")
        self.reason_entry = ctk.CTkEntry(form_frame, width=150)
        self.reason_entry.grid(row=3, column=3, padx=5, pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        self.save_btn = ctk.CTkButton(button_frame, text="Record Waste", command=self.record_waste, height=25, font=ctk.CTkFont(size=10))
        self.save_btn.pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Clear", command=self.clear_form, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
        
        # Data Grid
        columns = [
            {'key': 'waste_number', 'title': 'Waste No', 'width': 100},
            {'key': 'product_name', 'title': 'Product', 'width': 150},
            {'key': 'batch_number', 'title': 'Batch', 'width': 80},
            {'key': 'quantity', 'title': 'Quantity', 'width': 70},
            {'key': 'unit_cost', 'title': 'Unit Cost', 'width': 80},
            {'key': 'total_cost', 'title': 'Total Cost', 'width': 80},
            {'key': 'reason', 'title': 'Reason', 'width': 200},
            {'key': 'waste_date', 'title': 'Date', 'width': 100}
        ]
        
        from core.shared.components.data_grid import DataGrid
        self.data_grid = DataGrid(
            self, 
            columns, 
            on_row_select=self.on_waste_select,
            on_delete=self.on_waste_delete,
            items_per_page=10,
            use_enhanced=True
        )
        self.data_grid.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.load_products()
        self.load_waste_records()
    
    def load_waste_records(self):
        waste_data = []
        wastes = self.product_waste_service.get_all(page=1, page_size=1000)  # Load all for grid
        
        for waste in wastes:
            waste_record = {
                'id': waste.id,
                'waste_number': waste.waste_number,
                'product_name': waste.product_name,
                'batch_number': waste.batch_number or '',
                'quantity': f"{float(waste.quantity):.1f}",
                'unit_cost': f"₹{float(waste.unit_cost):.2f}",
                'total_cost': f"₹{float(waste.total_cost):.2f}",
                'reason': waste.reason[:50] + "..." if len(waste.reason) > 50 else waste.reason,
                'waste_date': waste.waste_date.strftime('%Y-%m-%d')
            }
            waste_data.append(waste_record)
        
        self.data_grid.set_data(waste_data)
    
    def on_waste_select(self, waste_data):
        # For viewing only - waste records are not editable
        pass
    

    
    def generate_waste_number(self):
        waste_number = f"WS-{datetime.now().strftime('%d%m%Y%H%M%S%f')[:-3]}"
        self.waste_number_entry.delete(0, tk.END)
        self.waste_number_entry.insert(0, waste_number)
        self.waste_number_entry.configure(state="readonly")
    
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
            self.product_values = [f"{prod.id}:{prod.name}" for prod in products]
            self.product_combo.configure_values(self.product_values)
    
    def on_product_select(self, value):
        if value and ':' in value:
            product_id = int(value.split(':')[0])
            self.populate_product_cost(product_id)
    
    def populate_product_cost(self, product_id):
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import Product
        
        with db_manager.get_session() as session:
            product = session.query(Product).filter(Product.id == product_id).first()
            if product:
                self.unit_cost_entry.delete(0, tk.END)
                self.unit_cost_entry.insert(0, f"{float(product.price):.2f}")
                self.calculate_total()
    
    def calculate_total(self, event=None):
        try:
            quantity = float(self.quantity_entry.get() or 0)
            unit_cost = float(self.unit_cost_entry.get() or 0)
            total = quantity * unit_cost
            self.total_cost_label.configure(text=f"₹{total:.2f}")
        except ValueError:
            self.total_cost_label.configure(text="₹0.00")
    
    @ExceptionMiddleware.handle_exceptions("ProductWasteScreen")
    def record_waste(self):
        if not self.validate_form():
            return
        
        try:
            waste_data = {
                'waste_number': self.waste_number_entry.get(),
                'product_id': int(self.product_combo.get().split(':')[0]),
                'batch_number': self.batch_entry.get(),
                'quantity': float(self.quantity_entry.get()),
                'unit_cost': float(self.unit_cost_entry.get()),
                'reason': self.reason_entry.get(),
                'waste_date': datetime.strptime(self.date_entry.get(), '%Y-%m-%d')
            }
            
            self.product_waste_service.create(waste_data)
            self.show_message("Product waste recorded successfully")
            self.clear_form()
            self.load_waste_records()
        except Exception as e:
            self.show_message(f"Error recording waste: {str(e)}", "error")
    
    def validate_form(self):
        if not all([self.product_combo.get(), self.quantity_entry.get(), self.unit_cost_entry.get(), self.reason_entry.get().strip()]):
            self.show_message("Please fill all required fields", "error")
            return False
        
        try:
            if float(self.quantity_entry.get()) <= 0 or float(self.unit_cost_entry.get()) <= 0:
                self.show_message("Quantity and unit cost must be greater than 0", "error")
                return False
        except ValueError:
            self.show_message("Please enter valid numbers for quantity and unit cost", "error")
            return False
        
        return True
    
    def clear_form(self):
        self.waste_number_entry.configure(state="normal")
        self.generate_waste_number()
        self.product_combo.clear()
        self.batch_entry.delete(0, tk.END)
        self.quantity_entry.delete(0, tk.END)
        self.unit_cost_entry.delete(0, tk.END)
        self.reason_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.total_cost_label.configure(text="₹0.00")
        self.save_btn.configure(text="Record Waste")
    @ExceptionMiddleware.handle_exceptions("WasteScreen")
    def on_waste_delete(self, wastes_data):
        """Handle waste deletion"""
        try:
            for waste_data in wastes_data:
                self.waste_service.delete(waste_data['id'])
            
            self.show_message(f"Successfully deleted {len(wastes_data)} waste(s)")
            self.clear_form()
            return True
        except Exception as e:
            self.show_message(f"Error deleting wastes: {str(e)}", "error")
            return False