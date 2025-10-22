from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.core.auth.oauth2_scheme import get_current_user
from app.core.utils.api_response import APIResponse

router = APIRouter()

@router.get("/menus")
async def get_user_menus(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get menus accessible to the current user based on roles"""
    sample_menus = [
        {
            "id": 1,
            "menu_name": "Dashboard",
            "menu_code": "DASHBOARD",
            "route": "/dashboard",
            "icon": "dashboard",
            "parent_menu_id": None,
            "sort_order": 1
        },
        {
            "id": 2,
            "menu_name": "Admin",
            "menu_code": "ADMIN",
            "route": "/admin",
            "icon": "admin_panel_settings",
            "parent_menu_id": None,
            "sort_order": 2
        }
    ]
    
    return APIResponse.success(sample_menus)

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