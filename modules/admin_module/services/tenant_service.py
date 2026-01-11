from typing import Dict, Any, Optional
from modules.admin_module.models.entities import Tenant
from modules.admin_module.services.base_service import BaseService
from core.database.connection import db_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware

class TenantService(BaseService):
    def __init__(self):
        super().__init__(Tenant)
    
    @ExceptionMiddleware.handle_exceptions()
    def get_tenant_by_id(self, tenant_id: int) -> Optional[Dict[str, Any]]:
        with db_manager.get_session() as session:
            tenant = session.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant:
                return None
            
            return {
                "id": tenant.id,
                "name": tenant.name,
                "code": tenant.code,
                "description": tenant.description,
                "logo": tenant.logo,
                "tagline": tenant.tagline,
                "address": tenant.address,
                "is_active": tenant.is_active
            }
    
    @ExceptionMiddleware.handle_exceptions()
    def update_tenant(self, tenant_id: int, tenant_data: Dict[str, Any]) -> bool:
        # Validate business_type if provided
        if 'business_type' in tenant_data:
            business_type = tenant_data['business_type'].upper()
            if business_type not in ['TRADING', 'SERVICE', 'HYBRID']:
                raise ValueError("business_type must be TRADING, SERVICE, or HYBRID")
            tenant_data['business_type'] = business_type
        
        with db_manager.get_session() as session:
            tenant = session.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant:
                return False
            
            # Update tenant fields
            for key, value in tenant_data.items():
                if hasattr(tenant, key) and key not in ['id', 'code']:
                    setattr(tenant, key, value)
            
            session.commit()
            return True