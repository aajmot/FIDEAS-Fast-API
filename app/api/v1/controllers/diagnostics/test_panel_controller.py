from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.core.auth.oauth2_scheme import get_current_user
from app.core.utils.api_response import APIResponse
from app.modules.diagnostics.services.test_panel_service import TestPanelService

router = APIRouter()

@router.get("/test-panels")
async def get_test_panels(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    test_panel_service = TestPanelService(db)
    test_panels = test_panel_service.get_all()
    
    panel_data = [{
        "id": panel.id,
        "name": panel.name,
        "description": panel.description,
        "cost": float(panel.cost) if panel.cost else 0,
        "gst": float(panel.gst) if panel.gst else 0,
        "is_active": panel.is_active
    } for panel in test_panels]
    
    return APIResponse.success(panel_data)

@router.post("/test-panels")
async def create_test_panel(
    panel_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    test_panel_service = TestPanelService(db)
    panel = test_panel_service.create(panel_data)
    return APIResponse.created({"id": panel.id})