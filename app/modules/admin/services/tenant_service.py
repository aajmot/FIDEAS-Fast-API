from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.db.models.admin_models.tenant_model import Tenant, TenantSetting

class TenantService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_tenant(self, tenant_id: int):
        return self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    def update_tenant(self, tenant_id: int, data: Dict[str, Any]):
        # Validate business_type if provided
        if 'business_type' in data:
            business_type = data['business_type'].upper()
            if business_type not in ['TRADING', 'SERVICE', 'HYBRID']:
                raise ValueError("business_type must be TRADING, SERVICE, or HYBRID")
            data['business_type'] = business_type
        
        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            return None
        
        # Update tenant fields
        for key, value in data.items():
            if hasattr(tenant, key) and key not in ['id', 'code']:  # Don't allow updating id or code
                setattr(tenant, key, value)
        
        self.db.commit()
        self.db.refresh(tenant)
        return tenant
    
    def get_tenant_settings(self, tenant_id: int):
        return self.db.query(TenantSetting).filter(
            TenantSetting.tenant_id == tenant_id
        ).all()
    
    def update_tenant_setting(self, tenant_id: int, setting: str, value: str, updated_by: str):
        tenant_setting = self.db.query(TenantSetting).filter(
            TenantSetting.tenant_id == tenant_id,
            TenantSetting.setting == setting
        ).first()
        
        if not tenant_setting:
            return None
        
        tenant_setting.value = value
        tenant_setting.updated_by = updated_by
        self.db.commit()
        self.db.refresh(tenant_setting)
        return tenant_setting