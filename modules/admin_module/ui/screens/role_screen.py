import customtkinter as ctk
import tkinter as tk
from core.shared.components.base_screen import BaseScreen
from modules.admin_module.services.role_service import RoleService
from core.shared.middleware.exception_handler import ExceptionMiddleware
from core.shared.components.import_mixin import ImportMixin

class RoleScreen(BaseScreen, ImportMixin):
    def __init__(self, parent, admin_module, **kwargs):
        self.admin_module = admin_module
        self.role_service = RoleService()
        self.selected_role = None
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Title and back button
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(header_frame, text="Role Management", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Back", command=self.back_to_dashboard, width=80).pack(side="right", padx=10, pady=10)
        
        # Form frame
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", padx=10, pady=5)
        
        # Form fields
        ctk.CTkLabel(form_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.name_input = ctk.CTkEntry(form_frame, width=300)
        self.name_input.grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Description:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.description_input = ctk.CTkEntry(form_frame, width=300)
        self.description_input.grid(row=1, column=1, padx=5, pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        self.save_btn = ctk.CTkButton(button_frame, text="Create", command=self.save_role, height=25, font=ctk.CTkFont(size=10))
        self.save_btn.pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Clear", command=self.clear_form, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
        self.add_import_button(button_frame)
        
        # Data Grid
        columns = [
            {'key': 'id', 'title': 'ID', 'width': 40},
            {'key': 'name', 'title': 'Name', 'width': 150},
            {'key': 'description', 'title': 'Description', 'width': 250}
        ]
        
        from core.shared.components.data_grid import DataGrid
        self.data_grid = DataGrid(
            self, 
            columns, 
            on_row_select=self.on_role_select,
            on_delete=self.on_role_delete,
            items_per_page=10,
            use_enhanced=True
        )
        self.data_grid.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.load_roles()
    
    @ExceptionMiddleware.handle_exceptions("RoleScreen")
    def load_roles(self):
        from core.database.connection import db_manager
        from modules.admin_module.models.entities import Role
        from core.shared.utils.session_manager import session_manager
        
        roles_data = []
        
        with db_manager.get_session() as session:
            query = session.query(Role)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(Role.tenant_id == tenant_id)
            roles = query.all()
            
            for role in roles:
                role_data = {
                    'id': role.id,
                    'name': role.name,
                    'description': role.description or ''
                }
                roles_data.append(role_data)
        
        self.data_grid.set_data(roles_data)
    
    def on_role_select(self, role_data):
        self.selected_role = role_data
        self.name_input.delete(0, tk.END)
        self.name_input.insert(0, role_data['name'])
        self.description_input.delete(0, tk.END)
        self.description_input.insert(0, role_data['description'])
        self.save_btn.configure(text="Update")
    
    @ExceptionMiddleware.handle_exceptions("RoleScreen")
    def save_role(self):
        if not self.name_input.get():
            self.show_message("Please enter role name", "error")
            return
        
        try:
            role_data = {
                'name': self.name_input.get(),
                'description': self.description_input.get()
            }
            
            if self.selected_role:
                # Update existing role
                self.role_service.update(self.selected_role['id'], role_data)
                self.show_message("Role updated successfully")
            else:
                # Create new role
                self.role_service.create(role_data)
                self.show_message("Role created successfully")
            
            self.clear_form()
            self.load_roles()
        except Exception as e:
            action = "updating" if self.selected_role else "creating"
            self.show_message(f"Error {action} role: {str(e)}", "error")
    
    def clear_form(self):
        self.selected_role = None
        self.name_input.delete(0, tk.END)
        self.description_input.delete(0, tk.END)
        self.save_btn.configure(text="Create")
    
    def download_template(self):
        template_data = {
            'Name': ['Admin', 'Manager', 'User'],
            'Description': ['System Administrator', 'Department Manager', 'Regular User']
        }
        self.create_template_file(template_data, 'roles')
    
    def import_from_excel(self):
        def process_role_row(row, index):
            name = str(row['Name']).strip()
            description = str(row.get('Description', '')).strip()
            
            if not name:
                return False
            
            role_data = {
                'name': name,
                'description': description
            }
            
            self.role_service.create(role_data)
            return True
        
        self.process_import_file(['Name'], process_role_row, 'roles')
    
    @ExceptionMiddleware.handle_exceptions("RoleScreen")
    def on_role_delete(self, roles_data):
        """Handle role deletion"""
        try:
            for role_data in roles_data:
                self.role_service.delete(role_data['id'])
            
            self.show_message(f"Successfully deleted {len(roles_data)} role(s)")
            self.clear_form()
            return True
        except Exception as e:
            self.show_message(f"Error deleting roles: {str(e)}", "error")
            return False
    
    def load_data(self):
        self.load_roles()