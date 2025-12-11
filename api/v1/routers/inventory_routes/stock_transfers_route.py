from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse, PaginatedResponse
from modules.inventory_module.models.stock_transfer_schemas import (
    StockTransferCreate,
    StockTransferResponse
)
from modules.inventory_module.services.stock_transfer_service import StockTransferService

router = APIRouter()
stock_transfer_service = StockTransferService()


@router.post("/stock-transfers", response_model=BaseResponse)
def create_stock_transfer(transfer: StockTransferCreate, current_user: dict = Depends(get_current_user)):
    """
    Create a new stock transfer
    """
    try:
        transfer_id = stock_transfer_service.create(
            transfer, 
            current_user['tenant_id'], 
            current_user['username']
        )
        return BaseResponse(
            success=True,
            message="Stock transfer created successfully",
            data={"id": transfer_id}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock-transfers", response_model=PaginatedResponse)
def get_all_stock_transfers(
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """
    Get all stock transfers with pagination
    """
    try:
        result = stock_transfer_service.get_all(
            tenant_id=current_user['tenant_id'],
            page=page, 
            page_size=page_size, 
            status=status
        )
        return PaginatedResponse(
            success=True,
            message="Stock transfers retrieved successfully",
            data=result['data'],
            total=result['total'],
            page=page,
            per_page=page_size,
            total_pages=(result['total'] + page_size - 1) // page_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock-transfers/{transfer_id}", response_model=BaseResponse)
def get_stock_transfer_by_id(transfer_id: int, current_user: dict = Depends(get_current_user)):
    """
    Get a specific stock transfer by ID
    """
    try:
        result = stock_transfer_service.get_by_id(transfer_id, current_user['tenant_id'])
        if not result:
            raise HTTPException(status_code=404, detail="Stock transfer not found")
        return BaseResponse(
            success=True,
            message="Stock transfer retrieved successfully",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
