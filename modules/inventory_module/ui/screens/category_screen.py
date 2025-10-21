import customtkinter as ctk
import tkinter as tk
from core.shared.components.base_screen import BaseScreen
from modules.inventory_module.services.category_service import CategoryService
from core.shared.middleware.exception_handler import ExceptionMiddleware
from core.shared.components.import_mixin import ImportMixin
from core.shared.utils.dropdown_migration import create_searchable_dropdown, extract_id_from_value

class CategoryScreen(BaseScreen, ImportMixin):
    def __init__(self, parent, inventory_module, **kwargs):
        self.inventory_module = inventory_module
        self.category_service = CategoryService()
        self.selected_category = None
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Title and back button
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        ctk.CTkLabel(header_frame, text="Category Management", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Back", command=self.back_to_dashboard, width=80).pack(side="right", padx=10, pady=10)
        
        # Form frame
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", padx=10, pady=5)
        
        # Form fields - horizontal layout like admin module
        ctk.CTkLabel(form_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.name_input = ctk.CTkEntry(form_frame, width=200)
        self.name_input.grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Parent Category:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.parent_combo = create_searchable_dropdown(
            form_frame, 
            values=[], 
            width=200, 
            placeholder_text="Select Parent Category..."
        )
        self.parent_combo.grid(row=0, column=3, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Description:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.description_input = ctk.CTkEntry(form_frame, width=420)
        self.description_input.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        self.save_btn = ctk.CTkButton(button_frame, text="Create", command=self.save_category, height=25, font=ctk.CTkFont(size=10))
        self.save_btn.pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Clear", command=self.clear_form, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
        self.add_import_button(button_frame)
        

        
        # Data Grid
        columns = [
            {'key': 'id', 'title': 'ID', 'width': 40},
            {'key': 'name', 'title': 'Name', 'width': 150},
            {'key': 'parent_name', 'title': 'Parent', 'width': 120},
            {'key': 'description', 'title': 'Description', 'width': 200}
        ]
        
        from core.shared.components.data_grid import DataGrid
        self.data_grid = DataGrid(
            self, 
            columns, 
            on_row_select=self.on_category_select,
            on_delete=self.on_category_delete,
            items_per_page=10,
            use_enhanced=True
        )
        self.data_grid.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.load_parent_categories()
        self.load_categories()
    
    @ExceptionMiddleware.handle_exceptions("CategoryScreen")
    def load_categories(self):
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import Category
        from core.shared.utils.session_manager import session_manager
        
        categories_data = []
        
        with db_manager.get_session() as session:
            query = session.query(Category)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(Category.tenant_id == tenant_id)
            categories = query.all()
            
            for category in categories:
                parent_name = ''
                if category.parent_id:
                    parent = session.query(Category).filter(Category.id == category.parent_id).first()
                    if parent:
                        parent_name = parent.name
                
                category_data = {
                    'id': category.id,
                    'name': category.name,
                    'parent_id': category.parent_id,
                    'parent_name': parent_name,
                    'description': category.description or ''
                }
                categories_data.append(category_data)
        
        self.data_grid.set_data(categories_data)
    
    def load_parent_categories(self):
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import Category
        from core.shared.utils.session_manager import session_manager
        
        with db_manager.get_session() as session:
            query = session.query(Category)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(Category.tenant_id == tenant_id)
            categories = query.all()
            category_values = [f"{cat.id}:{cat.name}" for cat in categories]
            self.parent_combo.configure_values(category_values)
    
    def on_category_select(self, category_data):
        self.selected_category = category_data
        self.name_input.delete(0, tk.END)
        self.name_input.insert(0, category_data['name'])
        self.description_input.delete(0, tk.END)
        self.description_input.insert(0, category_data['description'])
        
        # Set parent category
        if category_data['parent_id']:
            self.parent_combo.set(f"{category_data['parent_id']}:{category_data['parent_name']}")
        else:
            self.parent_combo.clear()
        
        self.save_btn.configure(text="Update")
    
    @ExceptionMiddleware.handle_exceptions("CategoryScreen")
    def save_category(self):
        if not self.name_input.get():
            self.show_message("Please enter category name", "error")
            return
        
        try:
            # Get parent category ID
            parent_id = extract_id_from_value(self.parent_combo.get())
            
            category_data = {
                'name': self.name_input.get(),
                'parent_id': parent_id,
                'description': self.description_input.get()
            }
            
            if self.selected_category:
                # Update existing category
                self.category_service.update(self.selected_category['id'], category_data)
                self.show_message("Category updated successfully")
            else:
                # Create new category
                self.category_service.create(category_data)
                self.show_message("Category created successfully")
            
            self.clear_form()
            self.load_categories()
        except Exception as e:
            action = "updating" if self.selected_category else "creating"
            self.show_message(f"Error {action} category: {str(e)}", "error")
    
    def clear_form(self):
        self.selected_category = None
        self.name_input.delete(0, tk.END)
        self.parent_combo.clear()
        self.description_input.delete(0, tk.END)
        self.save_btn.configure(text="Create")
        self.load_parent_categories()
    
    def back_to_dashboard(self):
        # Clear current screen and show dashboard welcome
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        # Show welcome message
        welcome_label = ctk.CTkLabel(
            self.parent,
            text="Welcome to FIDEAS Dashboard",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        welcome_label.pack(pady=(20, 10))
        
        info_label = ctk.CTkLabel(
            self.parent,
            text="Reports and analytics will be displayed here",
            font=ctk.CTkFont(size=14)
        )
        info_label.pack(pady=5)
    
    def download_template(self):
        template_data = {
            'Name': ['Electronics', 'Medicines', 'Accessories'],
            'Description': ['Electronic items', 'Medical supplies', 'General accessories']
        }
        self.create_template_file(template_data, 'categories')
    
    def import_from_excel(self):
        def process_category_row(row, index):
            name = str(row['Name']).strip()
            description = str(row.get('Description', '')).strip()
            
            if not name:
                return False
            
            category_data = {
                'name': name,
                'description': description
            }
            
            self.category_service.create(category_data)
            return True
        
        self.process_import_file(['Name'], process_category_row, 'categories')
    
    @ExceptionMiddleware.handle_exceptions("CategoryScreen")
    def on_category_delete(self, categories_data):
        """Handle category deletion"""
        try:
            for category_data in categories_data:
                self.category_service.delete(category_data['id'])
            
            self.show_message(f"Successfully deleted {len(categories_data)} category(s)")
            self.clear_form()
            return True
        except Exception as e:
            self.show_message(f"Error deleting categories: {str(e)}", "error")
            return False
    
    def load_data(self):
        self.load_categories()
        self.load_parent_categories()