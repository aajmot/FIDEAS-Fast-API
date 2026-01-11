from typing import Dict, Any, Optional
from datetime import datetime
from modules.admin_module.models.entities import TenantSetting
from core.database.connection import db_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware

class TenantSettingsService:
    
    @ExceptionMiddleware.handle_exceptions()
    def get_tenant_settings(self, tenant_id: int) -> Optional[Dict[str, Any]]:
        """Get tenant settings as simple key-value dict"""
        with db_manager.get_session() as session:
            settings = session.query(TenantSetting).filter(
                TenantSetting.tenant_id == tenant_id
            ).first()
            
            if not settings:
                return None
            
            return {
                "id": settings.id,
                "tenant_id": settings.tenant_id,
                "enable_inventory": settings.enable_inventory,
                "enable_gst": settings.enable_gst,
                "enable_bank_entry": settings.enable_bank_entry,
                "base_currency": settings.base_currency,
                "payment_modes": settings.payment_modes,
                "default_payment_mode": settings.default_payment_mode
            }
    
    @ExceptionMiddleware.handle_exceptions()
    def update_tenant_settings(self, tenant_id: int, settings_data: Dict[str, Any], username: str) -> bool:
        """Update tenant settings with dict of values"""
        with db_manager.get_session() as session:
            tenant_setting = session.query(TenantSetting).filter(
                TenantSetting.tenant_id == tenant_id
            ).first()
            
            if not tenant_setting:
                return False
            
            # Update fields directly
            for key, value in settings_data.items():
                if hasattr(tenant_setting, key) and key not in ['id', 'tenant_id', 'created_at', 'created_by']:
                    setattr(tenant_setting, key, value)
            
            tenant_setting.updated_by = username
            tenant_setting.updated_at = datetime.utcnow()
            session.commit()
            return True
