from modules.admin_module.ui.screens.login_screen import LoginScreen

from modules.admin_module.ui.screens.user_screen import UserScreen
from modules.admin_module.ui.screens.role_screen import RoleScreen
from modules.admin_module.ui.screens.tenant_screen import TenantScreen
from modules.admin_module.ui.screens.legal_entity_screen import LegalEntityScreen
from modules.admin_module.ui.screens.user_role_screen import UserRoleScreen
from core.shared.utils.logger import logger

class AdminModule:
    def __init__(self, root):
        self.name = "Admin Module"
        self.root = root
        self.current_screen = None
        self.current_user = None
        
        if root:
            self.show_login_screen()
        
        logger.info("Admin Module initialized", "AdminModule")
    
    def show_login_screen(self):
        self.clear_current_screen()
        self.current_screen = LoginScreen(self.root, self)
    
    def show_dashboard(self):
        self.clear_current_screen()
        from modules.dashboard.modern_dashboard import ModernDashboard
        self.current_screen = ModernDashboard(self.root)
    
    def show_user_screen(self):
        self.clear_current_screen()
        self.current_screen = UserScreen(self.root, self)
    
    def show_role_screen(self):
        self.clear_current_screen()
        self.current_screen = RoleScreen(self.root, self)
    
    def show_tenant_screen(self):
        self.clear_current_screen()
        self.current_screen = TenantScreen(self.root, self)
    
    def show_legal_entity_screen(self):
        self.clear_current_screen()
        self.current_screen = LegalEntityScreen(self.root, self)
    
    def show_user_role_mapping_screen(self):
        self.clear_current_screen()
        from modules.admin_module.ui.screens.user_role_mapping_screen import UserRoleMappingScreen
        self.current_screen = UserRoleMappingScreen(self.root, self)
    
    def show_financial_year_screen(self):
        self.clear_current_screen()
        from modules.admin_module.ui.screens.financial_year_screen import FinancialYearScreen
        self.current_screen = FinancialYearScreen(self.root, self)
    
    def show_tenant_update_screen(self):
        self.clear_current_screen()
        from modules.admin_module.ui.screens.tenant_update_screen import TenantUpdateScreen
        self.current_screen = TenantUpdateScreen(self.root, self)
    
    def show_menu_access_screen(self):
        self.clear_current_screen()
        from modules.admin_module.ui.screens.menu_access_screen import MenuAccessScreen
        self.current_screen = MenuAccessScreen(self.root)
    
    def clear_current_screen(self):
        if self.current_screen:
            self.current_screen.destroy()
        
        logger.info("Screen cleared", "AdminModule")
    
    def show_inventory_module(self):
        self.clear_current_screen()
        from modules.inventory_module.inventory_module import InventoryModule
        inventory_module = InventoryModule(self.root)
        # Inventory screens are now accessed through modern dashboard
        pass
    
    def show_account_module(self):
        self.clear_current_screen()
        # Account module screens are now accessed through modern dashboard
        pass
    
    def show_clinic_module(self):
        self.clear_current_screen()
        from modules.clinic_module.clinic_module import ClinicModule
        clinic_module = ClinicModule(self.root)
        # Clinic screens are now accessed through modern dashboard
        pass
    

    

    
    def initialize_data(self):
        """Initialize default data for admin module"""
        from modules.admin_module.services.tenant_service import TenantService
        from modules.admin_module.services.role_service import RoleService
        from modules.admin_module.services.user_service import UserService
        from modules.admin_module.services.module_service import ModuleService, TenantModuleService
        
        tenant_service = TenantService()
        role_service = RoleService()
        user_service = UserService()
        module_service = ModuleService()
        tenant_module_service = TenantModuleService()
        
        # Initialize modules first
        module_service.initialize_default_modules()
        
        # Create default tenant
        tenants = tenant_service.get_all()
        if not tenants:
            tenant_data = {
                'name': 'Default Tenant',
                'description': 'Default tenant for the application'
            }
            tenant_service.create(tenant_data)
            logger.info("Default tenant created", "AdminModule")
        
        # Use tenant ID 1 (first tenant)
        tenant_id = 1
        
        # Assign all modules to default tenant
        modules = module_service.get_available_modules()
        for module in modules:
            try:
                tenant_module_service.assign_module_to_tenant(tenant_id, module.id, 'system')
            except Exception:
                pass  # Module already assigned
        
        # Create default roles
        roles = role_service.get_all()
        if not roles:
            default_roles = [
                {'name': 'Admin', 'description': 'System Administrator', 'tenant_id': tenant_id},
                {'name': 'User', 'description': 'Regular User', 'tenant_id': tenant_id},
                {'name': 'Manager', 'description': 'Manager Role', 'tenant_id': tenant_id}
            ]
            for role_data in default_roles:
                role_service.create(role_data)
            logger.info("Default roles created", "AdminModule")
        
        # Create default admin user
        users = user_service.get_all()
        if not users:
            # Create user without password first
            admin_data = {
                'username': 'admin',
                'email': 'admin@example.com',
                'first_name': 'System',
                'last_name': 'Administrator',
                'tenant_id': tenant_id,
                'password_hash': 'temp'
            }
            
            # Use user service to create and set password properly
            from core.database.connection import db_manager
            with db_manager.get_session() as session:
                from modules.admin_module.models.entities import User
                admin_user = User(**admin_data)
                admin_user.set_password('admin123')
                session.add(admin_user)
                session.flush()
                user_id = admin_user.id
            
            # Assign admin role
            with db_manager.get_session() as session:
                from modules.admin_module.models.entities import UserRole
                user_role = UserRole(
                    user_id=user_id,
                    role_id=1,
                    tenant_id=tenant_id,
                    assigned_by=user_id,
                    created_by='system'
                )
                session.add(user_role)
            
            logger.info("Default admin user created", "AdminModule")