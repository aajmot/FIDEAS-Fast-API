from fastapi import APIRouter
from app.api.v1.controllers.reports.report_controller import router as report_router

router = APIRouter()

# Include report controller
router.include_router(report_router, tags=["Reports"])