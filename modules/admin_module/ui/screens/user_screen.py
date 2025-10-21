import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from core.shared.components.base_screen import BaseScreen
from modules.admin_module.services.user_service import UserService
from modules.admin_module.services.tenant_service import TenantService
from core.shared.middleware.exception_handler import ExceptionMiddleware

class UserScreen(BaseScreen):
    def __init__(self, parent, admin_module, **kwargs):
        self.admin_module = admin_module
        self.user_service = UserService()
        self.tenant_service = TenantService()
        self.selected_user = None
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Title and back button
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(header_frame, text="User Management", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Back", command=self.back_to_dashboard, width=80).pack(side="right", padx=10, pady=10)
        
        # Form frame
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", padx=10, pady=5)
        
        # Form fields
        ctk.CTkLabel(form_frame, text="Username:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.username_input = ctk.CTkEntry(form_frame, width=200)
        self.username_input.grid(row=0, column=1, padx=5, pady=5)
        self.username_input.bind("<FocusOut>", self.check_username_duplicate)
        
        ctk.CTkLabel(form_frame, text="Email:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.email_input = ctk.CTkEntry(form_frame, width=200)
        self.email_input.grid(row=0, column=3, padx=5, pady=5)
        self.email_input.bind("<FocusOut>", self.check_email_duplicate)
        
        ctk.CTkLabel(form_frame, text="First Name:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.first_name_input = ctk.CTkEntry(form_frame, width=200)
        self.first_name_input.grid(row=1, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Last Name:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.last_name_input = ctk.CTkEntry(form_frame, width=200)
        self.last_name_input.grid(row=1, column=3, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Password:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.password_input = ctk.CTkEntry(form_frame, width=200, show="*")
        self.password_input.grid(row=2, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Roles:").grid(row=2, column=2, padx=5, pady=5, sticky="w")
        
        from core.shared.components.multi_select_dropdown import MultiSelectCombobox
        self.roles_dropdown = MultiSelectCombobox(form_frame, width=28, height=28, font=('Arial', 10))
        self.roles_dropdown.grid(row=2, column=3, padx=5, pady=5, sticky="w")
        
        self.load_roles_for_selection()
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        self.save_btn = ctk.CTkButton(button_frame, text="Create", command=self.save_user, height=25, font=ctk.CTkFont(size=10))
        self.save_btn.pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Clear", command=self.clear_form, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Import Excel", command=self.import_from_excel, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Download Template", command=self.download_template, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
        
        # Data Grid
        columns = [
            {'key': 'id', 'title': 'ID', 'width': 40},
            {'key': 'username', 'title': 'Username', 'width': 120},
            {'key': 'email', 'title': 'Email', 'width': 150},
            {'key': 'first_name', 'title': 'First Name', 'width': 100},
            {'key': 'last_name', 'title': 'Last Name', 'width': 100}
        ]
        
        from core.shared.components.data_grid import DataGrid
        self.data_grid = DataGrid(
            self, 
            columns, 
            on_row_select=self.on_user_select,
            on_delete=self.on_user_delete,
            items_per_page=10,
            use_enhanced=True
        )
        self.data_grid.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.load_users()
    
    @ExceptionMiddleware.handle_exceptions("UserScreen")
    def load_users(self):
        from core.database.connection import db_manager
        from modules.admin_module.models.entities import User
        from core.shared.utils.session_manager import session_manager
        
        users_data = []
        
        with db_manager.get_session() as session:
            query = session.query(User)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(User.tenant_id == tenant_id)
            users = query.all()
            
            for user in users:
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name or '',
                    'last_name': user.last_name or '',
                    'tenant_id': user.tenant_id
                }
                users_data.append(user_data)
        
        self.data_grid.set_data(users_data)
    
    def load_roles_for_selection(self):
        from core.database.connection import db_manager
        from modules.admin_module.models.entities import Role
        from core.shared.utils.session_manager import session_manager
        
        roles_dict = {}
        with db_manager.get_session() as session:
            query = session.query(Role)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(Role.tenant_id == tenant_id)
            roles = query.all()
            
            for role in roles:
                roles_dict[role.id] = role.name
        
        self.roles_dropdown.set_options(roles_dict)
        self.roles_dropdown.clear_selection()
    
    def check_username_duplicate(self, event):
        username = self.username_input.get().strip()
        if not username or (self.selected_user and self.selected_user['username'] == username):
            return
        
        from core.database.connection import db_manager
        from modules.admin_module.models.entities import User
        from core.shared.utils.session_manager import session_manager
        
        with db_manager.get_session() as session:
            existing = session.query(User).filter(
                User.username == username,
                User.tenant_id == session_manager.get_current_tenant_id()
            ).first()
            
            if existing:
                self.show_message("Username already exists", "error")
                self.username_input.focus()
    
    def check_email_duplicate(self, event):
        email = self.email_input.get().strip()
        if not email or (self.selected_user and self.selected_user['email'] == email):
            return
        
        from core.database.connection import db_manager
        from modules.admin_module.models.entities import User
        from core.shared.utils.session_manager import session_manager
        
        with db_manager.get_session() as session:
            existing = session.query(User).filter(
                User.email == email,
                User.tenant_id == session_manager.get_current_tenant_id()
            ).first()
            
            if existing:
                self.show_message("Email already exists", "error")
                self.email_input.focus()
    
    def on_user_select(self, user_data):
        self.selected_user = user_data
        self.username_input.delete(0, tk.END)
        self.username_input.insert(0, user_data['username'])
        self.email_input.delete(0, tk.END)
        self.email_input.insert(0, user_data['email'])
        self.first_name_input.delete(0, tk.END)
        self.first_name_input.insert(0, user_data['first_name'])
        self.last_name_input.delete(0, tk.END)
        self.last_name_input.insert(0, user_data['last_name'])
        self.password_input.delete(0, tk.END)
        
        # Load user roles
        self.load_user_roles(user_data['id'])
        self.save_btn.configure(text="Update")
    
    def load_user_roles(self, user_id):
        from core.database.connection import db_manager
        from modules.admin_module.models.entities import UserRole
        
        selected_roles = set()
        with db_manager.get_session() as session:
            user_roles = session.query(UserRole).filter(UserRole.user_id == user_id).all()
            for user_role in user_roles:
                selected_roles.add(user_role.role_id)
        
        self.roles_dropdown.set_selected(selected_roles)
    
    @ExceptionMiddleware.handle_exceptions("UserScreen")
    def save_user(self):
        if not all([self.username_input.get(), self.email_input.get()]):
            self.show_message("Please fill username and email", "error")
            return
        
        if not self.selected_user and not self.password_input.get():
            self.show_message("Password is required for new users", "error")
            return
        
        # Get selected roles
        selected_roles = list(self.roles_dropdown.get_selected())
        
        try:
            from core.database.connection import db_manager
            from modules.admin_module.models.entities import User, UserRole
            from core.shared.utils.session_manager import session_manager
            import bcrypt
            
            with db_manager.get_session() as session:
                # Prepare user data
                user_data = {
                    'username': self.username_input.get(),
                    'email': self.email_input.get(),
                    'first_name': self.first_name_input.get(),
                    'last_name': self.last_name_input.get(),
                    'tenant_id': session_manager.get_current_tenant_id()
                }
                
                if self.password_input.get():
                    password_hash = bcrypt.hashpw(self.password_input.get().encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    user_data['password_hash'] = password_hash
                
                if self.selected_user:
                    # Update existing user
                    user = session.query(User).filter(User.id == self.selected_user['id']).first()
                    for key, value in user_data.items():
                        if hasattr(user, key) and value is not None:
                            setattr(user, key, value)
                    
                    # Update roles - remove existing and add new
                    session.query(UserRole).filter(UserRole.user_id == user.id).delete()
                    
                else:
                    # Create new user
                    user = User(**user_data)
                    session.add(user)
                    session.flush()  # Get user ID
                
                # Add selected roles - ensure user.id exists
                if user.id and selected_roles:
                    for role_id in selected_roles:
                        user_role = UserRole(
                            user_id=user.id,
                            role_id=role_id,
                            tenant_id=session_manager.get_current_tenant_id(),
                            assigned_by=1,  # Default to admin user
                            created_by=session_manager.get_current_username() or 'system'
                        )
                        session.add(user_role)
                
                session.commit()
                action = "updated" if self.selected_user else "created"
                self.show_message(f"User {action} successfully")
            
            self.clear_form()
            self.load_users()
        except Exception as e:
            action = "updating" if self.selected_user else "creating"
            self.show_message(f"Error {action} user: {str(e)}", "error")
    
    def clear_form(self):
        self.selected_user = None
        self.username_input.delete(0, tk.END)
        self.email_input.delete(0, tk.END)
        self.first_name_input.delete(0, tk.END)
        self.last_name_input.delete(0, tk.END)
        self.password_input.delete(0, tk.END)
        
        # Clear selected roles
        self.roles_dropdown.clear_selection()
        
        self.save_btn.configure(text="Create")
    

    
    @ExceptionMiddleware.handle_exceptions("UserScreen")
    def import_from_excel(self):
        """Import users data from Excel file"""
        from tkinter import filedialog, messagebox
        
        try:
            import pandas as pd
            
            # Ask for file to import
            filename = filedialog.askopenfilename(
                filetypes=[("Excel files", "*.xlsx *.xls")],
                title="Select Excel file to import"
            )
            
            if not filename:
                return
            
            # Read Excel file
            df = pd.read_excel(filename)
            
            # Validate required columns
            required_columns = ['Username', 'Email', 'Password']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                messagebox.showerror("Error", f"Missing required columns: {', '.join(missing_columns)}")
                return
            
            # Get available roles for mapping
            from core.database.connection import db_manager
            from modules.admin_module.models.entities import User, Role, UserRole
            from core.shared.utils.session_manager import session_manager
            import bcrypt
            
            roles_dict = {}
            with db_manager.get_session() as session:
                tenant_id = session_manager.get_current_tenant_id()
                roles = session.query(Role).filter(Role.tenant_id == tenant_id).all()
                for role in roles:
                    roles_dict[role.name.lower()] = role.id
            
            # Process each row
            success_count = 0
            error_count = 0
            errors = []
            
            with db_manager.get_session() as session:
                for index, row in df.iterrows():
                    try:
                        username = str(row['Username']).strip()
                        email = str(row['Email']).strip()
                        password = str(row['Password']).strip()
                        
                        if not username or not email or not password:
                            errors.append(f"Row {index + 2}: Username, Email and Password are required")
                            error_count += 1
                            continue
                        
                        # Check if user already exists
                        existing_user = session.query(User).filter(
                            User.username == username,
                            User.tenant_id == tenant_id
                        ).first()
                        
                        if existing_user:
                            errors.append(f"Row {index + 2}: Username '{username}' already exists")
                            error_count += 1
                            continue
                        
                        # Create user
                        user_data = {
                            'username': username,
                            'email': email,
                            'first_name': str(row.get('First Name', '')).strip(),
                            'last_name': str(row.get('Last Name', '')).strip(),
                            'tenant_id': tenant_id,
                            'created_by': session_manager.get_current_username()
                        }
                        
                        # Use provided password
                        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        user_data['password_hash'] = password_hash
                        
                        user = User(**user_data)
                        session.add(user)
                        session.flush()  # Get user ID
                        
                        # Assign roles if specified
                        roles_str = str(row.get('Roles', '')).strip()
                        if roles_str:
                            role_names = [r.strip().lower() for r in roles_str.split(',')]
                            for role_name in role_names:
                                if role_name in roles_dict:
                                    user_role = UserRole(
                                        user_id=user.id,
                                        role_id=roles_dict[role_name],
                                        tenant_id=tenant_id,
                                        created_by=session_manager.get_current_username()
                                    )
                                    session.add(user_role)
                        
                        success_count += 1
                        
                    except Exception as e:
                        errors.append(f"Row {index + 2}: {str(e)}")
                        error_count += 1
                
                if success_count > 0:
                    session.commit()
                    self.load_users()  # Refresh the grid
            
            # Show results
            message = f"Import completed:\n- Successfully imported: {success_count} users\n- Errors: {error_count}"
            if errors:
                message += f"\n\nErrors:\n" + "\n".join(errors[:10])  # Show first 10 errors
                if len(errors) > 10:
                    message += f"\n... and {len(errors) - 10} more errors"
            
            if error_count > 0:
                messagebox.showwarning("Import Results", message)
            else:
                messagebox.showinfo("Success", message)
                
        except ImportError:
            messagebox.showerror("Error", "pandas library is required for Excel import. Install with: pip install pandas openpyxl")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import users: {str(e)}")
    
    @ExceptionMiddleware.handle_exceptions("UserScreen")
    def download_template(self):
        """Download Excel template for users import"""
        from tkinter import filedialog, messagebox
        from datetime import datetime
        
        try:
            import pandas as pd
            
            # Create template data
            template_data = {
                'Username': ['john.doe', 'jane.smith'],
                'Email': ['john.doe@example.com', 'jane.smith@example.com'],
                'Password': ['password123', 'password123'],
                'First Name': ['John', 'Jane'],
                'Last Name': ['Doe', 'Smith'],
                'Roles': ['Admin', 'User']
            }
            
            df = pd.DataFrame(template_data)
            
            # Ask for save location
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile="users_import_template.xlsx"
            )
            
            if filename:
                df.to_excel(filename, index=False, sheet_name='Users Template')
                messagebox.showinfo("Success", f"Template downloaded to {filename}")
                
        except ImportError:
            messagebox.showerror("Error", "pandas library is required. Install with: pip install pandas openpyxl")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to download template: {str(e)}")
    
    @ExceptionMiddleware.handle_exceptions("UserScreen")
    def on_user_delete(self, users_data):
        """Handle user deletion"""
        try:
            for user_data in users_data:
                self.user_service.delete(user_data['id'])
            
            self.show_message(f"Successfully deleted {len(users_data)} user(s)")
            self.clear_form()
            return True
        except Exception as e:
            self.show_message(f"Error deleting users: {str(e)}", "error")
            return False