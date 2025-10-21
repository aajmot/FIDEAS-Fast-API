import customtkinter as ctk
import tkinter as tk
from core.shared.components.base_screen import BaseScreen
from modules.admin_module.services.legal_entity_service import LegalEntityService
from modules.admin_module.services.tenant_service import TenantService
from core.shared.middleware.exception_handler import ExceptionMiddleware
from core.shared.utils.dropdown_migration import create_searchable_dropdown
from tkinter import filedialog
from PIL import Image
import os
import shutil

class LegalEntityScreen(BaseScreen):
    def __init__(self, parent, admin_module, **kwargs):
        self.admin_module = admin_module
        self.legal_entity_service = LegalEntityService()
        self.tenant_service = TenantService()
        self.selected_entity = None
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Title and back button
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(header_frame, text="Legal Entity Management", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Back", command=self.back_to_dashboard, width=80).pack(side="right", padx=10, pady=10)
        
        # Form frame
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", padx=10, pady=5)
        
        # Form fields
        ctk.CTkLabel(form_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.name_input = ctk.CTkEntry(form_frame, width=200)
        self.name_input.grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Code:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.code_input = ctk.CTkEntry(form_frame, width=200)
        self.code_input.grid(row=0, column=3, padx=5, pady=5)
        self.code_input.bind("<FocusOut>", self.check_code_duplicate)
        
        ctk.CTkLabel(form_frame, text="Registration Number:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.registration_input = ctk.CTkEntry(form_frame, width=200)
        self.registration_input.grid(row=1, column=1, padx=5, pady=5)
        self.registration_input.bind("<FocusOut>", self.check_registration_duplicate)
        
        ctk.CTkLabel(form_frame, text="Logo:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        logo_frame = ctk.CTkFrame(form_frame)
        logo_frame.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        
        self.logo_input = ctk.CTkEntry(logo_frame, width=150, placeholder_text="No file selected")
        self.logo_input.pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(logo_frame, text="Browse", command=self.browse_logo, width=60, height=25).pack(side="left")
        
        ctk.CTkLabel(form_frame, text="Admin User:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.admin_dropdown = create_searchable_dropdown(
            form_frame, 
            values=[], 
            width=200, 
            placeholder_text="Select Admin User..."
        )
        self.admin_dropdown.grid(row=2, column=1, padx=5, pady=5)
        self.load_users_for_admin()
        
        ctk.CTkLabel(form_frame, text="Active:").grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.active_var = ctk.BooleanVar(value=True)
        self.active_checkbox = ctk.CTkCheckBox(form_frame, text="Yes", variable=self.active_var)
        self.active_checkbox.grid(row=2, column=3, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(form_frame, text="Address:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.address_input = ctk.CTkTextbox(form_frame, width=420, height=60)
        self.address_input.grid(row=3, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        self.save_btn = ctk.CTkButton(button_frame, text="Create", command=self.save_entity, height=25, font=ctk.CTkFont(size=10))
        self.save_btn.pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Clear", command=self.clear_form, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
        
        # Data Grid
        columns = [
            {'key': 'id', 'title': 'ID', 'width': 40},
            {'key': 'name', 'title': 'Name', 'width': 150},
            {'key': 'code', 'title': 'Code', 'width': 80},
            {'key': 'registration_number', 'title': 'Registration', 'width': 120},
            {'key': 'admin_user', 'title': 'Admin', 'width': 100},
            {'key': 'is_active', 'title': 'Active', 'width': 60}
        ]
        
        from core.shared.components.data_grid import DataGrid
        self.data_grid = DataGrid(
            self, 
            columns, 
            on_row_select=self.on_entity_select,
            on_delete=self.on_entity_delete,
            items_per_page=10,
            use_enhanced=True
        )
        self.data_grid.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.load_entities()
    
    def load_users_for_admin(self):
        from core.database.connection import db_manager
        from modules.admin_module.models.entities import User
        from core.shared.utils.session_manager import session_manager
        
        user_options = ["None"]
        self.user_mapping = {"None": None}
        
        with db_manager.get_session() as session:
            query = session.query(User)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(User.tenant_id == tenant_id)
            users = query.all()
            
            for user in users:
                display_name = f"{user.username} ({user.first_name} {user.last_name})".strip()
                user_options.append(display_name)
                self.user_mapping[display_name] = user.id
        
        self.admin_dropdown.configure_values(user_options)
        self.admin_dropdown.set("None")
    
    def check_code_duplicate(self, event):
        code = self.code_input.get().strip()
        if not code or (self.selected_entity and self.selected_entity.get('code') == code):
            return
        
        from core.database.connection import db_manager
        from modules.admin_module.models.entities import LegalEntity
        from core.shared.utils.session_manager import session_manager
        
        with db_manager.get_session() as session:
            existing = session.query(LegalEntity).filter(
                LegalEntity.code == code,
                LegalEntity.tenant_id == session_manager.get_current_tenant_id()
            ).first()
            
            if existing:
                self.show_message("Code already exists for this tenant", "error")
                self.code_input.focus()
    
    def check_registration_duplicate(self, event):
        registration = self.registration_input.get().strip()
        if not registration or (self.selected_entity and self.selected_entity.get('registration_number') == registration):
            return
        
        from core.database.connection import db_manager
        from modules.admin_module.models.entities import LegalEntity
        
        with db_manager.get_session() as session:
            existing = session.query(LegalEntity).filter(
                LegalEntity.registration_number == registration
            ).first()
            
            if existing:
                self.show_message("Registration number already exists", "error")
                self.registration_input.focus()
    
    def browse_logo(self):
        file_types = [
            ('Image files', '*.png *.jpg *.jpeg *.gif *.bmp'),
            ('PNG files', '*.png'),
            ('JPEG files', '*.jpg *.jpeg'),
            ('All files', '*.*')
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Logo Image",
            filetypes=file_types
        )
        
        if filename:
            if self.validate_logo_image(filename):
                # Create logos directory if it doesn't exist
                logos_dir = os.path.join(os.getcwd(), "logos")
                os.makedirs(logos_dir, exist_ok=True)
                
                # Copy file to logos directory with unique name
                file_ext = os.path.splitext(filename)[1]
                new_filename = f"logo_{len(os.listdir(logos_dir)) + 1}{file_ext}"
                new_path = os.path.join(logos_dir, new_filename)
                
                try:
                    shutil.copy2(filename, new_path)
                    self.logo_input.delete(0, tk.END)
                    self.logo_input.insert(0, new_path)
                    self.show_message("Logo uploaded successfully")
                except Exception as e:
                    self.show_message(f"Error uploading logo: {str(e)}", "error")
    
    def validate_logo_image(self, filepath):
        try:
            with Image.open(filepath) as img:
                width, height = img.size
                file_size = os.path.getsize(filepath)
                
                # Enterprise standard: 200x200px, max 2MB
                if width > 500 or height > 500:
                    self.show_message("Logo dimensions should not exceed 500x500 pixels", "error")
                    return False
                
                if file_size > 2 * 1024 * 1024:  # 2MB
                    self.show_message("Logo file size should not exceed 2MB", "error")
                    return False
                
                # Recommend square aspect ratio
                if abs(width - height) > min(width, height) * 0.2:
                    self.show_message("Warning: Logo should ideally be square (1:1 aspect ratio)", "warning")
                
                return True
        except Exception as e:
            self.show_message(f"Invalid image file: {str(e)}", "error")
            return False
    
    @ExceptionMiddleware.handle_exceptions("LegalEntityScreen")
    def load_entities(self):
        from core.database.connection import db_manager
        from modules.admin_module.models.entities import LegalEntity
        from core.shared.utils.session_manager import session_manager
        
        entities_data = []
        
        with db_manager.get_session() as session:
            query = session.query(LegalEntity)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(LegalEntity.tenant_id == tenant_id)
            entities = query.all()
            
            for entity in entities:
                admin_name = ""
                if entity.admin_user_id:
                    admin_user = session.query(User).filter(User.id == entity.admin_user_id).first()
                    if admin_user:
                        admin_name = admin_user.username
                
                entity_data = {
                    'id': entity.id,
                    'name': entity.name,
                    'code': entity.code,
                    'registration_number': entity.registration_number or '',
                    'address': entity.address or '',
                    'logo': entity.logo or '',
                    'admin_user_id': entity.admin_user_id,
                    'admin_user': admin_name,
                    'is_active': 'Yes' if entity.is_active else 'No'
                }
                entities_data.append(entity_data)
        
        self.data_grid.set_data(entities_data)
    
    def on_entity_select(self, entity_data):
        self.selected_entity = entity_data
        self.name_input.delete(0, tk.END)
        self.name_input.insert(0, entity_data['name'])
        self.code_input.delete(0, tk.END)
        self.code_input.insert(0, entity_data['code'])
        self.registration_input.delete(0, tk.END)
        self.registration_input.insert(0, entity_data['registration_number'])
        self.logo_input.delete(0, tk.END)
        self.logo_input.insert(0, entity_data['logo'])
        self.address_input.delete("1.0", tk.END)
        self.address_input.insert("1.0", entity_data['address'])
        
        # Set admin user
        if entity_data['admin_user_id']:
            for display_name, user_id in self.user_mapping.items():
                if user_id == entity_data['admin_user_id']:
                    self.admin_dropdown.set(display_name)
                    break
        else:
            self.admin_dropdown.set("None")
        
        # Set active status
        self.active_var.set(entity_data['is_active'] == 'Yes')
        self.save_btn.configure(text="Update")
    
    @ExceptionMiddleware.handle_exceptions("LegalEntityScreen")
    def save_entity(self):
        if not self.name_input.get().strip():
            self.show_message("Please enter entity name", "error")
            return
        
        if not self.code_input.get().strip():
            self.show_message("Please enter entity code", "error")
            return
        
        # Get admin user ID
        selected_admin = self.admin_dropdown.get()
        admin_user_id = self.user_mapping.get(selected_admin)
        
        entity_data = {
            'name': self.name_input.get().strip(),
            'code': self.code_input.get().strip(),
            'registration_number': self.registration_input.get().strip() or None,
            'logo': self.logo_input.get().strip() or None,
            'admin_user_id': admin_user_id,
            'address': self.address_input.get("1.0", tk.END).strip() or None,
            'is_active': self.active_var.get()
        }
        
        try:
            if self.selected_entity:
                self.legal_entity_service.update(self.selected_entity['id'], entity_data)
                self.show_message("Legal entity updated successfully")
            else:
                self.legal_entity_service.create(entity_data)
                self.show_message("Legal entity created successfully")
            
            self.clear_form()
            self.load_entities()
        except Exception as e:
            action = "updating" if self.selected_entity else "creating"
            self.show_message(f"Error {action} legal entity: {str(e)}", "error")
    
    def clear_form(self):
        self.selected_entity = None
        self.name_input.delete(0, tk.END)
        self.code_input.delete(0, tk.END)
        self.registration_input.delete(0, tk.END)
        self.logo_input.delete(0, tk.END)
        self.logo_input.configure(placeholder_text="No file selected")
        self.admin_dropdown.set("None")
        self.active_var.set(True)
        self.address_input.delete("1.0", tk.END)
        self.save_btn.configure(text="Create")
    @ExceptionMiddleware.handle_exceptions("EntityScreen")
    def on_entity_delete(self, entitys_data):
        """Handle entity deletion"""
        try:
            for entity_data in entitys_data:
                self.entity_service.delete(entity_data['id'])
            
            self.show_message(f"Successfully deleted {len(entitys_data)} entity(s)")
            self.clear_form()
            return True
        except Exception as e:
            self.show_message(f"Error deleting entitys: {str(e)}", "error")
            return False