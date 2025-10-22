from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.base import get_db
from app.core.auth.oauth2_scheme import get_current_user
from app.core.utils.api_response import APIResponse

class TenantRegistrationRequest(BaseModel):
    tenant: Dict[str, Any]
    admin_user: Dict[str, Any]

router = APIRouter()

@router.get("/tenant")
async def get_tenant(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return APIResponse.success({
        "id": current_user.get("tenant_id"),
        "name": "Sample Tenant",
        "code": "TENANT001",
        "description": "Sample tenant description",
        "is_active": True
    })

@router.put("/tenant")
async def update_tenant(
    tenant_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return APIResponse.success(message="Tenant updated successfully")

@router.get("/tenant-settings")
async def get_tenant_settings(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return APIResponse.success([])

@router.put("/tenant-settings/{setting}")
async def update_tenant_setting(
    setting: str,
    data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return APIResponse.success(message="Setting updated successfully")

@router.post("/register-tenant")
async def register_tenant(
    registration_data: TenantRegistrationRequest,
    db: Session = Depends(get_db)
):
    """Register a new tenant with admin user"""
    try:
        tenant_data = registration_data.tenant
        admin_user_data = registration_data.admin_user
        
        # Validate required fields
        required_tenant_fields = ['name', 'code']
        required_user_fields = ['username', 'email', 'password', 'first_name', 'last_name']
        
        for field in required_tenant_fields:
            if not tenant_data.get(field):
                raise HTTPException(status_code=400, detail=f"Tenant {field} is required")
        
        for field in required_user_fields:
            if not admin_user_data.get(field):
                raise HTTPException(status_code=400, detail=f"Admin user {field} is required")
        
        # Validate business_type
        business_type = tenant_data.get('business_type', 'TRADING').upper()
        if business_type not in ['TRADING', 'SERVICE', 'HYBRID']:
            raise HTTPException(status_code=400, detail="business_type must be TRADING, SERVICE, or HYBRID")
        
        # Implementation would go here
        return APIResponse.success(
            message="Tenant registration completed successfully",
            data={"tenant_id": 1, "admin_user_id": 1}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")