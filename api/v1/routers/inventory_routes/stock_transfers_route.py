from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from modules.inventory_module.models.stock_transfer_schemas import (
    StockTransferRequest,
    StockTransferResponse,
    StockTransferListResponse
)
from modules.inventory_module.services.stock_transfer_service import StockTransferService

router = APIRouter()
stock_transfer_service = StockTransferService()


@router.post("/stock-transfers", response_model=StockTransferResponse, status_code=201)
def create_stock_transfer(transfer: StockTransferRequest):
    """
    Create a new stock transfer
    """
    try:
        result = stock_transfer_service.create(transfer)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock-transfers", response_model=StockTransferListResponse)
def get_all_stock_transfers(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Filter by status (DRAFT, APPROVED, IN_TRANSIT, COMPLETED, CANCELLED)")
):
    """
    Get all stock transfers with pagination and optional status filter
    """
    try:
        result = stock_transfer_service.get_all(page=page, page_size=page_size, status=status)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock-transfers/{transfer_id}", response_model=StockTransferResponse)
def get_stock_transfer_by_id(transfer_id: int):
    """
    Get a specific stock transfer by ID
    """
    try:
        result = stock_transfer_service.get_by_id(transfer_id)
        if not result:
            raise HTTPException(status_code=404, detail="Stock transfer not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/stock-transfers/{transfer_id}", status_code=204)
def delete_stock_transfer(transfer_id: int):
    """
    Soft delete a stock transfer by ID
    """
    try:
        success = stock_transfer_service.delete(transfer_id)
        if not success:
            raise HTTPException(status_code=404, detail="Stock transfer not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
