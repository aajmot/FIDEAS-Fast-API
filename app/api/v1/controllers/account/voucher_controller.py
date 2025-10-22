from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from app.core.utils.api_response import BaseResponse, PaginatedResponse
from app.core.utils.pagination import PaginationParams
from app.modules.account.services.voucher_service import VoucherService

router = APIRouter()

@router.get("/vouchers", response_model=PaginatedResponse)
async def get_vouchers(pagination: PaginationParams = Depends()):
    try:
        service = VoucherService()
        vouchers = service.get_all()
        return PaginatedResponse(
            success=True,
            message="Vouchers retrieved successfully",
            data=[voucher.__dict__ for voucher in vouchers],
            total=len(vouchers),
            page=pagination.page,
            per_page=pagination.per_page,
            total_pages=1
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/vouchers", response_model=BaseResponse)
async def create_voucher(voucher_data: Dict[str, Any]):
    try:
        service = VoucherService()
        voucher = service.create(voucher_data)
        return BaseResponse(
            success=True,
            message="Voucher created successfully",
            data={"id": voucher.id}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/vouchers/{voucher_id}", response_model=BaseResponse)
async def get_voucher(voucher_id: int):
    try:
        service = VoucherService()
        voucher = service.get_by_id(voucher_id)
        if not voucher:
            raise HTTPException(status_code=404, detail="Voucher not found")
        return BaseResponse(
            success=True,
            message="Voucher retrieved successfully",
            data=voucher.__dict__
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/vouchers/{voucher_id}", response_model=BaseResponse)
async def update_voucher(voucher_id: int, voucher_data: Dict[str, Any]):
    try:
        service = VoucherService()
        voucher = service.update(voucher_id, voucher_data)
        return BaseResponse(
            success=True,
            message="Voucher updated successfully",
            data={"id": voucher.id}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/vouchers/{voucher_id}", response_model=BaseResponse)
async def delete_voucher(voucher_id: int):
    try:
        service = VoucherService()
        service.delete(voucher_id)
        return BaseResponse(
            success=True,
            message="Voucher deleted successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))