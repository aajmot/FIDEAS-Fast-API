from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime, timedelta
import jwt
import os
from pydantic import BaseModel

from api.schemas.common import BaseResponse

class LoginRequest(BaseModel):
    username: str
    password: str
from modules.admin_module.services.tenant_service import TenantService
from modules.admin_module.services.user_service import UserService

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
async def register_tenant(registration_data: Dict[str, Any]):
    """Register a new tenant with admin user"""
    try:
        # Ensure database is properly initialized
        from core.shared.utils.database_initializer import ensure_database_initialized, initialize_tenant_data
        ensure_database_initialized()
        
        from core.database.connection import db_manager
        from modules.admin_module.models.entities import Tenant, User, Role, UserRole, TenantSetting
        
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
        
        # Validate business_type
        business_type = tenant_data.get('business_type', 'TRADING').upper()
        if business_type not in ['TRADING', 'SERVICE', 'HYBRID']:
            raise HTTPException(status_code=400, detail="business_type must be TRADING, SERVICE, or HYBRID")
        
        with db_manager.get_session() as session:
            # Check if tenant code already exists
            existing_tenant = session.query(Tenant).filter(Tenant.code == tenant_data['code']).first()
            if existing_tenant:
                raise HTTPException(status_code=400, detail="Tenant code already exists")
            
            # Check if username already exists
            existing_user = session.query(User).filter(User.username == admin_user_data['username']).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="Username already exists")
            
            # Create tenant
            tenant = Tenant(
                name=tenant_data['name'],
                code=tenant_data['code'],
                tagline=tenant_data.get('tagline', ''),
                address=tenant_data.get('address', ''),
                business_type=business_type,
                created_at=datetime.utcnow()
            )
            session.add(tenant)
            session.flush()  # Get tenant ID
            
            # Create admin role
            admin_role = Role(
                name="Admin",
                description="System Administrator",
                tenant_id=tenant.id,
                created_by="system"
            )
            session.add(admin_role)
            session.flush()
            
            # Create admin user
            admin_user = User(
                username=admin_user_data['username'],
                email=admin_user_data['email'],
                first_name=admin_user_data['first_name'],
                last_name=admin_user_data['last_name'],
                tenant_id=tenant.id,
                is_tenant_admin=True,  # Set as tenant admin
                created_by="system"
            )
            admin_user.set_password(admin_user_data['password'])
            session.add(admin_user)
            session.flush()
            
            # Assign admin role to user
            user_role = UserRole(
                user_id=admin_user.id,
                role_id=admin_role.id,
                tenant_id=tenant.id,
                created_by="system"
            )
            session.add(user_role)
            
            # Assign all modules to tenant
            from modules.admin_module.models.entities import ModuleMaster, TenantModuleMapping
            all_modules = session.query(ModuleMaster).filter_by(is_active=True).all()
            for module in all_modules:
                tenant_module = TenantModuleMapping(
                    tenant_id=tenant.id,
                    module_id=module.id,
                    is_active=True,
                    created_by="system"
                )
                session.add(tenant_module)
            
            # Create default tenant settings
            enable_inventory_value = 'FALSE' if business_type == 'SERVICE' else 'TRUE'
            
            settings = [
                TenantSetting(
                    tenant_id=tenant.id,
                    setting='enable_inventory',
                    description='use stock and COGS entry',
                    value_type='BOOLEAN',
                    value=enable_inventory_value,
                    created_by='system'
                ),
                TenantSetting(
                    tenant_id=tenant.id,
                    setting='enable_gst',
                    description='Apply gst calculation',
                    value_type='BOOLEAN',
                    value='TRUE',
                    created_by='system'
                ),
                TenantSetting(
                    tenant_id=tenant.id,
                    setting='enable_bank_entry',
                    description='Auto create bank receipt/payment',
                    value_type='BOOLEAN',
                    value='TRUE',
                    created_by='system'
                )
            ]
            
            for setting in settings:
                session.add(setting)
            
            session.commit()
            
            # Get IDs before session closes
            tenant_id = tenant.id
            admin_user_id = admin_user.id
            
        # Initialize tenant-specific data outside the session
        try:
            initialize_tenant_data(tenant_id)
        except Exception as e:
            # Log the error but don't fail the registration
            print(f"Warning: Failed to initialize tenant data: {str(e)}")
        
        return BaseResponse(
            success=True,
            message="Tenant registration completed successfully",
            data={"tenant_id": tenant_id, "admin_user_id": admin_user_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/login", response_model=BaseResponse)
async def login(login_data: LoginRequest):
    """User login endpoint"""
    try:
        username = login_data.username
        password = login_data.password
        
        if not username or not password:
            raise HTTPException(status_code=400, detail="Username and password are required")
        
        # Authenticate user
        user_service = UserService()
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