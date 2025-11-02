from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import math

from api.schemas.common import BaseResponse
from api.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.get("/tenant", response_model=BaseResponse)
async def get_tenant(current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import Tenant

    with db_manager.get_session() as session:
        tenant = session.query(Tenant).filter(Tenant.id == current_user["tenant_id"]).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        tenant_data = {
            "id": tenant.id,
            "name": tenant.name,
            "code": tenant.code,
            "description": tenant.description,
            "logo": tenant.logo,
            "tagline": tenant.tagline,
            "address": tenant.address,
            "is_active": tenant.is_active
        }

    return BaseResponse(
        success=True,
        message="Tenant retrieved successfully",
        data=tenant_data
    )


@router.put("/tenant", response_model=BaseResponse)
async def update_tenant(tenant_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import Tenant

    # Validate business_type if provided
    if 'business_type' in tenant_data:
        business_type = tenant_data['business_type'].upper()
        if business_type not in ['TRADING', 'SERVICE', 'HYBRID']:
            raise HTTPException(status_code=400, detail="business_type must be TRADING, SERVICE, or HYBRID")
        tenant_data['business_type'] = business_type

    with db_manager.get_session() as session:
        tenant = session.query(Tenant).filter(Tenant.id == current_user["tenant_id"]).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        # Update tenant fields
        for key, value in tenant_data.items():
            if hasattr(tenant, key) and key != 'id' and key != 'code':
                setattr(tenant, key, value)

        session.commit()

        return BaseResponse(
            success=True,
            message="Tenant updated successfully"
        )


@router.get("/tenant-settings", response_model=BaseResponse)
async def get_tenant_settings(current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import TenantSetting

    with db_manager.get_session() as session:
        settings = session.query(TenantSetting).filter(
            TenantSetting.tenant_id == current_user["tenant_id"]
        ).all()

        settings_data = [{
            "id": s.id,
            "setting": s.setting,
            "description": s.description,
            "value_type": s.value_type,
            "value": s.value
        } for s in settings]

    return BaseResponse(
        success=True,
        message="Tenant settings retrieved successfully",
        data=settings_data
    )


@router.put("/tenant-settings/{setting}", response_model=BaseResponse)
async def update_tenant_setting(setting: str, data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import TenantSetting

    with db_manager.get_session() as session:
        tenant_setting = session.query(TenantSetting).filter(
            TenantSetting.tenant_id == current_user["tenant_id"],
            TenantSetting.setting == setting
        ).first()

        if not tenant_setting:
            raise HTTPException(status_code=404, detail="Setting not found")

        tenant_setting.value = data.get("value")
        tenant_setting.updated_by = current_user["username"]
        session.commit()

        return BaseResponse(
            success=True,
            message="Setting updated successfully"
        )
