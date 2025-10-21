import customtkinter as ctk
import tkinter as tk
from core.shared.components.base_screen import BaseScreen
from modules.inventory_module.services.customer_service import CustomerService
from core.shared.middleware.exception_handler import ExceptionMiddleware
from core.shared.components.import_mixin import ImportMixin

class CustomerScreen(BaseScreen, ImportMixin):
    def __init__(self, parent, inventory_module, **kwargs):
        self.inventory_module = inventory_module
        self.customer_service = CustomerService()
        self.selected_customer = None
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        ctk.CTkLabel(header_frame, text="Customer Management", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Back", command=self.back_to_dashboard, width=80).pack(side="right", padx=10, pady=10)
        
        # Form
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(form_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.name_input = ctk.CTkEntry(form_frame, width=200)
        self.name_input.grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Phone:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.phone_input = ctk.CTkEntry(form_frame, width=150)
        self.phone_input.grid(row=0, column=3, padx=5, pady=5)
        self.phone_input.bind("<FocusOut>", self.check_phone_duplicate)
        
        ctk.CTkLabel(form_frame, text="Email:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.email_input = ctk.CTkEntry(form_frame, width=200)
        self.email_input.grid(row=1, column=1, padx=5, pady=5)
        self.email_input.bind("<FocusOut>", self.check_email_duplicate)
        
        ctk.CTkLabel(form_frame, text="Age:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.age_input = ctk.CTkEntry(form_frame, width=150)
        self.age_input.grid(row=1, column=3, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Tax ID:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.tax_id_input = ctk.CTkEntry(form_frame, width=200)
        self.tax_id_input.grid(row=2, column=1, padx=5, pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        self.save_btn = ctk.CTkButton(button_frame, text="Create", command=self.save_customer, height=25, font=ctk.CTkFont(size=10))
        self.save_btn.pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Clear", command=self.clear_form, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
        self.add_import_button(button_frame)
        
        # Data Grid
        columns = [
            {'key': 'id', 'title': 'ID', 'width': 40},
            {'key': 'name', 'title': 'Name', 'width': 150},
            {'key': 'phone', 'title': 'Phone', 'width': 120},
            {'key': 'email', 'title': 'Email', 'width': 150},
            {'key': 'age', 'title': 'Age', 'width': 60},
            {'key': 'tax_id', 'title': 'Tax ID', 'width': 120}
        ]
        
        from core.shared.components.data_grid import DataGrid
        self.data_grid = DataGrid(
            self, 
            columns, 
            on_row_select=self.on_customer_select,
            on_delete=self.on_customer_delete,
            items_per_page=10,
            use_enhanced=True
        )
        self.data_grid.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.load_customers()
    
    def check_phone_duplicate(self, event):
        phone = self.phone_input.get().strip()
        if not phone or (self.selected_customer and self.selected_customer['phone'] == phone):
            return
        
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import Customer
        from core.shared.utils.session_manager import session_manager
        
        with db_manager.get_session() as session:
            existing = session.query(Customer).filter(
                Customer.phone == phone,
                Customer.tenant_id == session_manager.get_current_tenant_id()
            ).first()
            
            if existing:
                self.show_message("Phone number already exists", "error")
                self.phone_input.focus()
    
    def check_email_duplicate(self, event):
        email = self.email_input.get().strip()
        if not email or (self.selected_customer and self.selected_customer['email'] == email):
            return
        
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import Customer
        from core.shared.utils.session_manager import session_manager
        
        with db_manager.get_session() as session:
            existing = session.query(Customer).filter(
                Customer.email == email,
                Customer.tenant_id == session_manager.get_current_tenant_id()
            ).first()
            
            if existing:
                self.show_message("Email already exists", "error")
                self.email_input.focus()
    
    @ExceptionMiddleware.handle_exceptions("CustomerScreen")
    def load_customers(self):
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import Customer
        from core.shared.utils.session_manager import session_manager
        
        customers_data = []
        
        with db_manager.get_session() as session:
            query = session.query(Customer)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(Customer.tenant_id == tenant_id)
            customers = query.all()
            
            for customer in customers:
                customer_data = {
                    'id': customer.id,
                    'name': customer.name,
                    'phone': customer.phone,
                    'email': customer.email or '',
                    'age': customer.age or '',
                    'tax_id': customer.tax_id or ''
                }
                customers_data.append(customer_data)
        
        self.data_grid.set_data(customers_data)
    
    def on_customer_select(self, customer_data):
        self.selected_customer = customer_data
        self.name_input.delete(0, tk.END)
        self.name_input.insert(0, customer_data['name'])
        self.phone_input.delete(0, tk.END)
        self.phone_input.insert(0, customer_data['phone'])
        self.email_input.delete(0, tk.END)
        self.email_input.insert(0, customer_data['email'])
        self.age_input.delete(0, tk.END)
        self.age_input.insert(0, str(customer_data['age']) if customer_data['age'] else '')
        self.tax_id_input.delete(0, tk.END)
        self.tax_id_input.insert(0, customer_data['tax_id'])
        self.save_btn.configure(text="Update")
    
    @ExceptionMiddleware.handle_exceptions("CustomerScreen")
    def save_customer(self):
        if not all([self.name_input.get(), self.phone_input.get()]):
            self.show_message("Please enter name and phone", "error")
            return
        
        try:
            customer_data = {
                'name': self.name_input.get(),
                'phone': self.phone_input.get(),
                'email': self.email_input.get(),
                'age': int(self.age_input.get()) if self.age_input.get() else None,
                'tax_id': self.tax_id_input.get()
            }
            
            if self.selected_customer:
                # Update existing customer
                self.customer_service.update(self.selected_customer['id'], customer_data)
                self.show_message("Customer updated successfully")
            else:
                # Create new customer
                self.customer_service.create(customer_data)
                self.show_message("Customer created successfully")
            
            self.clear_form()
            self.load_customers()
        except Exception as e:
            action = "updating" if self.selected_customer else "creating"
            self.show_message(f"Error {action} customer: {str(e)}", "error")
    
    def clear_form(self):
        self.selected_customer = None
        self.name_input.delete(0, tk.END)
        self.phone_input.delete(0, tk.END)
        self.email_input.delete(0, tk.END)
        self.age_input.delete(0, tk.END)
        self.tax_id_input.delete(0, tk.END)
        self.save_btn.configure(text="Create")
    
    def download_template(self):
        template_data = {
            'Name': ['John Doe', 'Jane Smith', 'Mike Johnson'],
            'Phone': ['1234567890', '0987654321', '5555555555'],
            'Email': ['john@example.com', 'jane@example.com', 'mike@example.com'],
            'Age': [30, 25, 35],
            'Tax_ID': ['TAX001', 'TAX002', 'TAX003']
        }
        self.create_template_file(template_data, 'customers')
    
    def import_from_excel(self):
        def process_customer_row(row, index):
            name = str(row['Name']).strip()
            phone = str(row['Phone']).strip()
            email = str(row.get('Email', '')).strip()
            age = row.get('Age', None)
            
            if not name or not phone:
                return False
            
            customer_data = {
                'name': name,
                'phone': phone,
                'email': email,
                'age': int(age) if age and str(age).isdigit() else None,
                'tax_id': str(row.get('Tax_ID', '')).strip()
            }
            
            self.customer_service.create(customer_data)
            return True
        
        self.process_import_file(['Name', 'Phone'], process_customer_row, 'customers')
    
    @ExceptionMiddleware.handle_exceptions("CustomerScreen")
    def on_customer_delete(self, customers_data):
        """Handle customer deletion"""
        try:
            for customer_data in customers_data:
                self.customer_service.delete(customer_data['id'])
            
            self.show_message(f"Successfully deleted {len(customers_data)} customer(s)")
            self.clear_form()
            return True
        except Exception as e:
            self.show_message(f"Error deleting customers: {str(e)}", "error")
            return False
    
    def load_data(self):
        self.load_customers()