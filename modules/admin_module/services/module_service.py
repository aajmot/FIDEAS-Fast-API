from modules.admin_module.models.entities import ModuleMaster, TenantModuleMapping
from modules.admin_module.services.base_service import BaseService
from core.database.connection import db_manager
from core.shared.utils.logger import logger

class ModuleService(BaseService):
    def __init__(self):
        super().__init__(ModuleMaster)
    
    def initialize_default_modules(self):
        """Initialize default modules"""
        with db_manager.get_session() as session:
            existing_modules = session.query(ModuleMaster).count()
            if existing_modules == 0:
                default_modules = [
                    {'module_name': 'Admin', 'module_code': 'ADMIN', 'description': 'User and system administration', 'is_mandatory': True},
                    {'module_name': 'Inventory', 'module_code': 'INVENTORY', 'description': 'Inventory and stock management', 'is_mandatory': False},
                    {'module_name': 'Account', 'module_code': 'ACCOUNT', 'description': 'Financial accounting and reporting', 'is_mandatory': False},
                    {'module_name': 'Clinic', 'module_code': 'CLINIC', 'description': 'Healthcare and clinic management', 'is_mandatory': False}
                ]
                
                for module_data in default_modules:
                    module = ModuleMaster(**module_data)
                    session.add(module)
                
                session.commit()
                logger.info("Default modules initialized", "ModuleService")
    
    def get_tenant_modules(self, tenant_id):
        """Get all modules assigned to a tenant"""
        with db_manager.get_session() as session:
            return session.query(ModuleMaster).join(TenantModuleMapping).filter(
                TenantModuleMapping.tenant_id == tenant_id,
                TenantModuleMapping.is_active == True,
                ModuleMaster.is_active == True
            ).all()
    
    def get_available_modules(self):
        """Get all available modules"""
        with db_manager.get_session() as session:
            return session.query(ModuleMaster).filter(ModuleMaster.is_active == True).all()

class TenantModuleService(BaseService):
    def __init__(self):
        super().__init__(TenantModuleMapping)
    
    def assign_module_to_tenant(self, tenant_id, module_id, created_by=None):
        """Assign a module to a tenant"""
        with db_manager.get_session() as session:
            existing = session.query(TenantModuleMapping).filter(
                TenantModuleMapping.tenant_id == tenant_id,
                TenantModuleMapping.module_id == module_id
            ).first()
            
            if existing:
                existing.is_active = True
                session.commit()
                return existing
            else:
                tenant_module = TenantModuleMapping(
                    tenant_id=tenant_id,
                    module_id=module_id,
                    created_by=created_by or 'system'
                )
                session.add(tenant_module)
                session.commit()
                return tenant_module
    
    def remove_module_from_tenant(self, tenant_id, module_id):
        """Remove a module from a tenant (only if not mandatory)"""
        with db_manager.get_session() as session:
            module = session.query(ModuleMaster).filter(ModuleMaster.id == module_id).first()
            if module and module.is_mandatory:
                raise ValueError("Cannot remove mandatory module")
            
            tenant_module = session.query(TenantModuleMapping).filter(
                TenantModuleMapping.tenant_id == tenant_id,
                TenantModuleMapping.module_id == module_id
            ).first()
            
            if tenant_module:
                tenant_module.is_active = False
                session.commit()
    
    def get_tenant_module_mappings(self, tenant_id):
        """Get all module mappings for a tenant"""
        with db_manager.get_session() as session:
            return session.query(TenantModuleMapping).filter(
                TenantModuleMapping.tenant_id == tenant_id,is_active=True,is_deleted=False
            ).all()