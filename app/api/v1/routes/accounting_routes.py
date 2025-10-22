from fastapi import APIRouter
from app.api.v1.routes.account_routes import router as account_router

router = APIRouter()

# Include account routes
router.include_router(account_router, tags=["Account"])