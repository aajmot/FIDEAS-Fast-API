from fastapi import APIRouter
from app.api.v1.controllers.notifications.notification_controller import router as notification_router

router = APIRouter()

# Include notification controller
router.include_router(notification_router, tags=["Notifications"])