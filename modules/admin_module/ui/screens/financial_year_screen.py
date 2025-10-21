import customtkinter as ctk
import tkinter as tk
from datetime import datetime
from core.shared.components.base_screen import BaseScreen
from core.shared.components.modern_calendar import ModernCalendar
from modules.admin_module.services.financial_year_service import FinancialYearService
from core.shared.middleware.exception_handler import ExceptionMiddleware

class FinancialYearScreen(BaseScreen):
    def __init__(self, parent, admin_module, **kwargs):
        self.admin_module = admin_module
        self.financial_year_service = FinancialYearService()
        self.selected_fy = None
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(header_frame, text="Financial Year Management", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Back", command=self.back_to_dashboard, width=80).pack(side="right", padx=10, pady=10)
        
        # Form frame
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", padx=10, pady=5)
        
        # Form fields
        ctk.CTkLabel(form_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.name_entry = ctk.CTkEntry(form_frame, width=200)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Code:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.code_entry = ctk.CTkEntry(form_frame, width=200)
        self.code_entry.grid(row=0, column=3, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Start Date:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        start_date_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        start_date_frame.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.start_date_entry = ctk.CTkEntry(start_date_frame, width=150, placeholder_text="YYYY-MM-DD")
        self.start_date_entry.pack(side="left")
        ctk.CTkButton(start_date_frame, text="📅", width=35, height=25, 
                     command=self.open_start_date_calendar,
                     fg_color=("#3B8ED0", "#1F6AA5"),
                     hover_color=("#36719F", "#144870")).pack(side="left", padx=(5, 0))
        
        ctk.CTkLabel(form_frame, text="End Date:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        end_date_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        end_date_frame.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        self.end_date_entry = ctk.CTkEntry(end_date_frame, width=150, placeholder_text="YYYY-MM-DD")
        self.end_date_entry.pack(side="left")
        ctk.CTkButton(end_date_frame, text="📅", width=35, height=25, 
                     command=self.open_end_date_calendar,
                     fg_color=("#3B8ED0", "#1F6AA5"),
                     hover_color=("#36719F", "#144870")).pack(side="left", padx=(5, 0))
        
        ctk.CTkLabel(form_frame, text="Is Current:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.is_current_var = ctk.BooleanVar()
        self.is_current_checkbox = ctk.CTkCheckBox(form_frame, text="Current Financial Year", variable=self.is_current_var)
        self.is_current_checkbox.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        self.save_btn = ctk.CTkButton(button_frame, text="Create", command=self.save_financial_year, height=25, font=ctk.CTkFont(size=10))
        self.save_btn.pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Clear", command=self.clear_form, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
        
        # Data Grid
        columns = [
            {'key': 'id', 'title': 'ID', 'width': 40},
            {'key': 'name', 'title': 'Name', 'width': 150},
            {'key': 'code', 'title': 'Code', 'width': 100},
            {'key': 'start_date', 'title': 'Start Date', 'width': 100},
            {'key': 'end_date', 'title': 'End Date', 'width': 100},
            {'key': 'is_current', 'title': 'Current', 'width': 80}
        ]
        
        from core.shared.components.data_grid import DataGrid
        self.data_grid = DataGrid(
            self, 
            columns, 
            on_row_select=self.on_fy_select,
            on_delete=self.on_fy_delete,
            items_per_page=10,
            use_enhanced=True
        )
        self.data_grid.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.load_financial_years()
    
    def open_start_date_calendar(self):
        self.open_modern_calendar(self.start_date_entry)
    
    def open_end_date_calendar(self):
        self.open_modern_calendar(self.end_date_entry)
    
    def open_modern_calendar(self, entry_widget):
        from datetime import datetime, date
        
        # Get current date from entry or default to today
        try:
            initial_date = datetime.strptime(entry_widget.get(), '%Y-%m-%d').date() if entry_widget.get() else date.today()
        except ValueError:
            initial_date = date.today()
        
        # Callback to update entry
        def on_date_selected(date_str):
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, date_str)
        
        # Open modern calendar
        ModernCalendar(self, on_date_selected, initial_date)
    
    @ExceptionMiddleware.handle_exceptions("FinancialYearScreen")
    def save_financial_year(self):
        if not self.validate_form():
            return
        
        try:
            fy_data = {
                'name': self.name_entry.get(),
                'code': self.code_entry.get(),
                'start_date': datetime.strptime(self.start_date_entry.get(), '%Y-%m-%d'),
                'end_date': datetime.strptime(self.end_date_entry.get(), '%Y-%m-%d'),
                'is_current': self.is_current_var.get()
            }
            
            if self.selected_fy:
                # Update existing financial year
                self.financial_year_service.update(self.selected_fy['id'], fy_data)
                self.show_message("Financial year updated successfully")
            else:
                # Create new financial year
                self.financial_year_service.create(fy_data)
                self.show_message("Financial year created successfully")
            
            self.clear_form()
            self.load_financial_years()
        except Exception as e:
            action = "updating" if self.selected_fy else "creating"
            self.show_message(f"Error {action} financial year: {str(e)}", "error")
    
    def validate_form(self):
        if not all([self.name_entry.get().strip(), self.code_entry.get().strip(), self.start_date_entry.get(), self.end_date_entry.get()]):
            self.show_message("Please fill all required fields", "error")
            return False
        
        try:
            start_date = datetime.strptime(self.start_date_entry.get(), '%Y-%m-%d')
            end_date = datetime.strptime(self.end_date_entry.get(), '%Y-%m-%d')
            
            if start_date >= end_date:
                self.show_message("Start date must be before end date", "error")
                return False
        except ValueError:
            self.show_message("Please enter valid dates in YYYY-MM-DD format", "error")
            return False
        
        return True
    
    def load_financial_years(self):
        fy_data = []
        financial_years = self.financial_year_service.get_all()
        
        for fy in financial_years:
            fy_record = {
                'id': fy.id,
                'name': fy.name,
                'code': fy.code,
                'start_date': fy.start_date.strftime('%Y-%m-%d'),
                'end_date': fy.end_date.strftime('%Y-%m-%d'),
                'is_current': 'Yes' if fy.is_current else 'No'
            }
            fy_data.append(fy_record)
        
        self.data_grid.set_data(fy_data)
    
    def on_fy_select(self, fy_data):
        self.selected_fy = fy_data
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, fy_data['name'])
        self.code_entry.delete(0, tk.END)
        self.code_entry.insert(0, fy_data['code'])
        self.start_date_entry.delete(0, tk.END)
        self.start_date_entry.insert(0, fy_data['start_date'])
        self.end_date_entry.delete(0, tk.END)
        self.end_date_entry.insert(0, fy_data['end_date'])
        self.is_current_var.set(fy_data['is_current'] == 'Yes')
        self.save_btn.configure(text="Update")
    
    def clear_form(self):
        self.selected_fy = None
        self.name_entry.delete(0, tk.END)
        self.code_entry.delete(0, tk.END)
        self.start_date_entry.delete(0, tk.END)
        self.end_date_entry.delete(0, tk.END)
        self.is_current_var.set(False)
        self.save_btn.configure(text="Create")
    @ExceptionMiddleware.handle_exceptions("FyScreen")
    def on_fy_delete(self, fys_data):
        """Handle fy deletion"""
        try:
            for fy_data in fys_data:
                self.fy_service.delete(fy_data['id'])
            
            self.show_message(f"Successfully deleted {len(fys_data)} fy(s)")
            self.clear_form()
            return True
        except Exception as e:
            self.show_message(f"Error deleting fys: {str(e)}", "error")
            return False