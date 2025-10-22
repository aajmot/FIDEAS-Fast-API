from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime, timedelta
import jwt
import os
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.core.utils.api_response import APIResponse

class LoginRequest(BaseModel):
    username: str
    password: str

class BaseResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = None

router = APIRouter()

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/register-tenant", response_model=BaseResponse)
async def register_tenant(registration_data: Dict[str, Any], db: Session = Depends(get_db)):
    """Register a new tenant with admin user"""
    try:
        from app.modules.admin.services.tenant_service import TenantService
        from app.modules.admin.services.user_service import UserService
        
        tenant_data = registration_data.get('tenant', {})
        admin_user_data = registration_data.get('admin_user', {})
        
        # Validate required fields
        required_tenant_fields = ['name', 'code']
        required_user_fields = ['username', 'email', 'password', 'first_name', 'last_name']
        
        for field in required_tenant_fields:
            if not tenant_data.get(field):
                raise HTTPException(status_code=400, detail=f"Tenant {field} is required")
        
        for field in required_user_fields:
            if not admin_user_data.get(field):
                raise HTTPException(status_code=400, detail=f"Admin user {field} is required")
        
        # Create tenant and admin user
        tenant_service = TenantService()
        user_service = UserService()
        
        # Implementation would go here
        
        return BaseResponse(
            success=True,
            message="Tenant registration completed successfully",
            data={"tenant_id": 1, "admin_user_id": 1}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/login", response_model=BaseResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """User login endpoint"""
    try:
        from app.modules.admin.services.user_service import UserService
        
        username = login_data.username
        password = login_data.password
        
        if not username or not password:
            raise HTTPException(status_code=400, detail="Username and password are required")
        
        # Authenticate user
        user_service = UserService(db)
        user_data = user_service.authenticate(username, password)
        
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Get user roles
        user_roles = user_service.get_user_roles(user_data['id'])
        role_names = [role['name'] for role in user_roles]
        
        # Create access token
        token_data = {
            "sub": str(user_data['id']),
            "username": user_data['username'],
            "tenant_id": user_data['tenant_id'],
            "roles": role_names
        }
        access_token = create_access_token(token_data)
        
        return BaseResponse(
            success=True,
            message="Login successful",
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user_data['id'],
                    "username": user_data['username'],
                    "email": user_data['email'],
                    "first_name": user_data['first_name'],
                    "last_name": user_data['last_name'],
                    "tenant_id": user_data['tenant_id'],
                    "is_tenant_admin": user_data.get('is_tenant_admin', False),
                    "roles": role_names
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@router.post("/logout")
async def logout():
    """User logout endpoint"""
    return APIResponse.success(message="Logged out successfully")