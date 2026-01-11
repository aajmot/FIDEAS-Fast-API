from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from api.schemas.common import BaseResponse
from api.middleware.auth_middleware import get_current_user
from modules.admin_module.services.tenant_service import TenantService
from modules.admin_module.services.tenant_settings_service import TenantSettingsService

router = APIRouter()
tenant_service = TenantService()
tenant_settings_service = TenantSettingsService()


@router.get("/tenant", response_model=BaseResponse)
async def get_tenant(current_user: dict = Depends(get_current_user)):
    try:
        tenant_data = tenant_service.get_tenant_by_id(current_user["tenant_id"])
        if not tenant_data:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        return BaseResponse(
            success=True,
            message="Tenant retrieved successfully",
            data=tenant_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/tenant", response_model=BaseResponse)
async def update_tenant(tenant_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    try:
        success = tenant_service.update_tenant(current_user["tenant_id"], tenant_data)
        if not success:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        return BaseResponse(
            success=True,
            message="Tenant updated successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenant-settings", response_model=BaseResponse)
async def get_tenant_settings(current_user: dict = Depends(get_current_user)):
    try:
        settings_data = tenant_settings_service.get_tenant_settings(current_user["tenant_id"])
        if not settings_data:
            raise HTTPException(status_code=404, detail="Tenant settings not found")
        
        return BaseResponse(
            success=True,
            message="Tenant settings retrieved successfully",
            data=settings_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/tenant-settings", response_model=BaseResponse)
async def update_tenant_settings(settings_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    try:
        success = tenant_settings_service.update_tenant_settings(
            current_user["tenant_id"], 
            settings_data, 
            current_user["username"]
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Tenant settings not found")
        
        return BaseResponse(
            success=True,
            message="Settings updated successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
