from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from sqlalchemy import or_
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user
from modules.health_module.services.test_panel_service import TestPanelService
from modules.health_module.services.test_result_service import TestResultService

router = APIRouter()

@router.get("/testpanels", response_model=PaginatedResponse)
async def get_test_panels(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.health_module.models.diagnostic_entities import TestPanel
    from modules.health_module.models.care_entities import TestCategory
    
    with db_manager.get_session() as session:
        query = session.query(TestPanel).filter(
            TestPanel.tenant_id == current_user["tenant_id"],
            TestPanel.is_deleted == False
        )
        
        if pagination.search:
            query = query.filter(or_(
                TestPanel.name.ilike(f"%{pagination.search}%"),
                TestPanel.description.ilike(f"%{pagination.search}%")
            ))
        
        total = query.count()
        panels = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        panel_data = []
        for panel in panels:
            category = session.query(TestCategory).filter(TestCategory.id == panel.category_id).first() if panel.category_id else None
            panel_data.append({
                "id": panel.id,
                "name": panel.name,
                "description": panel.description,
                "category_id": panel.category_id,
                "category_name": category.name if category else None,
                "cost": float(panel.cost) if panel.cost else None,
                "gst": float(panel.gst) if panel.gst else None,
                "cess": float(panel.cess) if panel.cess else None,
                "expired_on": panel.expired_on.isoformat() if panel.expired_on else None,
                "is_active": panel.is_active,
                "created_at": panel.created_at.isoformat() if panel.created_at else None,
                "created_by": panel.created_by,
                "updated_at": panel.updated_at.isoformat() if panel.updated_at else None,
                "updated_by": panel.updated_by
            })
    
    return PaginatedResponse(
        success=True,
        message="Test panels retrieved successfully",
        data=panel_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/testpanels", response_model=BaseResponse)
async def create_test_panel(panel_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    service = TestPanelService()
    panel_data["tenant_id"] = current_user["tenant_id"]
    panel_data["created_by"] = current_user["username"]
    panel = service.create(panel_data)
    
    return BaseResponse(
        success=True,
        message="Test panel created successfully",
        data={"id": panel.id}
    )

@router.get("/testpanels/{panel_id}", response_model=BaseResponse)
async def get_test_panel(panel_id: int, current_user: dict = Depends(get_current_user)):
    service = TestPanelService()
    panel = service.get_by_id(panel_id, current_user["tenant_id"])
    
    if not panel:
        raise HTTPException(status_code=404, detail="Test panel not found")
    
    items = service.get_items(panel_id, current_user["tenant_id"])
    
    return BaseResponse(
        success=True,
        message="Test panel retrieved successfully",
        data={
            "id": panel.id,
            "name": panel.name,
            "description": panel.description,
            "category_id": panel.category_id,
            "cost": float(panel.cost) if panel.cost else None,
            "gst": float(panel.gst) if panel.gst else None,
            "cess": float(panel.cess) if panel.cess else None,
            "expired_on": panel.expired_on.isoformat() if panel.expired_on else None,
            "is_active": panel.is_active,
            "created_at": panel.created_at.isoformat() if panel.created_at else None,
            "created_by": panel.created_by,
            "updated_at": panel.updated_at.isoformat() if panel.updated_at else None,
            "updated_by": panel.updated_by,
            "items": [{
                "id": item.id,
                "test_id": item.test_id,
                "test_name": item.test_name
            } for item in items]
        }
    )

@router.put("/testpanels/{panel_id}", response_model=BaseResponse)
async def update_test_panel(panel_id: int, panel_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    service = TestPanelService()
    panel_data["updated_by"] = current_user["username"]
    
    for field in ['cost', 'gst', 'cess']:
        if field in panel_data and panel_data[field] == '':
            panel_data[field] = None
    
    if 'category_id' in panel_data and panel_data['category_id'] == '':
        panel_data['category_id'] = None
    
    panel = service.update(panel_id, panel_data)
    
    if not panel:
        raise HTTPException(status_code=404, detail="Test panel not found")
    
    return BaseResponse(success=True, message="Test panel updated successfully")

@router.delete("/testpanels/{panel_id}", response_model=BaseResponse)
async def delete_test_panel(panel_id: int, current_user: dict = Depends(get_current_user)):
    service = TestPanelService()
    success = service.delete(panel_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Test panel not found")
    
    return BaseResponse(success=True, message="Test panel deleted successfully")

@router.get("/testpanels/{panel_id}/items", response_model=BaseResponse)
async def get_test_panel_items(panel_id: int, current_user: dict = Depends(get_current_user)):
    service = TestPanelService()
    items = service.get_items(panel_id, current_user["tenant_id"])
    
    return BaseResponse(
        success=True,
        message="Test panel items retrieved successfully",
        data=[{
            "id": item.id,
            "test_id": item.test_id,
            "test_name": item.test_name,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "created_by": item.created_by,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            "updated_by": item.updated_by
        } for item in items]
    )
