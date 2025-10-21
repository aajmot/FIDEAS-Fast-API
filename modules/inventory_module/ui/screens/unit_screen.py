import customtkinter as ctk
import tkinter as tk
from core.shared.components.base_screen import BaseScreen
from modules.inventory_module.services.unit_service import UnitService
from core.shared.middleware.exception_handler import ExceptionMiddleware
from core.shared.components.import_mixin import ImportMixin

class UnitScreen(BaseScreen, ImportMixin):
    def __init__(self, parent, inventory_module, **kwargs):
        self.inventory_module = inventory_module
        self.unit_service = UnitService()
        self.selected_unit = None
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        ctk.CTkLabel(header_frame, text="Unit Master", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Back", command=self.back_to_dashboard, width=80).pack(side="right", padx=10, pady=10)
        
        # Form
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(form_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.name_input = ctk.CTkEntry(form_frame, width=200)
        self.name_input.grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Symbol:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.symbol_input = ctk.CTkEntry(form_frame, width=100)
        self.symbol_input.grid(row=0, column=3, padx=5, pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        self.save_btn = ctk.CTkButton(button_frame, text="Create", command=self.save_unit, height=25, font=ctk.CTkFont(size=10))
        self.save_btn.pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Clear", command=self.clear_form, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
        self.add_import_button(button_frame)
        
        # Data Grid
        columns = [
            {'key': 'id', 'title': 'ID', 'width': 40},
            {'key': 'name', 'title': 'Name', 'width': 150},
            {'key': 'symbol', 'title': 'Symbol', 'width': 80}
        ]
        
        from core.shared.components.data_grid import DataGrid
        self.data_grid = DataGrid(
            self, 
            columns, 
            on_row_select=self.on_unit_select,
            on_delete=self.on_unit_delete,
            items_per_page=10,
            use_enhanced=True
        )
        self.data_grid.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.load_units()
    
    @ExceptionMiddleware.handle_exceptions("UnitScreen")
    def load_units(self):
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import Unit
        
        units_data = []
        
        with db_manager.get_session() as session:
            units = session.query(Unit).all()
            
            for unit in units:
                unit_data = {
                    'id': unit.id,
                    'name': unit.name,
                    'symbol': unit.symbol or ''
                }
                units_data.append(unit_data)
        
        self.data_grid.set_data(units_data)
    
    def on_unit_select(self, unit_data):
        self.selected_unit = unit_data
        self.name_input.delete(0, tk.END)
        self.name_input.insert(0, unit_data['name'])
        self.symbol_input.delete(0, tk.END)
        self.symbol_input.insert(0, unit_data['symbol'])
        self.save_btn.configure(text="Update")
    
    @ExceptionMiddleware.handle_exceptions("UnitScreen")
    def save_unit(self):
        if not self.name_input.get():
            self.show_message("Please enter unit name", "error")
            return
        
        try:
            unit_data = {
                'name': self.name_input.get(),
                'symbol': self.symbol_input.get()
            }
            
            if self.selected_unit:
                self.unit_service.update(self.selected_unit['id'], unit_data)
                self.show_message("Unit updated successfully")
            else:
                self.unit_service.create(unit_data)
                self.show_message("Unit created successfully")
            
            self.clear_form()
            self.load_units()
        except Exception as e:
            action = "updating" if self.selected_unit else "creating"
            self.show_message(f"Error {action} unit: {str(e)}", "error")
    
    def clear_form(self):
        self.selected_unit = None
        self.name_input.delete(0, tk.END)
        self.symbol_input.delete(0, tk.END)
        self.save_btn.configure(text="Create")
    
    def download_template(self):
        template_data = {
            'Name': ['Kilogram', 'Gram', 'Liter'],
            'Symbol': ['kg', 'g', 'l']
        }
        self.create_template_file(template_data, 'units')
    
    def import_from_excel(self):
        def process_unit_row(row, index):
            name = str(row['Name']).strip()
            symbol = str(row.get('Symbol', '')).strip()
            
            if not name:
                return False
            
            unit_data = {
                'name': name,
                'symbol': symbol
            }
            
            self.unit_service.create(unit_data)
            return True
        
        self.process_import_file(['Name'], process_unit_row, 'units')
    
    @ExceptionMiddleware.handle_exceptions("UnitScreen")
    def on_unit_delete(self, units_data):
        """Handle unit deletion"""
        try:
            for unit_data in units_data:
                self.unit_service.delete(unit_data['id'])
            
            self.show_message(f"Successfully deleted {len(units_data)} unit(s)")
            self.clear_form()
            return True
        except Exception as e:
            self.show_message(f"Error deleting units: {str(e)}", "error")
            return False
    
    def load_data(self):
        self.load_units()