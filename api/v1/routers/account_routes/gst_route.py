from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from api.schemas.common import BaseResponse
from api.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.post("/calculate-gst", response_model=BaseResponse)
async def calculate_gst(
    gst_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Calculate GST amounts"""
    from modules.account_module.services.gst_service import GSTService

    try:
        result = GSTService.calculate_gst(
            subtotal=gst_data['subtotal'],
            gst_rate=gst_data['gst_rate'],
            is_interstate=gst_data.get('is_interstate', False)
        )
        return BaseResponse(
            success=True,
            message="GST calculated successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
