import customtkinter as ctk
import tkinter as tk
from core.shared.components.base_screen import BaseScreen
from modules.admin_module.services.tenant_service import TenantService
from core.shared.middleware.exception_handler import ExceptionMiddleware

class TenantScreen(BaseScreen):
    def __init__(self, parent, admin_module, **kwargs):
        self.admin_module = admin_module
        self.tenant_service = TenantService()
        self.selected_tenant = None
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Title and back button
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(header_frame, text="Tenant Management", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Back", command=self.go_back_to_dashboard, width=80).pack(side="right", padx=10, pady=10)
        
        # Form frame
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", padx=10, pady=5)
        
        # Form fields
        ctk.CTkLabel(form_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.name_input = ctk.CTkEntry(form_frame, width=300)
        self.name_input.grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Code:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.code_input = ctk.CTkEntry(form_frame, width=300)
        self.code_input.grid(row=1, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Description:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.description_input = ctk.CTkEntry(form_frame, width=300)
        self.description_input.grid(row=2, column=1, padx=5, pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(button_frame, text="Create", command=self.create_tenant).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Update", command=self.update_tenant).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Clear", command=self.clear_form).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Refresh", command=self.load_tenants).pack(side="left", padx=5, pady=5)
        
        # Tenants list
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        ctk.CTkLabel(list_frame, text="Tenants:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)
        
        self.tenants_listbox = tk.Listbox(list_frame, height=10)
        self.tenants_listbox.pack(fill="both", expand=True, padx=10, pady=5)
        self.tenants_listbox.bind('<<ListboxSelect>>', self.on_tenant_select)
        
        self.load_tenants()
    
    @ExceptionMiddleware.handle_exceptions("TenantScreen")
    def load_tenants(self):
        from core.database.connection import db_manager
        from modules.admin_module.models.entities import Tenant
        
        self.tenants_listbox.delete(0, tk.END)
        self.tenants = []
        
        with db_manager.get_session() as session:
            tenants = session.query(Tenant).all()
            for tenant in tenants:
                tenant_data = {
                    'id': tenant.id,
                    'name': tenant.name,
                    'code': tenant.code or '',
                    'description': tenant.description or ''
                }
                self.tenants.append(tenant_data)
                display_text = f"{tenant_data['code']} - {tenant_data['name']} - {tenant_data['description'] or 'No description'}"
                self.tenants_listbox.insert(tk.END, display_text)
    
    def on_tenant_select(self, event):
        selection = self.tenants_listbox.curselection()
        if selection:
            tenant_data = self.tenants[selection[0]]
            self.selected_tenant = tenant_data
            self.name_input.delete(0, tk.END)
            self.name_input.insert(0, tenant_data['name'])
            self.code_input.delete(0, tk.END)
            self.code_input.insert(0, tenant_data['code'])
            self.description_input.delete(0, tk.END)
            self.description_input.insert(0, tenant_data['description'])
    
    @ExceptionMiddleware.handle_exceptions("TenantScreen")
    def create_tenant(self):
        if not self.name_input.get():
            self.show_message("Please enter tenant name", "error")
            return
        
        if not self.code_input.get():
            self.show_message("Please enter tenant code", "error")
            return
        
        try:
            tenant_data = {
                'name': self.name_input.get(),
                'code': self.code_input.get(),
                'description': self.description_input.get()
            }
            
            self.tenant_service.create(tenant_data)
            self.show_message("Tenant created successfully")
            self.clear_form()
            self.load_tenants()
        except Exception as e:
            self.show_message(f"Error creating tenant: {str(e)}", "error")
    
    @ExceptionMiddleware.handle_exceptions("TenantScreen")
    def update_tenant(self):
        if not self.selected_tenant:
            self.show_message("Please select a tenant to update", "error")
            return
        
        try:
            tenant_data = {
                'name': self.name_input.get(),
                'code': self.code_input.get(),
                'description': self.description_input.get()
            }
            
            self.tenant_service.update(self.selected_tenant['id'], tenant_data)
            self.show_message("Tenant updated successfully")
            self.clear_form()
            self.load_tenants()
        except Exception as e:
            self.show_message(f"Error updating tenant: {str(e)}", "error")
    
    def clear_form(self):
        self.selected_tenant = None
        self.name_input.delete(0, tk.END)
        self.code_input.delete(0, tk.END)
        self.description_input.delete(0, tk.END)
        self.tenants_listbox.selection_clear(0, tk.END)
    
    def go_back_to_dashboard(self):
        """Go back to dashboard"""
        self.destroy()
        root = self
        while root.master:
            root = root.master
        for widget in root.winfo_children():
            widget.destroy()
        from modules.dashboard.modern_dashboard import ModernDashboard
        ModernDashboard(root)