from fastapi import APIRouter, Depends

from api.schemas.common import BaseResponse
from api.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.get("/account-types", response_model=BaseResponse)
async def get_account_types(current_user: dict = Depends(get_current_user)):
    """
    Get list of allowed account types.
    
    Returns the five standard account types used in the accounting system.
    Each type is returned as an object with a 'value' property for future extensibility.
    """
    account_types = [
        {"value": "LIABILITY"},
        {"value": "EXPENSE"},
        {"value": "ASSET"},
        {"value": "INCOME"},
        {"value": "EQUITY"}
    ]
    
    return BaseResponse(
        success=True,
        message="Account types retrieved successfully",
        data=account_types
    )
