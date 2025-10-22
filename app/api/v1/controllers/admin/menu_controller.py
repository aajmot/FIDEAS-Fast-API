from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.core.auth.oauth2_scheme import get_current_user
from app.core.utils.api_response import APIResponse
from app.modules.admin.services.menu_service import MenuService

router = APIRouter()

@router.get("/menus")
async def get_user_menus(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get menus accessible to the current user based on roles"""
    menu_service = MenuService(db)
    menus = menu_service.get_user_menus(current_user["user_id"], current_user["tenant_id"])
    return APIResponse.success(menus)

@router.get("/role-menu-mappings")
async def get_role_menu_mappings(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return APIResponse.success([])

@router.get("/role-menu-mappings/{role_id}/menus")
async def get_role_menus(
    role_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return APIResponse.success([])

@router.put("/role-menu-mappings/{role_id}/menus")
async def update_role_menus(
    role_id: int,
    menu_mappings: List[Dict[str, Any]],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return APIResponse.success(message="Role menu mappings updated successfully")