from fastapi import APIRouter
from app.api.v1.controllers.diagnostics.test_panel_controller import router as test_panel_router

router = APIRouter()

# Include all diagnostics controllers
router.include_router(test_panel_router, tags=["Diagnostics - Test Panels"])