import customtkinter as ctk
import tkinter as tk
from typing import List, Dict, Any
from core.shared.utils.logger import logger
from core.shared.utils.session_manager import session_manager
from modules.admin_module.services.menu_service import MenuService

class ModernDashboard:
    def __init__(self, root):
        self.root = root
        self.current_screen = None
        self.user_menus = []
        self.expanded_menus = {}  # Track expanded state of menus
        # Theme colors
        self.theme_primary = "#2563eb"
        self.theme_secondary = "#3b82f6"
        self.theme_accent = "#1d4ed8"
        self.setup_dashboard()
        self.load_user_menus()
        logger.info("Modern Dashboard initialized", "ModernDashboard")
    
    def setup_dashboard(self):
        # Configure root
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Main container
        self.main_container = ctk.CTkFrame(self.root)
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        # Create top menu, content area, and footer
        self.create_top_menu()
        self.create_content_area()
        self.create_footer()
        
        # Floating dropdown (initially hidden)
        self.floating_dropdown = None
    
    def create_top_menu(self):
        # Top menu bar
        self.menu_bar = ctk.CTkFrame(self.main_container, height=50, corner_radius=8)
        self.menu_bar.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))
        self.menu_bar.grid_propagate(False)
        self.menu_bar.grid_columnconfigure(1, weight=1)
        
        # Logo/Title with tenant name
        tenant_name = session_manager.get_current_tenant_name() or "FIDEAS"
        logo_label = ctk.CTkLabel(
            self.menu_bar,
            text=f"🏢 {tenant_name}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#1f538d", "#14375e")
        )
        logo_label.grid(row=0, column=0, padx=15, pady=12, sticky="w")
        
        # Menu container
        self.menu_container = ctk.CTkFrame(self.menu_bar, fg_color="transparent")
        self.menu_container.grid(row=0, column=1, sticky="ew", padx=10)
        
        # User info
        username = session_manager.get_current_username() or "Guest"
        self.user_btn = ctk.CTkButton(
            self.menu_bar,
            text=f"👤 {username}",
            width=100,
            height=30,
            fg_color=self.theme_accent,
            hover_color=self.theme_secondary,
            command=self.show_user_menu,
            font=ctk.CTkFont(size=11)
        )
        self.user_btn.grid(row=0, column=2, padx=15, pady=10, sticky="e")
        
        self.current_dropdown = None
    
    def create_content_area(self):
        # Content area
        self.content_area = ctk.CTkFrame(self.main_container, corner_radius=8)
        self.content_area.grid(row=1, column=0, sticky="nsew", padx=5, pady=(5, 5))
        
        # Default welcome content
        self.show_welcome_screen()
    
    def create_footer(self):
        # Footer using grid layout
        footer_frame = ctk.CTkFrame(self.main_container, height=30, corner_radius=0)
        footer_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=(0, 5))
        footer_frame.grid_propagate(False)
        
        footer_label = ctk.CTkLabel(
            footer_frame,
            text="fideas@2025",
            font=ctk.CTkFont(size=11),
            text_color="gray50"
        )
        footer_label.pack(expand=True)
    
    def show_welcome_screen(self):
        self.clear_content()
        
        welcome_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        welcome_frame.pack(expand=True, fill="both")
        
        # Center the welcome content
        center_frame = ctk.CTkFrame(welcome_frame, fg_color="transparent")
        center_frame.pack(expand=True)
        
        welcome_title = ctk.CTkLabel(
            center_frame,
            text="🎯 Welcome to FIDEAS",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=("#1f538d", "#14375e")
        )
        welcome_title.pack(pady=(50, 20))
        
        subtitle = ctk.CTkLabel(
            center_frame,
            text="Enterprise Management System",
            font=ctk.CTkFont(size=16),
            text_color=("gray60", "gray40")
        )
        subtitle.pack(pady=(0, 30))
        
        info_text = ctk.CTkLabel(
            center_frame,
            text="Select a menu item from the top menu bar to get started",
            font=ctk.CTkFont(size=14),
            text_color=("gray50", "gray50")
        )
        info_text.pack(pady=10)
    
    def load_user_menus(self):
        """Load menus based on user roles"""
        try:
            user_id = session_manager.get_current_user_id()
            tenant_id = session_manager.get_current_tenant_id()
            
            if not user_id or not tenant_id:
                logger.error("No user or tenant ID found in session", "ModernDashboard")
                return
            
            # Get user menus from service
            self.user_menus = MenuService.get_user_menus(user_id, tenant_id)
            logger.info(f"Loaded {len(self.user_menus)} menu groups for user", "ModernDashboard")
            
            # Render menus in sidebar
            self.render_menus()
            
        except Exception as e:
            logger.error(f"Failed to load user menus: {str(e)}", "ModernDashboard")
            self.show_error_message("Failed to load menus")
    
    def render_menus(self):
        """Render menus in the top menu bar"""
        # Clear existing menu items
        for widget in self.menu_container.winfo_children():
            widget.destroy()
        
        if not self.user_menus:
            no_menu_label = ctk.CTkLabel(
                self.menu_container,
                text="No menus available",
                font=ctk.CTkFont(size=11),
                text_color="gray50"
            )
            no_menu_label.pack(side="left", padx=10)
            return
        
        # Render each main menu horizontally
        for i, menu in enumerate(self.user_menus):
            self.create_top_menu_item(menu, i)
    
    def create_top_menu_item(self, menu: Dict[str, Any], index: int):
        """Create a top menu item with dropdown"""
        menu_btn = ctk.CTkButton(
            self.menu_container,
            text=f"{menu.get('icon', '📁')} {menu['name']}",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=30,
            width=120,
            fg_color=self.theme_primary,
            hover_color=self.theme_secondary,
            command=lambda m=menu, btn=None: self.show_dropdown_menu(m, btn)
        )
        menu_btn.pack(side="left", padx=2)
        
        # Store menu data and button reference
        menu_btn.menu_data = menu
        
        # Update command with button reference
        menu_btn.configure(command=lambda m=menu, btn=menu_btn: self.show_dropdown_menu(m, btn))
    
    def show_dropdown_menu(self, menu: Dict[str, Any], button: ctk.CTkButton):
        """Show floating dropdown menu"""
        if not menu.get('children'):
            return
        
        # Close existing dropdown
        self.close_dropdown()
        
        # Create floating dropdown frame with auto width and height
        self.floating_dropdown = ctk.CTkFrame(self.main_container, corner_radius=8, border_width=2)
        
        # Position below the button
        button.update_idletasks()
        button_x = button.winfo_x()
        button_y = button.winfo_y() + button.winfo_height()
        
        self.floating_dropdown.place(x=button_x, y=button_y + 5)
        
        # Create content frame (no scroll)
        self.scrollable_frame = ctk.CTkFrame(self.floating_dropdown, fg_color="transparent")
        self.scrollable_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Add menu items
        self.create_expandable_menu_items(menu)
        
        # Bring to front
        self.floating_dropdown.lift()
        
        self.current_dropdown = self.floating_dropdown
        
        # Bind click outside to close dropdown
        self.root.bind('<Button-1>', self.on_click_outside, add='+')
    
    def count_menu_items(self, items):
        """Count total menu items including nested ones"""
        count = 0
        for item in items:
            count += 1
            if item.get('children'):
                count += self.count_menu_items(item['children'])
        return count
    
    def create_expandable_menu_items(self, menu: Dict[str, Any]):
        """Create menu items with submenu support"""
        children = menu.get('children', [])
        
        for submenu in children:
            if submenu.get('children'):
                # Has submenu - create expandable item
                self.create_menu_with_submenu(submenu)
            else:
                # No submenu - create simple item
                self.create_simple_menu_item(submenu)
    
    def create_menu_with_submenu(self, menu_item: Dict[str, Any]):
        """Create menu item that shows submenu on the right"""
        icon = menu_item.get('icon', '▶')
        name = menu_item.get('name', 'Unknown')
        
        item_btn = ctk.CTkButton(
            self.scrollable_frame,
            text=f"{icon} {name} ▶",
            font=ctk.CTkFont(size=12),
            height=35,
            anchor='w',
            fg_color='transparent',
            text_color=('gray10', 'gray90'),
            hover_color=('gray80', 'gray20')
        )
        item_btn.pack(fill='x', padx=5, pady=2)
        
        def show_submenu():
            self.show_submenu_popup(menu_item, item_btn)
        
        item_btn.configure(command=show_submenu)
    
    def show_submenu_popup(self, menu_item: Dict[str, Any], parent_btn):
        """Show submenu popup to the right of parent menu"""
        # Close any existing submenu
        if hasattr(self, 'submenu_popup') and self.submenu_popup:
            self.submenu_popup.destroy()
        
        # Create submenu popup in main container
        self.submenu_popup = ctk.CTkFrame(self.main_container, corner_radius=8, border_width=1)
        
        # Get positions relative to main container
        self.main_container.update_idletasks()
        self.floating_dropdown.update_idletasks()
        parent_btn.update_idletasks()
        
        # Calculate position: dropdown_x + dropdown_width, dropdown_y + button_y
        dropdown_x = self.floating_dropdown.winfo_x()
        dropdown_y = self.floating_dropdown.winfo_y()
        dropdown_width = self.floating_dropdown.winfo_reqwidth()
        btn_y = parent_btn.winfo_y()
        
        self.submenu_popup.place(x=dropdown_x + dropdown_width - 10, y=dropdown_y + btn_y)
        
        # Add submenu items
        for child in menu_item.get('children', []):
            self.create_submenu_item(child)
        
        self.submenu_popup.lift()
        
        # Update click outside binding to include submenu
        self.root.bind('<Button-1>', self.on_click_outside, add='+')
    
    def create_submenu_item(self, item: Dict[str, Any]):
        """Create submenu item"""
        icon = item.get('icon', '•')
        name = item.get('name', 'Unknown')
        
        item_btn = ctk.CTkButton(
            self.submenu_popup,
            text=f"{icon} {name}",
            font=ctk.CTkFont(size=11),
            height=30,
            anchor='w',
            fg_color='transparent',
            text_color=('gray10', 'gray90'),
            hover_color=('gray80', 'gray20')
        )
        item_btn.pack(fill='x', padx=5, pady=1)
        
        def on_click():
            self.close_dropdown()
            menu_obj = {
                'name': item.get('name', 'Unknown'),
                'code': item.get('code', ''),
                'module_code': item.get('module_code', '')
            }
            self.load_screen(menu_obj)
        
        item_btn.configure(command=on_click)
    
    def create_inventory_expandable_menu(self):
        """Create expandable menu structure for Inventory module (fallback)"""
        # Define inventory menu structure
        inventory_structure = {
            'Master': {
                'icon': '📋',
                'items': [
                    {'name': 'Unit Master', 'code': 'UNIT_MASTER', 'icon': '📏'},
                    {'name': 'Category Management', 'code': 'CATEGORY_MGMT', 'icon': '🏷️'},
                    {'name': 'Product Management', 'code': 'PRODUCT_MGMT', 'icon': '📦'},
                    {'name': 'Customer Management', 'code': 'INV_CUSTOMER_MGMT', 'icon': '👥'},
                    {'name': 'Supplier Management', 'code': 'SUPPLIER_MGMT', 'icon': '🏭'}
                ]
            },
            'Transaction': {
                'icon': '💼',
                'items': [
                    {'name': 'Purchase Order', 'code': 'PURCHASE_ORDER', 'icon': '🛒'},
                    {'name': 'Sales Order', 'code': 'SALES_ORDER', 'icon': '💰'},
                    {'name': 'Product Waste', 'code': 'PRODUCT_WASTE', 'icon': '🗑️'}
                ]
            },
            'Stocks': {
                'icon': '📊',
                'items': [
                    {'name': 'Stock Details', 'code': 'STOCK_DETAILS', 'icon': '📈'},
                    {'name': 'Stock Meter', 'code': 'STOCK_METER', 'icon': '⚡'},
                    {'name': 'Stock Tracking', 'code': 'STOCK_TRACKING', 'icon': '🔍'}
                ]
            }
        }
        
        # Create expandable sections
        for section_name, section_data in inventory_structure.items():
            self.create_expandable_section(section_name, section_data)
    
    def create_expandable_section(self, section_name: str, section_data: Dict[str, Any]):
        """Create an expandable section with toggle functionality"""
        # Check if section is expanded
        is_expanded = self.expanded_menus.get('Inventory', {}).get(section_name, False)
        
        # Section header frame
        header_frame = tk.Frame(self.scrollable_frame, bg='#f8fafc', height=32, relief='flat', bd=1)
        header_frame.pack(fill='x', padx=2, pady=1)
        header_frame.pack_propagate(False)
        
        # Expand/collapse icon
        expand_icon = '▼' if is_expanded else '▶'
        
        # Header content
        header_label = tk.Label(
            header_frame,
            text=f"{expand_icon} {section_data['icon']} {section_name}",
            bg='#f8fafc',
            fg='#1f538d',
            font=('Arial', 11, 'bold'),
            anchor='w',
            padx=12
        )
        header_label.pack(fill='both', expand=True)
        
        # Container for section items
        items_container = tk.Frame(self.scrollable_frame, bg='white')
        
        # Show/hide items based on expanded state
        if is_expanded:
            items_container.pack(fill='x', padx=2)
            for item in section_data['items']:
                self.create_section_item(items_container, item)
        
        # Toggle functionality
        def toggle_section(event=None):
            current_state = self.expanded_menus.get('Inventory', {}).get(section_name, False)
            new_state = not current_state
            
            # Update state
            if 'Inventory' not in self.expanded_menus:
                self.expanded_menus['Inventory'] = {}
            self.expanded_menus['Inventory'][section_name] = new_state
            
            # Update icon
            new_icon = '▼' if new_state else '▶'
            header_label.configure(text=f"{new_icon} {section_data['icon']} {section_name}")
            
            # Show/hide items
            if new_state:
                items_container.pack(fill='x', padx=2)
                for item in section_data['items']:
                    self.create_section_item(items_container, item)
            else:
                items_container.pack_forget()
                for widget in items_container.winfo_children():
                    widget.destroy()
        
        # Hover effects for header
        def on_header_enter(e):
            header_frame.configure(bg='#e2e8f0')
            header_label.configure(bg='#e2e8f0')
        
        def on_header_leave(e):
            header_frame.configure(bg='#f8fafc')
            header_label.configure(bg='#f8fafc')
        
        # Bind events
        header_frame.bind('<Button-1>', toggle_section)
        header_label.bind('<Button-1>', toggle_section)
        header_frame.bind('<Enter>', on_header_enter)
        header_frame.bind('<Leave>', on_header_leave)
        header_label.bind('<Enter>', on_header_enter)
        header_label.bind('<Leave>', on_header_leave)
    
    def create_section_item(self, parent, item: Dict[str, Any]):
        """Create an item within an expandable section"""
        icon = item.get('icon', '•')
        name = item.get('name', 'Unknown')
        
        item_btn = ctk.CTkButton(
            parent,
            text=f"{icon} {name}",
            font=ctk.CTkFont(size=11),
            height=30,
            anchor='w',
            fg_color='transparent',
            text_color=('gray10', 'gray90'),
            hover_color=('gray80', 'gray20')
        )
        item_btn.pack(fill='x', padx=10, pady=1)
        
        def on_click():
            self.close_dropdown()
            menu_obj = {
                'name': item.get('name', 'Unknown'),
                'code': item.get('code', ''),
                'module_code': item.get('module_code', 'INVENTORY')
            }
            self.load_screen(menu_obj)
        
        item_btn.configure(command=on_click)
    
    def create_simple_menu_item(self, submenu: Dict[str, Any]):
        """Create simple menu item button"""
        icon = submenu.get('icon', '•')
        name = submenu.get('name', 'Unknown')
        
        item_btn = ctk.CTkButton(
            self.scrollable_frame,
            text=f"{icon} {name}",
            font=ctk.CTkFont(size=12),
            height=35,
            anchor='w',
            fg_color='transparent',
            text_color=('gray10', 'gray90'),
            hover_color=('gray80', 'gray20')
        )
        item_btn.pack(fill='x', padx=5, pady=2)
        
        def on_click():
            self.close_dropdown()
            if submenu.get('action') == 'logout':
                self.logout()
            else:
                self.load_screen(submenu)
        
        item_btn.configure(command=on_click)
    
    def show_user_menu(self):
        """Show user dropdown menu"""
        logger.info("User menu clicked", "ModernDashboard")
        
        # Create user menu structure like other menus
        user_menu = {
            'name': 'User Menu',
            'children': [
                {'name': 'Logout', 'icon': '🚪', 'action': 'logout'}
            ]
        }
        
        self.show_dropdown_menu(user_menu, self.user_btn)
    
    def close_dropdown(self):
        """Close current dropdown"""
        if self.floating_dropdown:
            self.floating_dropdown.destroy()
            self.floating_dropdown = None
        if hasattr(self, 'submenu_popup') and self.submenu_popup:
            self.submenu_popup.destroy()
            self.submenu_popup = None
        self.current_dropdown = None
        
        # Unbind click outside event
        try:
            self.root.unbind('<Button-1>')
        except:
            pass
    
    def on_click_outside(self, event):
        """Handle click outside dropdown to close it"""
        if self.current_dropdown:
            # Check if click is outside the dropdown
            widget = event.widget
            dropdown_widgets = []
            
            if self.floating_dropdown:
                dropdown_widgets.extend(self.get_all_children(self.floating_dropdown))
            if hasattr(self, 'submenu_popup') and self.submenu_popup:
                dropdown_widgets.extend(self.get_all_children(self.submenu_popup))
            
            if widget not in dropdown_widgets:
                self.close_dropdown()
    
    def get_all_children(self, widget):
        """Get all child widgets recursively"""
        children = [widget]
        for child in widget.winfo_children():
            children.extend(self.get_all_children(child))
        return children
    
    def load_screen(self, menu: Dict[str, Any]):
        """Load the appropriate screen based on menu selection"""
        try:
            self.clear_content()
            
            # Show loading message
            loading_label = ctk.CTkLabel(
                self.content_area,
                text=f"Loading {menu['name']}...",
                font=ctk.CTkFont(size=16)
            )
            loading_label.pack(expand=True)
            
            # Update UI
            self.root.update()
            
            # Load the appropriate module screen
            module_code = menu.get('module_code', '').upper()
            menu_code = menu.get('code', '')
            
            if module_code == 'ADMIN':
                self.load_admin_screen(menu_code)
            elif module_code == 'INVENTORY':
                self.load_inventory_screen(menu_code)
            elif module_code == 'ACCOUNT':
                self.load_account_screen(menu_code)
            elif module_code == 'CLINIC':
                self.load_clinic_screen(menu_code)
            else:
                self.show_not_implemented(menu['name'])
                
        except Exception as e:
            logger.error(f"Failed to load screen for {menu['name']}: {str(e)}", "ModernDashboard")
            self.show_error_message(f"Failed to load {menu['name']}")
    
    def load_admin_screen(self, menu_code: str):
        """Load admin module screens"""
        from modules.admin_module.admin_module import AdminModule
        
        self.clear_content()
        admin_module = AdminModule(self.content_area)
        
        screen_mapping = {
            'USER_MGMT': admin_module.show_user_screen,
            'ROLE_MGMT': admin_module.show_role_screen,
            'USER_ROLE_MAPPING': admin_module.show_user_role_mapping_screen,
            'MENU_ACCESS': admin_module.show_menu_access_screen,
            'TENANT_UPDATE': admin_module.show_tenant_update_screen,
            'LEGAL_ENTITY_MGMT': admin_module.show_legal_entity_screen,
            'FINANCIAL_YEAR': admin_module.show_financial_year_screen
        }
        
        if menu_code in screen_mapping:
            screen_mapping[menu_code]()
        else:
            self.show_not_implemented(f"Admin - {menu_code}")
    
    def load_inventory_screen(self, menu_code: str):
        """Load inventory module screens"""
        from modules.inventory_module.inventory_module import InventoryModule
        
        self.clear_content()
        inventory_module = InventoryModule(self.content_area)
        
        screen_mapping = {
            'UNIT_MASTER': inventory_module.show_unit_screen,
            'CATEGORY_MGMT': inventory_module.show_category_screen,
            'PRODUCT_MGMT': inventory_module.show_product_screen,

            'INV_CUSTOMER_MGMT': inventory_module.show_customer_screen,
            'SUPPLIER_MGMT': inventory_module.show_supplier_screen,
            'PURCHASE_ORDER': inventory_module.show_purchase_order_screen,
            'SALES_ORDER': inventory_module.show_sales_order_screen,
            'PRODUCT_WASTE': inventory_module.show_product_waste_screen,
            'STOCK_DETAILS': inventory_module.show_stock_details_screen,
            'STOCK_METER': inventory_module.show_stock_meter_screen,
            'STOCK_TRACKING': inventory_module.show_stock_tracking_screen
        }
        
        if menu_code in screen_mapping:
            screen_mapping[menu_code]()
        else:
            self.show_not_implemented(f"Inventory - {menu_code}")
    
    def load_account_screen(self, menu_code: str):
        """Load account module screens"""
        from modules.account_module.account_module import AccountModule
        
        self.clear_content()
        account_module = AccountModule(self.content_area)
        
        screen_mapping = {
            'CHART_ACCOUNTS': account_module.show_account_master_screen,
            'LEDGER': account_module.show_ledger_screen,
            'JOURNAL': account_module.show_journal_screen,
            'VOUCHERS': account_module.show_voucher_screen,
            'PAYMENTS': account_module.show_payment_screen,
            'REPORTS': account_module.show_reports_screen,
            'AR_AGING': account_module.show_ar_aging_screen,
            'AP_AGING': account_module.show_ap_aging_screen,
            'AUDIT_TRAIL': account_module.show_audit_trail_screen,
            'GST_CALCULATOR': account_module.show_gst_calculator_screen
        }
        
        if menu_code in screen_mapping:
            screen_mapping[menu_code]()
        else:
            self.show_not_implemented(f"Account - {menu_code}")
    
    def load_clinic_screen(self, menu_code: str):
        """Load clinic module screens"""
        from modules.clinic_module.clinic_module import ClinicModule
        
        self.clear_content()
        clinic_module = ClinicModule(self.content_area)
        
        screen_mapping = {
            'PATIENT_MGMT': clinic_module.show_patient_screen,
            'DOCTOR_MGMT': clinic_module.show_doctor_screen,
            'APPOINTMENT_MGMT': clinic_module.show_appointment_screen,
            'MEDICAL_RECORDS': clinic_module.show_medical_records_screen,
            'PRESCRIPTION_MGMT': clinic_module.show_prescription_screen,
            'CLINIC_BILLING': clinic_module.show_billing_screen,
            'EMPLOYEE_MGMT': clinic_module.show_employee_screen
        }
        
        if menu_code in screen_mapping:
            screen_mapping[menu_code]()
        else:
            self.show_not_implemented(f"Clinic - {menu_code}")
    
    def show_not_implemented(self, feature_name: str):
        """Show not implemented message"""
        self.clear_content()
        
        not_impl_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        not_impl_frame.pack(expand=True, fill="both")
        
        center_frame = ctk.CTkFrame(not_impl_frame, fg_color="transparent")
        center_frame.pack(expand=True)
        
        icon_label = ctk.CTkLabel(
            center_frame,
            text="🚧",
            font=ctk.CTkFont(size=48)
        )
        icon_label.pack(pady=(50, 20))
        
        title_label = ctk.CTkLabel(
            center_frame,
            text=f"{feature_name}",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 10))
        
        message_label = ctk.CTkLabel(
            center_frame,
            text="This feature is under development",
            font=ctk.CTkFont(size=14),
            text_color="gray50"
        )
        message_label.pack(pady=5)
    
    def show_error_message(self, message: str):
        """Show error message"""
        self.clear_content()
        
        error_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        error_frame.pack(expand=True, fill="both")
        
        center_frame = ctk.CTkFrame(error_frame, fg_color="transparent")
        center_frame.pack(expand=True)
        
        error_label = ctk.CTkLabel(
            center_frame,
            text=f"❌ {message}",
            font=ctk.CTkFont(size=16),
            text_color="red"
        )
        error_label.pack(expand=True)
    
    def clear_content(self):
        """Clear main content area"""
        for widget in self.content_area.winfo_children():
            widget.destroy()
    
    def logout(self):
        """Handle user logout"""
        try:
            # Close any open dropdowns first
            self.close_dropdown()
            
            # Clear session
            session_manager.clear_session()
            logger.info("User logged out successfully", "ModernDashboard")
            
            # Clear all widgets from root
            for widget in self.root.winfo_children():
                widget.destroy()
            
            # Show login screen
            from modules.admin_module.admin_module import AdminModule
            AdminModule(self.root)
            
        except Exception as e:
            logger.error(f"Error during logout: {str(e)}", "ModernDashboard")
            # Force clear and show login anyway
            for widget in self.root.winfo_children():
                widget.destroy()
            from modules.admin_module.admin_module import AdminModule
            AdminModule(self.root)
    
    def destroy(self):
        """Clean up dashboard"""
        if hasattr(self, 'main_container'):
            self.main_container.destroy()