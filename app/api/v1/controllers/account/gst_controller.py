from fastapi import APIRouter
from typing import Dict, Any
from app.core.utils.api_response import BaseResponse

router = APIRouter()

@router.post("/calculate-gst", response_model=BaseResponse)
async def calculate_gst(gst_data: Dict[str, Any]):
    """Calculate GST amounts"""
    try:
        subtotal = gst_data.get('subtotal', 0)
        gst_rate = gst_data.get('gst_rate', 18)
        is_interstate = gst_data.get('is_interstate', False)
        
        # TODO: Implement actual GST calculation logic
        gst_amount = subtotal * (gst_rate / 100)
        
        if is_interstate:
            result = {
                "subtotal": subtotal,
                "igst_rate": gst_rate,
                "igst_amount": gst_amount,
                "cgst_rate": 0,
                "cgst_amount": 0,
                "sgst_rate": 0,
                "sgst_amount": 0,
                "total_gst": gst_amount,
                "total_amount": subtotal + gst_amount
            }
        else:
            cgst_rate = sgst_rate = gst_rate / 2
            cgst_amount = sgst_amount = gst_amount / 2
            result = {
                "subtotal": subtotal,
                "igst_rate": 0,
                "igst_amount": 0,
                "cgst_rate": cgst_rate,
                "cgst_amount": cgst_amount,
                "sgst_rate": sgst_rate,
                "sgst_amount": sgst_amount,
                "total_gst": gst_amount,
                "total_amount": subtotal + gst_amount
            }
        
        return BaseResponse(
            success=True,
            message="GST calculated successfully",
            data=result
        )
    except Exception as e:
        return BaseResponse(
            success=False,
            message=f"GST calculation failed: {str(e)}",
            data={}
        )