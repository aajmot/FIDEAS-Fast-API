from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.core.auth.oauth2_scheme import get_current_user
from app.core.utils.api_response import APIResponse
from app.modules.inventory.services.category_service import CategoryService

router = APIRouter()

@router.get("/categories")
async def get_categories(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category_service = CategoryService(db)
    categories = category_service.get_all()
    
    category_data = [{
        "id": category.id,
        "name": category.name,
        "description": category.description,
        "is_active": category.is_active
    } for category in categories]
    
    return APIResponse.success(category_data)

@router.post("/categories")
async def create_category(
    category_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category_service = CategoryService(db)
    category = category_service.create(category_data)
    return APIResponse.created({"id": category.id})

@router.get("/categories/{category_id}")
async def get_category(
    category_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category_service = CategoryService(db)
    category = category_service.get_by_id(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return APIResponse.success({
        "id": category.id,
        "name": category.name,
        "description": category.description,
        "is_active": category.is_active
    })

@router.put("/categories/{category_id}")
async def update_category(
    category_id: int,
    category_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category_service = CategoryService(db)
    category = category_service.update(category_id, category_data)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return APIResponse.success(message="Category updated successfully")

@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category_service = CategoryService(db)
    success = category_service.delete(category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return APIResponse.success(message="Category deleted successfully")