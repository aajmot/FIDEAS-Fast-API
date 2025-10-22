import customtkinter as ctk
import os
from core.shared.components.base_screen import BaseScreen
from modules.admin_module.services.user_service import UserService
from core.shared.middleware.exception_handler import ExceptionMiddleware

class LoginScreen(BaseScreen):
    def __init__(self, parent, admin_module, **kwargs):
        self.admin_module = admin_module
        self.user_service = UserService()
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Create main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(expand=True, fill="both", padx=50, pady=50)
        
        # Title
        app_name = os.getenv('APP_NAME', 'FIDEAS-Enterprise Management Tool')
        title = ctk.CTkLabel(
            main_frame,
            text=app_name,
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=20)
        
        # Username input
        ctk.CTkLabel(main_frame, text="Username:").pack(pady=(20, 5))
        self.username_input = ctk.CTkEntry(
            main_frame,
            placeholder_text="Enter username",
            width=300,
            height=40
        )
        self.username_input.pack(pady=5)
        
        # Password input
        ctk.CTkLabel(main_frame, text="Password:").pack(pady=(10, 5))
        self.password_input = ctk.CTkEntry(
            main_frame,
            placeholder_text="Enter password",
            show="*",
            width=300,
            height=40
        )
        self.password_input.pack(pady=5)
        
        # Login button
        login_btn = ctk.CTkButton(
            main_frame,
            text="Login",
            command=self.on_login,
            width=300,
            height=40
        )
        login_btn.pack(pady=20)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="",
            text_color="red"
        )
        self.status_label.pack(pady=10)
        
        # Bind Enter key to login
        self.username_input.bind("<Return>", lambda e: self.on_login())
        self.password_input.bind("<Return>", lambda e: self.on_login())
        
        # Add footer
        footer_frame = ctk.CTkFrame(self, height=30, corner_radius=0)
        footer_frame.pack(side="bottom", fill="x")
        footer_frame.pack_propagate(False)
        
        footer_label = ctk.CTkLabel(
            footer_frame,
            text="fideas@2025",
            font=ctk.CTkFont(size=11),
            text_color="gray50"
        )
        footer_label.pack(expand=True)
    
    @ExceptionMiddleware.handle_exceptions("LoginScreen")
    def on_login(self):
        username = self.username_input.get().strip()
        password = self.password_input.get().strip()
        
        if not username or not password:
            self.status_label.configure(text="Please enter both username and password", text_color="red")
            return
        
        user = self.user_service.authenticate(username, password)
        if user:
            from core.shared.utils.session_manager import SessionManager, session_manager
            from modules.dashboard.modern_dashboard import ModernDashboard
            from modules.admin_module.services.tenant_service import TenantService
            
            # Fetch tenant information
            try:
                from core.database.connection import db_manager
                from modules.admin_module.models.entities import Tenant
                with db_manager.get_session() as session:
                    tenant = session.query(Tenant).filter(Tenant.id == user['tenant_id']).first()
                    tenant_name = tenant.name if tenant else "Unknown Tenant"
            except Exception:
                tenant_name = "Unknown Tenant"
            
            # Set session data using both methods for compatibility
            SessionManager.set_session_data({
                'user_id': user['id'],
                'username': user['username'],
                'tenant_id': user['tenant_id'],
                'tenant_name': tenant_name,
                'is_active': True
            })
            
            # Also set in the global session manager
            session_manager.set_current_user(user)
            
            self.admin_module.current_user = user
            self.status_label.configure(text=f"Welcome, {user['username']}!", text_color="green")
            
            # Clear current screen and show modern dashboard
            self.destroy()
            ModernDashboard(self.master)
        else:
            self.status_label.configure(text="Invalid username or password", text_color="red")