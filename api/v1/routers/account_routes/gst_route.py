from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any
from api.schemas.common import BaseResponse
from api.middleware.auth_middleware import get_current_user
from modules.account_module.services.gst_service import GSTService

router = APIRouter()


@router.post("/calculate-gst", response_model=BaseResponse)
async def calculate_gst(
    gst_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Calculate GST amounts"""
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


@router.get("/gstr1", response_model=BaseResponse)
async def get_gstr1(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000),
    current_user: dict = Depends(get_current_user)
):
    """Generate GSTR-1 report for outward supplies"""
    try:
        data = GSTService.get_gstr1_data(month, year)
        return BaseResponse(
            success=True,
            message="GSTR-1 report generated successfully",
            data=data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gstr3b", response_model=BaseResponse)
async def get_gstr3b(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000),
    current_user: dict = Depends(get_current_user)
):
    """Generate GSTR-3B summary return"""
    try:
        data = GSTService.get_gstr3b_data(month, year)
        return BaseResponse(
            success=True,
            message="GSTR-3B report generated successfully",
            data=data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
