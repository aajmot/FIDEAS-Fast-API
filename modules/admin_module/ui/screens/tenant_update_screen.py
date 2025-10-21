import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
from core.shared.components.base_screen import BaseScreen
from modules.admin_module.services.tenant_service import TenantService
from modules.admin_module.services.module_service import ModuleService, TenantModuleService
from core.shared.utils.logger import logger

class TenantUpdateScreen(BaseScreen):
    def __init__(self, parent, admin_module):
        self.admin_module = admin_module
        self.tenant_service = TenantService()
        self.module_service = ModuleService()
        self.tenant_module_service = TenantModuleService()
        self.current_tenant = None
        self.logo_path = None
        self.module_vars = {}
        
        super().__init__(parent)
        self.load_tenant_data()
    
    def setup_ui(self):
        super().setup_ui()
        
        # Main container
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        main_frame = ctk.CTkFrame(self.main_frame)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ctk.CTkFrame(main_frame)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(header_frame, text="Tenant Update", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Back", command=self.go_back, width=80).pack(side="right", padx=10, pady=10)
        
        # Form frame with two columns
        form_frame = ctk.CTkFrame(main_frame)
        form_frame.pack(fill="both", expand=True, padx=10, pady=5)
        form_frame.grid_columnconfigure(0, weight=1)
        form_frame.grid_columnconfigure(1, weight=1)
        
        # Left side - Basic Information
        ctk.CTkLabel(form_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.name_entry = ctk.CTkEntry(form_frame, width=200)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(form_frame, text="Code:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.code_entry = ctk.CTkEntry(form_frame, width=200)
        self.code_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(form_frame, text="Tagline:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.tagline_entry = ctk.CTkEntry(form_frame, width=200)
        self.tagline_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(form_frame, text="Address:").grid(row=3, column=0, padx=5, pady=5, sticky="nw")
        self.address_text = ctk.CTkTextbox(form_frame, width=200, height=60)
        self.address_text.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(form_frame, text="Logo:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        logo_frame = ctk.CTkFrame(form_frame)
        logo_frame.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        self.logo_label = ctk.CTkLabel(logo_frame, text="No logo selected", width=150)
        self.logo_label.pack(side="left", padx=5)
        self.logo_button = ctk.CTkButton(logo_frame, text="Browse", command=self.browse_logo, width=80)
        self.logo_button.pack(side="left", padx=5)
        
        # Right side - Module Access
        ctk.CTkLabel(form_frame, text="Module Access:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, padx=(20, 5), pady=5, sticky="w")
        
        self.modules_frame = ctk.CTkFrame(form_frame)
        self.modules_frame.grid(row=0, column=3, rowspan=5, padx=5, pady=5, sticky="nsew")
        
        self.load_modules()
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(button_frame, text="Update", command=self.update_tenant, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Clear", command=self.clear_form, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
    
    def load_modules(self):
        """Load available modules as checkboxes"""
        from core.database.connection import db_manager
        from modules.admin_module.models.entities import ModuleMaster
        
        with db_manager.get_session() as session:
            modules = session.query(ModuleMaster).filter(ModuleMaster.is_active == True).all()
            
            for i, module in enumerate(modules):
                var = ctk.BooleanVar()
                self.module_vars[module.id] = var
                
                checkbox = ctk.CTkCheckBox(self.modules_frame, text=module.module_name, variable=var)
                if module.is_mandatory:
                    checkbox.configure(state="disabled")
                    var.set(True)
                
                checkbox.pack(anchor="w", padx=10, pady=2)
    
    def load_tenant_data(self):
        """Load current tenant data"""
        # Populate with current data after UI is created
        self.after(100, self._populate_form_data)
    
    def _populate_form_data(self):
        """Populate form data after UI is fully created"""
        # Try to get current user from session manager
        from core.shared.utils.session_manager import session_manager
        current_user = session_manager.get_current_user()
        
        if not current_user:
            print("No current user in session")
            return
        
        print(f"Current user: {current_user}")
            
        # Get fresh tenant data from database
        from core.database.connection import db_manager
        from modules.admin_module.models.entities import Tenant, TenantModuleMapping
        
        try:
            with db_manager.get_session() as session:
                # Get current user's tenant_id
                user_tenant_id = current_user.get('tenant_id')
                print(f"Loading tenant data for tenant_id: {user_tenant_id}")
                
                tenant = session.query(Tenant).filter(
                    Tenant.id == user_tenant_id
                ).first()
                
                if tenant:
                    print(f"Found tenant: {tenant.name}")
                    # Clear and populate basic info
                    self.name_entry.delete(0, 'end')
                    self.code_entry.delete(0, 'end')
                    self.tagline_entry.delete(0, 'end')
                    self.address_text.delete("1.0", 'end')
                    
                    self.name_entry.insert(0, tenant.name or "")
                    self.code_entry.insert(0, tenant.code or "")
                    self.tagline_entry.insert(0, tenant.tagline or "")
                    self.address_text.insert("1.0", tenant.address or "")
                    
                    if tenant.logo:
                        self.logo_path = tenant.logo
                        self.logo_label.configure(text=os.path.basename(tenant.logo))
                    
                    # Load module mappings
                    mappings = session.query(TenantModuleMapping).filter(
                        TenantModuleMapping.tenant_id == tenant.id,
                        TenantModuleMapping.is_active == True
                    ).all()
                    
                    mapped_module_ids = [mapping.module_id for mapping in mappings]
                    
                    for module_id, var in self.module_vars.items():
                        if module_id in mapped_module_ids:
                            var.set(True)
                else:
                    print(f"No tenant found for tenant_id: {user_tenant_id}")
        except Exception as e:
            print(f"Error loading tenant data: {str(e)}")
    
    def browse_logo(self):
        """Browse for logo file"""
        file_path = filedialog.askopenfilename(
            title="Select Logo",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        
        if file_path:
            # Copy to logos directory
            logos_dir = "logos"
            if not os.path.exists(logos_dir):
                os.makedirs(logos_dir)
            
            filename = os.path.basename(file_path)
            destination = os.path.join(logos_dir, filename)
            
            try:
                import shutil
                shutil.copy2(file_path, destination)
                self.logo_path = destination
                self.logo_label.configure(text=filename)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to copy logo: {str(e)}")
    
    def update_tenant(self):
        """Update tenant information"""
        from core.shared.utils.session_manager import session_manager
        current_user = session_manager.get_current_user()
        
        if not current_user:
            messagebox.showerror("Error", "No user session found")
            return
        
        try:
            # Update tenant basic info directly
            from core.database.connection import db_manager
            from modules.admin_module.models.entities import Tenant
            
            with db_manager.get_session() as session:
                tenant = session.query(Tenant).filter(
                    Tenant.id == current_user.get('tenant_id')
                ).first()
                
                if not tenant:
                    messagebox.showerror("Error", "Tenant not found")
                    return
                
                # Update tenant fields
                tenant.name = self.name_entry.get().strip()
                tenant.code = self.code_entry.get().strip()
                tenant.tagline = self.tagline_entry.get().strip()
                tenant.address = self.address_text.get("1.0", "end-1c").strip()
                tenant.logo = self.logo_path
                
                if not tenant.name:
                    messagebox.showerror("Error", "Tenant name is required")
                    return
                
                if not tenant.code:
                    messagebox.showerror("Error", "Tenant code is required")
                    return
                
                session.commit()
            
            # Update module mappings
            from modules.admin_module.models.entities import TenantModuleMapping, ModuleMaster
            
            with db_manager.get_session() as session:
                tenant_id = current_user.get('tenant_id')
                
                # Get current mappings
                current_mappings = session.query(TenantModuleMapping).filter(
                    TenantModuleMapping.tenant_id == tenant_id
                ).all()
                current_module_ids = {mapping.module_id for mapping in current_mappings if mapping.is_active}
                
                for module_id, var in self.module_vars.items():
                    is_selected = var.get()
                    
                    # Check if module is mandatory
                    module = session.query(ModuleMaster).filter(ModuleMaster.id == module_id).first()
                    if module and module.is_mandatory:
                        continue  # Skip mandatory modules
                    
                    existing_mapping = session.query(TenantModuleMapping).filter(
                        TenantModuleMapping.tenant_id == tenant_id,
                        TenantModuleMapping.module_id == module_id
                    ).first()
                    
                    if is_selected and module_id not in current_module_ids:
                        # Add or activate module mapping
                        if existing_mapping:
                            existing_mapping.is_active = True
                        else:
                            new_mapping = TenantModuleMapping(
                                tenant_id=tenant_id,
                                module_id=module_id,
                                created_by=current_user.get('username', 'system') if current_user else 'system'
                            )
                            session.add(new_mapping)
                    elif not is_selected and module_id in current_module_ids:
                        # Deactivate module mapping
                        if existing_mapping:
                            existing_mapping.is_active = False
                
                session.commit()
            
            messagebox.showinfo("Success", "Tenant updated successfully")
            logger.info(f"Tenant {current_user.get('tenant_id')} updated", "TenantUpdateScreen")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update tenant: {str(e)}")
            logger.error(f"Failed to update tenant: {str(e)}", "TenantUpdateScreen")
    
    def go_back(self):
        """Go back to dashboard"""
        self.destroy()
        
        # Find root window and clear it
        root = self
        while root.master:
            root = root.master
        
        for widget in root.winfo_children():
            widget.destroy()
        
        # Create new dashboard
        from modules.dashboard.modern_dashboard import ModernDashboard
        ModernDashboard(root)
    
    def clear_form(self):
        """Clear form fields"""
        self.name_entry.delete(0, 'end')
        self.code_entry.delete(0, 'end')
        self.tagline_entry.delete(0, 'end')
        self.address_text.delete("1.0", 'end')
        self.logo_label.configure(text="No logo selected")
        self.logo_path = None
        
        # Clear module checkboxes (except mandatory ones)
        for module_id, var in self.module_vars.items():
            from core.database.connection import db_manager
            from modules.admin_module.models.entities import ModuleMaster
            
            with db_manager.get_session() as session:
                module = session.query(ModuleMaster).filter(ModuleMaster.id == module_id).first()
                if module and not module.is_mandatory:
                    var.set(False)