from fastapi import APIRouter, Depends
from api.schemas.common import BaseResponse
from api.middleware.auth_middleware import get_current_user

router = APIRouter()

@router.get("/get-user", response_model=BaseResponse)
async def get_user(current_user: dict = Depends(get_current_user)):
    return BaseResponse(
        success=True,
        message="User retrieved successfully (v2)",
        data={
            "user_id": current_user["user_id"],
            "username": current_user["username"],
            "tenant_id": current_user["tenant_id"],
            "api_version": "v2"
        }
    )