from fastapi import APIRouter
from app.api.v1.controllers.warehouse.warehouse_controller import router as warehouse_router

router = APIRouter()

# Include warehouse controller
router.include_router(warehouse_router, tags=["Warehouse"])