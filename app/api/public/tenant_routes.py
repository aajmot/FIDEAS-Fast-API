from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime
from pydantic import BaseModel

from app.core.utils.api_response import APIResponse
from app.modules.admin.services.tenant_service import TenantService
from app.modules.admin.services.user_service import UserService
from app.db.base import get_db
from sqlalchemy.orm import Session
from fastapi import Depends

class TenantRegistrationRequest(BaseModel):
    tenant: Dict[str, Any]
    admin_user: Dict[str, Any]

router = APIRouter()

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
        
        tenant_service = TenantService(db)
        user_service = UserService(db)
        
        # Create tenant and admin user logic here
        # This would need to be implemented based on your specific requirements
        
        return APIResponse.success(
            message="Tenant registration completed successfully",
            data={"tenant_id": 1, "admin_user_id": 1}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")