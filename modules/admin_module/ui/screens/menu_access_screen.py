import customtkinter as ctk
from typing import Dict, List, Optional
from core.shared.components.base_screen import BaseScreen
from modules.admin_module.services.menu_service import MenuService
from modules.admin_module.models.entities import Role
from core.database.connection import db_manager
from core.shared.utils.session_manager import SessionManager
from core.shared.utils.dropdown_migration import create_searchable_dropdown

class MenuAccessScreen(BaseScreen):
    def __init__(self, parent):
        self.selected_role_id = None
        self.menu_permissions = {}
        super().__init__(parent)
        self.load_roles()
        self.load_menus()
    
    def setup_ui(self):
        super().setup_ui()
        
        # Title and back button
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(header_frame, text="Menu Access Control", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Back", command=self.back_to_dashboard, width=80).pack(side="right", padx=10, pady=10)
        
        # Form frame
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", padx=10, pady=5)
        
        # Role selection
        ctk.CTkLabel(form_frame, text="Select Role:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.role_dropdown = create_searchable_dropdown(
            form_frame, 
            values=[], 
            width=250, 
            placeholder_text="Select a role...",
            command=self.on_role_selected
        )
        self.role_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Instructions
        ctk.CTkLabel(form_frame, text="Select a role to configure menu permissions", font=ctk.CTkFont(size=12)).grid(row=0, column=2, padx=20, pady=5, sticky="w")
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(button_frame, text="Save Permissions", command=self.save_permissions, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Clear", command=self.clear_form, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
        
        # Menu permissions frame
        self.permissions_frame = ctk.CTkScrollableFrame(self, height=300)
        self.permissions_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    def load_roles(self):
        """Load all roles except admin roles"""
        try:
            session_data = SessionManager.get_session_data()
            tenant_id = session_data.get('tenant_id')
            
            if not tenant_id:
                self.show_error("No tenant ID found in session")
                return
            
            with db_manager.get_session() as session:
                roles = session.query(Role).filter(
                    Role.tenant_id == tenant_id,
                    Role.is_active == True
                ).all()
                
                if not roles:
                    self.show_error("No non-admin roles found")
                    return
                
                role_names = [role.name for role in roles]
                self.role_dropdown.configure_values(role_names)
                self.role_dropdown.set("Select a role...")
                
                self.roles_data = {role.name: role.id for role in roles}
                print(f"DEBUG: Loaded {len(roles)} roles: {role_names}")
        
        except Exception as e:
            print(f"ERROR: Error loading roles: {str(e)}")
            self.show_error(f"Error loading roles: {str(e)}")
    
    def load_menus(self):
        """Load all menus"""
        try:
            self.menus = MenuService.get_all_menus()
            print(f"DEBUG: Loaded {len(self.menus)} menus")
            if not self.menus:
                # Force menu creation if none exist
                with db_manager.get_session() as session:
                    MenuService._insert_default_menus(session)
                self.menus = MenuService.get_all_menus()
                print(f"DEBUG: After insertion, loaded {len(self.menus)} menus")
        except Exception as e:
            print(f"ERROR: Error loading menus: {str(e)}")
            self.show_error(f"Error loading menus: {str(e)}")
    
    def on_role_selected(self, selected_role):
        """Handle role selection"""
        print(f"DEBUG: Role selected: {selected_role}")
        if selected_role and selected_role in self.roles_data:
            self.selected_role_id = self.roles_data[selected_role]
            print(f"DEBUG: Selected role ID: {self.selected_role_id}")
            self.load_role_permissions()
            self.display_menu_permissions()
        else:
            print(f"DEBUG: Role not found in data: {selected_role}")
    
    def load_role_permissions(self):
        """Load existing permissions for selected role"""
        if not self.selected_role_id:
            return
        
        try:
            session_data = SessionManager.get_session_data()
            tenant_id = session_data.get('tenant_id')
            
            self.menu_permissions = MenuService.get_role_menu_permissions(
                self.selected_role_id, tenant_id
            )
            print(f"DEBUG: Loaded {len(self.menu_permissions)} existing permissions for role {self.selected_role_id}")
            
            # Debug: Print existing permissions
            for menu_id, perms in self.menu_permissions.items():
                print(f"DEBUG: Menu {menu_id} permissions: {perms}")
                
        except Exception as e:
            print(f"ERROR: Error loading permissions: {str(e)}")
            self.show_error(f"Error loading permissions: {str(e)}")
    
    def display_menu_permissions(self):
        """Display menu permissions in UI"""
        # Clear existing widgets
        for widget in self.permissions_frame.winfo_children():
            widget.destroy()
        
        if not hasattr(self, 'menus') or not self.menus:
            no_menus_label = ctk.CTkLabel(self.permissions_frame, text="No menus available", text_color="orange")
            no_menus_label.pack(pady=20)
            return
        
        self.permission_vars = {}
        
        # Header
        header_frame = ctk.CTkFrame(self.permissions_frame)
        header_frame.pack(fill="x", padx=5, pady=5)
        
        # Configure grid columns with proper sizing
        header_frame.grid_columnconfigure(0, weight=3, minsize=200)
        for i in range(1, 7):
            header_frame.grid_columnconfigure(i, weight=0, minsize=50)
        
        ctk.CTkLabel(header_frame, text="Menu", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=10, pady=8, sticky="w")
        ctk.CTkLabel(header_frame, text="Create", font=("Arial", 10, "bold")).grid(row=0, column=1, padx=5, pady=8)
        ctk.CTkLabel(header_frame, text="Update", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=5, pady=8)
        ctk.CTkLabel(header_frame, text="Delete", font=("Arial", 10, "bold")).grid(row=0, column=3, padx=5, pady=8)
        ctk.CTkLabel(header_frame, text="Import", font=("Arial", 10, "bold")).grid(row=0, column=4, padx=5, pady=8)
        ctk.CTkLabel(header_frame, text="Export", font=("Arial", 10, "bold")).grid(row=0, column=5, padx=5, pady=8)
        ctk.CTkLabel(header_frame, text="Print", font=("Arial", 10, "bold")).grid(row=0, column=6, padx=5, pady=8)
        
        # Display menus recursively
        print(f"DEBUG: Displaying {len(self.menus)} menus")
        self.display_menu_tree(self.menus, 0)
    
    def display_menu_tree(self, menus: List[Dict], level: int):
        """Recursively display menu tree with permissions"""
        for menu in menus:
            # Show all menus for admin assignment
            print(f"DEBUG: Processing menu: {menu['name']} (admin_only: {menu.get('is_admin_only', False)})")
            
            menu_frame = ctk.CTkFrame(self.permissions_frame)
            menu_frame.pack(fill="x", padx=5 + (level * 15), pady=2)
            
            # Configure grid columns with consistent sizing
            menu_frame.grid_columnconfigure(0, weight=3, minsize=200)
            for i in range(1, 7):
                menu_frame.grid_columnconfigure(i, weight=0, minsize=50)
            
            # Menu name with indentation
            indent = "  " * level
            menu_name = f"{indent}{menu.get('icon', '📄')} {menu['name']}"
            ctk.CTkLabel(menu_frame, text=menu_name, anchor="w", font=("Arial", 11)).grid(row=0, column=0, padx=10, pady=6, sticky="w")
            
            # Permission checkboxes
            menu_id = menu['id']
            existing_perms = self.menu_permissions.get(menu_id, {})
            
            self.permission_vars[menu_id] = {}
            
            permissions = ['can_create', 'can_update', 'can_delete', 'can_import', 'can_export', 'can_print']
            for i, perm in enumerate(permissions):
                perm_value = existing_perms.get(perm, False)
                var = ctk.BooleanVar(value=perm_value)
                checkbox = ctk.CTkCheckBox(menu_frame, text="", variable=var, width=20, height=20,
                                         command=lambda m=menu, p=perm: self.on_permission_change(m, p))
                checkbox.grid(row=0, column=i+1, padx=5, pady=6, sticky="")
                self.permission_vars[menu_id][perm] = var
            
            # Display children
            if menu.get('children'):
                self.display_menu_tree(menu['children'], level + 1)
    
    def save_permissions(self):
        """Save menu permissions for selected role"""
        if not self.selected_role_id:
            self.show_error("Please select a role first")
            return
        
        try:
            session_data = SessionManager.get_session_data()
            tenant_id = session_data.get('tenant_id')
            username = session_data.get('username', 'system')
            
            saved_count = 0
            for menu_id, perms in self.permission_vars.items():
                permissions = {
                    perm_name: var.get() for perm_name, var in perms.items()
                }
                
                # Save all permissions (including false ones to clear existing)
                success = MenuService.assign_menu_permissions(
                    self.selected_role_id,
                    menu_id,
                    permissions,
                    tenant_id,
                    username
                )
                if success:
                    saved_count += 1
            
            print(f"DEBUG: Saved permissions for {saved_count} menus")
            
            self.show_success("Permissions saved successfully")
            
        except Exception as e:
            self.show_error(f"Error saving permissions: {str(e)}")
    
    def clear_form(self):
        """Clear the form"""
        self.selected_role_id = None
        self.role_dropdown.set("Select a role...")
        # Clear existing widgets
        for widget in self.permissions_frame.winfo_children():
            widget.destroy()
    
    def show_success(self, message: str):
        """Show success message"""
        self.show_message(message, "info")
        print(f"SUCCESS: {message}")
    
    def on_permission_change(self, menu: Dict, permission: str):
        """Handle permission change - cascade to children if parent selected"""
        if menu.get('children'):
            parent_var = self.permission_vars[menu['id']][permission]
            parent_value = parent_var.get()
            self.cascade_permission(menu['children'], permission, parent_value)
    
    def cascade_permission(self, children: List[Dict], permission: str, value: bool):
        """Recursively set permission for all children"""
        for child in children:
            if child['id'] in self.permission_vars:
                self.permission_vars[child['id']][permission].set(value)
            if child.get('children'):
                self.cascade_permission(child['children'], permission, value)
    
    def show_error(self, message: str):
        """Show error message"""
        self.show_message(message, "error")
        print(f"ERROR: {message}")