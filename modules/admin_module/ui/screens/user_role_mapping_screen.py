import customtkinter as ctk
import tkinter as tk
from core.shared.components.base_screen import BaseScreen
from modules.admin_module.services.user_service import UserService
from core.shared.middleware.exception_handler import ExceptionMiddleware

class UserRoleMappingScreen(BaseScreen):
    def __init__(self, parent, admin_module, **kwargs):
        self.admin_module = admin_module
        self.user_service = UserService()
        self.selected_user = None
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Title and back button
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(header_frame, text="User-Role Mapping", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Back", command=self.back_to_dashboard, width=80).pack(side="right", padx=10, pady=10)
        
        # Main content frame
        content_frame = ctk.CTkFrame(self)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Left side - Users list
        left_frame = ctk.CTkFrame(content_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(left_frame, text="Users", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        
        # Users data grid
        user_columns = [
            {'key': 'id', 'title': 'ID', 'width': 40},
            {'key': 'username', 'title': 'Username', 'width': 120},
            {'key': 'email', 'title': 'Email', 'width': 150},
            {'key': 'role_count', 'title': 'Roles', 'width': 60}
        ]
        
        from core.shared.components.data_grid import DataGrid
        self.users_grid = DataGrid(left_frame, user_columns, on_row_select=self.on_user_select, items_per_page=15)
        self.users_grid.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Right side - Role assignment
        right_frame = ctk.CTkFrame(content_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(right_frame, text="Role Assignment", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        
        # Selected user info
        self.user_info_label = ctk.CTkLabel(right_frame, text="Select a user to manage roles", font=ctk.CTkFont(size=12))
        self.user_info_label.pack(pady=10)
        
        # Available roles
        roles_frame = ctk.CTkFrame(right_frame)
        roles_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(roles_frame, text="Available Roles:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=5)
        
        # Scrollable frame for role checkboxes
        self.roles_scroll_frame = ctk.CTkScrollableFrame(roles_frame, height=200)
        self.roles_scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(right_frame)
        button_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkButton(button_frame, text="Save Changes", command=self.save_role_changes, height=30).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Refresh", command=self.load_users, height=30).pack(side="left", padx=5, pady=5)
        
        self.role_vars = {}
        self.load_users()
        self.load_roles()
    
    @ExceptionMiddleware.handle_exceptions("UserRoleMappingScreen")
    def load_users(self):
        from core.database.connection import db_manager
        from modules.admin_module.models.entities import User, UserRole
        from core.shared.utils.session_manager import session_manager
        
        users_data = []
        
        with db_manager.get_session() as session:
            query = session.query(User)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(User.tenant_id == tenant_id)
            users = query.all()
            
            for user in users:
                # Count roles for this user
                role_count = session.query(UserRole).filter(UserRole.user_id == user.id).count()
                
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role_count': str(role_count)
                }
                users_data.append(user_data)
        
        self.users_grid.set_data(users_data)
    
    def load_roles(self):
        from core.database.connection import db_manager
        from modules.admin_module.models.entities import Role
        from core.shared.utils.session_manager import session_manager
        
        # Clear existing role checkboxes
        for widget in self.roles_scroll_frame.winfo_children():
            widget.destroy()
        
        self.role_vars = {}
        
        with db_manager.get_session() as session:
            query = session.query(Role)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(Role.tenant_id == tenant_id)
            roles = query.all()
            
            for role in roles:
                var = tk.BooleanVar()
                self.role_vars[role.id] = {'var': var, 'name': role.name}
                
                checkbox = ctk.CTkCheckBox(
                    self.roles_scroll_frame,
                    text=role.name,
                    variable=var,
                    font=ctk.CTkFont(size=11)
                )
                checkbox.pack(anchor="w", padx=5, pady=2)
    
    def on_user_select(self, user_data):
        self.selected_user = user_data
        self.user_info_label.configure(text=f"Managing roles for: {user_data['username']} ({user_data['email']})")
        self.load_user_roles(user_data['id'])
    
    def load_user_roles(self, user_id):
        from core.database.connection import db_manager
        from modules.admin_module.models.entities import UserRole
        
        # Clear all checkboxes
        for role_data in self.role_vars.values():
            role_data['var'].set(False)
        
        # Set checkboxes for user's roles
        with db_manager.get_session() as session:
            user_roles = session.query(UserRole).filter(UserRole.user_id == user_id).all()
            for user_role in user_roles:
                if user_role.role_id in self.role_vars:
                    self.role_vars[user_role.role_id]['var'].set(True)
    
    @ExceptionMiddleware.handle_exceptions("UserRoleMappingScreen")
    def save_role_changes(self):
        if not self.selected_user:
            self.show_message("Please select a user first", "error")
            return
        
        try:
            from core.database.connection import db_manager
            from modules.admin_module.models.entities import UserRole
            from core.shared.utils.session_manager import session_manager
            
            user_id = self.selected_user['id']
            selected_roles = {role_id for role_id, role_data in self.role_vars.items() if role_data['var'].get()}
            
            with db_manager.get_session() as session:
                # Remove all existing roles for this user
                session.query(UserRole).filter(UserRole.user_id == user_id).delete()
                
                # Add selected roles
                for role_id in selected_roles:
                    user_role = UserRole(
                        user_id=user_id,
                        role_id=role_id,
                        tenant_id=session_manager.get_current_tenant_id(),
                        assigned_by=session_manager.get_current_user()['id'] if session_manager.get_current_user() else None,
                        created_by=session_manager.get_current_username()
                    )
                    session.add(user_role)
                
                session.commit()
                self.show_message("Role assignments updated successfully")
                self.load_users()  # Refresh user list to show updated role counts
                
        except Exception as e:
            self.show_message(f"Error updating roles: {str(e)}", "error")