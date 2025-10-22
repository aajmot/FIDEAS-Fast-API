from fastapi import APIRouter
from app.api.v1.controllers.admin.user_controller import router as user_router
from app.api.v1.controllers.admin.role_controller import router as role_router
from app.api.v1.controllers.admin.tenant_controller import router as tenant_router
from app.api.v1.controllers.admin.legal_entity_controller import router as legal_entity_router
from app.api.v1.controllers.admin.financial_year_controller import router as financial_year_router
from app.api.v1.controllers.admin.menu_controller import router as menu_router
from app.api.v1.controllers.admin.user_role_controller import router as user_role_router
from app.api.v1.controllers.admin.dashboard_controller import router as dashboard_router

router = APIRouter()

# Include all admin controllers
router.include_router(user_router, tags=["Admin - Users"])
router.include_router(role_router, tags=["Admin - Roles"])
router.include_router(tenant_router, tags=["Admin - Tenant"])
router.include_router(legal_entity_router, tags=["Admin - Legal Entities"])
router.include_router(financial_year_router, tags=["Admin - Financial Years"])
router.include_router(menu_router, tags=["Admin - Menus"])
router.include_router(user_role_router, tags=["Admin - User Roles"])
router.include_router(dashboard_router, tags=["Admin - Dashboard"])