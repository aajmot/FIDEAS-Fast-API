import customtkinter as ctk
import tkinter as tk
from core.shared.components.base_screen import BaseScreen
from modules.inventory_module.services.supplier_service import SupplierService
from core.shared.middleware.exception_handler import ExceptionMiddleware

class SupplierScreen(BaseScreen):
    def __init__(self, parent, inventory_module, **kwargs):
        self.inventory_module = inventory_module
        self.supplier_service = SupplierService()
        self.selected_supplier = None
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Title and back button
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(header_frame, text="Supplier Management", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Back", command=self.back_to_dashboard, width=80).pack(side="right", padx=10, pady=10)
        
        # Form frame
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", padx=10, pady=5)
        
        # Form fields
        ctk.CTkLabel(form_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.name_input = ctk.CTkEntry(form_frame, width=200)
        self.name_input.grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Phone:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.phone_input = ctk.CTkEntry(form_frame, width=200)
        self.phone_input.grid(row=0, column=3, padx=5, pady=5)
        self.phone_input.bind("<FocusOut>", self.check_phone_duplicate)
        
        ctk.CTkLabel(form_frame, text="Email:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.email_input = ctk.CTkEntry(form_frame, width=200)
        self.email_input.grid(row=1, column=1, padx=5, pady=5)
        self.email_input.bind("<FocusOut>", self.check_email_duplicate)
        
        ctk.CTkLabel(form_frame, text="Tax ID:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.tax_id_input = ctk.CTkEntry(form_frame, width=200)
        self.tax_id_input.grid(row=1, column=3, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Contact Person:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.contact_person_input = ctk.CTkEntry(form_frame, width=200)
        self.contact_person_input.grid(row=2, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Address:").grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.address_input = ctk.CTkEntry(form_frame, width=200)
        self.address_input.grid(row=2, column=3, padx=5, pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        self.save_btn = ctk.CTkButton(button_frame, text="Create", command=self.save_supplier, height=25, font=ctk.CTkFont(size=10))
        self.save_btn.pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Clear", command=self.clear_form, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Import Excel", command=self.import_from_excel, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Download Template", command=self.download_template, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
        
        # Data Grid
        columns = [
            {'key': 'id', 'title': 'ID', 'width': 40},
            {'key': 'name', 'title': 'Name', 'width': 150},
            {'key': 'phone', 'title': 'Phone', 'width': 120},
            {'key': 'email', 'title': 'Email', 'width': 150},
            {'key': 'tax_id', 'title': 'Tax ID', 'width': 100}
        ]
        
        from core.shared.components.data_grid import DataGrid
        self.data_grid = DataGrid(
            self, 
            columns, 
            on_row_select=self.on_supplier_select,
            on_delete=self.on_supplier_delete,
            items_per_page=10,
            use_enhanced=True
        )
        self.data_grid.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.load_suppliers()
    
    def check_phone_duplicate(self, event):
        phone = self.phone_input.get().strip()
        if not phone or (self.selected_supplier and self.selected_supplier['phone'] == phone):
            return
        
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import Supplier
        from core.shared.utils.session_manager import session_manager
        
        with db_manager.get_session() as session:
            existing = session.query(Supplier).filter(
                Supplier.phone == phone,
                Supplier.tenant_id == session_manager.get_current_tenant_id()
            ).first()
            
            if existing:
                self.show_message("Phone number already exists", "error")
                self.phone_input.focus()
    
    def check_email_duplicate(self, event):
        email = self.email_input.get().strip()
        if not email or (self.selected_supplier and self.selected_supplier['email'] == email):
            return
        
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import Supplier
        from core.shared.utils.session_manager import session_manager
        
        with db_manager.get_session() as session:
            existing = session.query(Supplier).filter(
                Supplier.email == email,
                Supplier.tenant_id == session_manager.get_current_tenant_id()
            ).first()
            
            if existing:
                self.show_message("Email already exists", "error")
                self.email_input.focus()
    
    @ExceptionMiddleware.handle_exceptions("SupplierScreen")
    def load_suppliers(self):
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import Supplier
        from core.shared.utils.session_manager import session_manager
        
        suppliers_data = []
        
        with db_manager.get_session() as session:
            query = session.query(Supplier)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(Supplier.tenant_id == tenant_id)
            suppliers = query.all()
            
            for supplier in suppliers:
                supplier_data = {
                    'id': supplier.id,
                    'name': supplier.name,
                    'phone': supplier.phone,
                    'email': supplier.email or '',
                    'tax_id': supplier.tax_id or '',
                    'contact_person': supplier.contact_person or '',
                    'address': supplier.address or ''
                }
                suppliers_data.append(supplier_data)
        
        self.data_grid.set_data(suppliers_data)
    
    def on_supplier_select(self, supplier_data):
        self.selected_supplier = supplier_data
        self.name_input.delete(0, tk.END)
        self.name_input.insert(0, supplier_data['name'])
        self.phone_input.delete(0, tk.END)
        self.phone_input.insert(0, supplier_data['phone'])
        self.email_input.delete(0, tk.END)
        self.email_input.insert(0, supplier_data['email'])
        self.tax_id_input.delete(0, tk.END)
        self.tax_id_input.insert(0, supplier_data['tax_id'])
        self.contact_person_input.delete(0, tk.END)
        self.contact_person_input.insert(0, supplier_data['contact_person'])
        self.address_input.delete(0, tk.END)
        self.address_input.insert(0, supplier_data['address'])
        self.save_btn.configure(text="Update")
    
    @ExceptionMiddleware.handle_exceptions("SupplierScreen")
    def save_supplier(self):
        if not all([self.name_input.get(), self.phone_input.get()]):
            self.show_message("Please enter name and phone", "error")
            return
        
        try:
            supplier_data = {
                'name': self.name_input.get(),
                'phone': self.phone_input.get(),
                'email': self.email_input.get(),
                'tax_id': self.tax_id_input.get(),
                'contact_person': self.contact_person_input.get(),
                'address': self.address_input.get()
            }
            
            if self.selected_supplier:
                # Update existing supplier
                self.supplier_service.update(self.selected_supplier['id'], supplier_data)
                self.show_message("Supplier updated successfully")
            else:
                # Create new supplier
                self.supplier_service.create(supplier_data)
                self.show_message("Supplier created successfully")
            
            self.clear_form()
            self.load_suppliers()
        except Exception as e:
            action = "updating" if self.selected_supplier else "creating"
            self.show_message(f"Error {action} supplier: {str(e)}", "error")
    
    def clear_form(self):
        self.selected_supplier = None
        self.name_input.delete(0, tk.END)
        self.phone_input.delete(0, tk.END)
        self.email_input.delete(0, tk.END)
        self.tax_id_input.delete(0, tk.END)
        self.contact_person_input.delete(0, tk.END)
        self.address_input.delete(0, tk.END)
        self.save_btn.configure(text="Create")
    
    @ExceptionMiddleware.handle_exceptions("SupplierScreen")
    def import_from_excel(self):
        """Import suppliers from Excel file"""
        from tkinter import filedialog, messagebox
        
        try:
            import pandas as pd
            
            filename = filedialog.askopenfilename(
                filetypes=[("Excel files", "*.xlsx *.xls")],
                title="Select Excel file to import"
            )
            
            if not filename:
                return
            
            df = pd.read_excel(filename)
            
            required_columns = ['Name', 'Phone']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                messagebox.showerror("Error", f"Missing required columns: {', '.join(missing_columns)}")
                return
            
            success_count = 0
            error_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    name = str(row['Name']).strip()
                    phone = str(row['Phone']).strip()
                    
                    if not name or not phone:
                        errors.append(f"Row {index + 2}: Name and Phone are required")
                        error_count += 1
                        continue
                    
                    supplier_data = {
                        'name': name,
                        'phone': phone,
                        'email': str(row.get('Email', '')).strip(),
                        'tax_id': str(row.get('Tax ID', '')).strip(),
                        'contact_person': str(row.get('Contact Person', '')).strip(),
                        'address': str(row.get('Address', '')).strip()
                    }
                    
                    self.supplier_service.create(supplier_data)
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")
                    error_count += 1
            
            if success_count > 0:
                self.load_suppliers()
            
            message = f"Import completed:\n- Successfully imported: {success_count} suppliers\n- Errors: {error_count}"
            if errors:
                message += f"\n\nErrors:\n" + "\n".join(errors[:10])
                if len(errors) > 10:
                    message += f"\n... and {len(errors) - 10} more errors"
            
            if error_count > 0:
                messagebox.showwarning("Import Results", message)
            else:
                messagebox.showinfo("Success", message)
                
        except ImportError:
            messagebox.showerror("Error", "pandas library is required for Excel import. Install with: pip install pandas openpyxl")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import suppliers: {str(e)}")
    
    @ExceptionMiddleware.handle_exceptions("SupplierScreen")
    def download_template(self):
        """Download Excel template for suppliers import"""
        from tkinter import filedialog, messagebox
        
        try:
            import pandas as pd
            
            template_data = {
                'Name': ['ABC Suppliers Ltd', 'XYZ Trading Co'],
                'Phone': ['+1234567890', '+0987654321'],
                'Email': ['contact@abc.com', 'info@xyz.com'],
                'Tax ID': ['TAX001', 'TAX002'],
                'Contact Person': ['John Doe', 'Jane Smith'],
                'Address': ['123 Main St, City', '456 Oak Ave, Town']
            }
            
            df = pd.DataFrame(template_data)
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile="suppliers_import_template.xlsx"
            )
            
            if filename:
                df.to_excel(filename, index=False, sheet_name='Suppliers Template')
                messagebox.showinfo("Success", f"Template downloaded to {filename}")
                
        except ImportError:
            messagebox.showerror("Error", "pandas library is required. Install with: pip install pandas openpyxl")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to download template: {str(e)}")
    
    @ExceptionMiddleware.handle_exceptions("SupplierScreen")
    def on_supplier_delete(self, suppliers_data):
        """Handle supplier deletion"""
        try:
            for supplier_data in suppliers_data:
                self.supplier_service.delete(supplier_data['id'])
            
            self.show_message(f"Successfully deleted {len(suppliers_data)} supplier(s)")
            self.clear_form()
            return True
        except Exception as e:
            self.show_message(f"Error deleting suppliers: {str(e)}", "error")
            return False