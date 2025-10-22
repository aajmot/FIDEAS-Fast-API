import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import shutil
from core.shared.components.base_screen import BaseScreen
from modules.admin_module.services.tenant_service import TenantService
from modules.admin_module.services.user_service import UserService
from core.shared.utils.logger import logger
from sqlalchemy import text

class TenantSetupScreen(BaseScreen):
    def __init__(self, parent, on_complete_callback=None):
        self.tenant_service = TenantService()
        self.user_service = UserService()
        self.on_complete_callback = on_complete_callback
        self.logo_path = None
        super().__init__(parent)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Main container
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        ctk.CTkLabel(main_frame, text="Initial Tenant Setup", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=20)
        ctk.CTkLabel(main_frame, text="Please setup your tenant information and admin user", font=ctk.CTkFont(size=14)).pack(pady=10)
        
        # Scrollable frame for form
        scrollable_frame = ctk.CTkScrollableFrame(main_frame)
        scrollable_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # Form frame
        form_frame = ctk.CTkFrame(scrollable_frame)
        form_frame.pack(fill="x", padx=10, pady=10)
        
        # Tenant Information Section
        ctk.CTkLabel(form_frame, text="Tenant Information", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, pady=10, sticky="w")
        
        ctk.CTkLabel(form_frame, text="Tenant Name:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.tenant_name_entry = ctk.CTkEntry(form_frame, width=300)
        self.tenant_name_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(form_frame, text="Tenant Code:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.tenant_code_entry = ctk.CTkEntry(form_frame, width=300)
        self.tenant_code_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(form_frame, text="Tagline:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.tagline_entry = ctk.CTkEntry(form_frame, width=300)
        self.tagline_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(form_frame, text="Address:").grid(row=4, column=0, padx=5, pady=5, sticky="nw")
        self.address_text = ctk.CTkTextbox(form_frame, width=300, height=60)
        self.address_text.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(form_frame, text="Logo:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        logo_frame = ctk.CTkFrame(form_frame)
        logo_frame.grid(row=5, column=1, padx=5, pady=5, sticky="w")
        self.logo_label = ctk.CTkLabel(logo_frame, text="No logo selected", width=200)
        self.logo_label.pack(side="left", padx=5)
        ctk.CTkButton(logo_frame, text="Browse", command=self.browse_logo, width=80).pack(side="left", padx=5)
        
        # Admin User Section
        ctk.CTkLabel(form_frame, text="Admin User", font=ctk.CTkFont(size=16, weight="bold")).grid(row=6, column=0, columnspan=2, pady=(20,10), sticky="w")
        
        ctk.CTkLabel(form_frame, text="Username:").grid(row=7, column=0, padx=5, pady=5, sticky="w")
        self.username_entry = ctk.CTkEntry(form_frame, width=300)
        self.username_entry.grid(row=7, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(form_frame, text="Email:").grid(row=8, column=0, padx=5, pady=5, sticky="w")
        self.email_entry = ctk.CTkEntry(form_frame, width=300)
        self.email_entry.grid(row=8, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(form_frame, text="Password:").grid(row=9, column=0, padx=5, pady=5, sticky="w")
        self.password_entry = ctk.CTkEntry(form_frame, width=300, show="*")
        self.password_entry.grid(row=9, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(form_frame, text="First Name:").grid(row=10, column=0, padx=5, pady=5, sticky="w")
        self.first_name_entry = ctk.CTkEntry(form_frame, width=300)
        self.first_name_entry.grid(row=10, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(form_frame, text="Last Name:").grid(row=11, column=0, padx=5, pady=5, sticky="w")
        self.last_name_entry = ctk.CTkEntry(form_frame, width=300)
        self.last_name_entry.grid(row=11, column=1, padx=5, pady=5, sticky="w")
        
        # Button frame at bottom
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(button_frame, text="Complete Setup", command=self.complete_setup, height=40, font=ctk.CTkFont(size=14)).pack(pady=10)
    
    def browse_logo(self):
        file_path = filedialog.askopenfilename(
            title="Select Logo",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        
        if file_path:
            logos_dir = "logos"
            if not os.path.exists(logos_dir):
                os.makedirs(logos_dir)
            
            filename = os.path.basename(file_path)
            destination = os.path.join(logos_dir, filename)
            
            try:
                shutil.copy2(file_path, destination)
                self.logo_path = destination
                self.logo_label.configure(text=filename)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to copy logo: {str(e)}")
    
    def complete_setup(self):
        # Validate inputs
        if not all([self.tenant_name_entry.get().strip(), self.tenant_code_entry.get().strip(),
                   self.username_entry.get().strip(), self.email_entry.get().strip(),
                   self.password_entry.get().strip()]):
            messagebox.showerror("Error", "Please fill in all required fields")
            return
        
        try:
            # Ensure database is properly initialized
            from core.shared.utils.database_initializer import ensure_database_initialized, initialize_tenant_data
            ensure_database_initialized()
            
            from core.database.connection import db_manager
            from modules.admin_module.models.entities import Tenant, User, Role, UserRole
            
            with db_manager.get_session() as session:
                # Create tenant
                tenant = Tenant(
                    name=self.tenant_name_entry.get().strip(),
                    code=self.tenant_code_entry.get().strip(),
                    tagline=self.tagline_entry.get().strip(),
                    address=self.address_text.get("1.0", "end-1c").strip(),
                    logo=self.logo_path
                )
                session.add(tenant)
                session.flush()  # Get tenant ID
                
                # Create admin role
                admin_role = Role(
                    name="Admin",
                    description="System Administrator",
                    tenant_id=tenant.id,
                    created_by="system"
                )
                session.add(admin_role)
                session.flush()
                
                # Create admin user
                admin_user = User(
                    username=self.username_entry.get().strip(),
                    email=self.email_entry.get().strip(),
                    first_name=self.first_name_entry.get().strip(),
                    last_name=self.last_name_entry.get().strip(),
                    tenant_id=tenant.id,
                    is_tenant_admin=True,
                    created_by="system"
                )
                admin_user.set_password(self.password_entry.get().strip())
                session.add(admin_user)
                session.flush()
                
                # Assign admin role to user
                user_role = UserRole(
                    user_id=admin_user.id,
                    role_id=admin_role.id,
                    tenant_id=tenant.id,
                    created_by="system"
                )
                session.add(user_role)
                
                session.commit()
                
                # Initialize tenant-specific data
                initialize_tenant_data(tenant.id)
                

            
            messagebox.showinfo("Success", "Tenant setup completed successfully!")
            logger.info(f"Initial tenant setup completed: {self.tenant_name_entry.get().strip()}", "TenantSetupScreen")
            
            if self.on_complete_callback:
                self.on_complete_callback()
            
        except Exception as e:
            messagebox.showerror("Error", f"Setup failed: {str(e)}")
            logger.error(f"Tenant setup failed: {str(e)}", "TenantSetupScreen")