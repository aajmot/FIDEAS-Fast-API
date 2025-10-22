from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional
from app.core.utils.api_response import BaseResponse, PaginatedResponse
from app.core.utils.pagination import PaginationParams
from app.modules.account.services.account_service import AccountService

router = APIRouter()

@router.get("/accounts", response_model=PaginatedResponse)
async def get_accounts(pagination: PaginationParams = Depends()):
    try:
        service = AccountService()
        accounts = service.get_all()
        return PaginatedResponse(
            success=True,
            message="Accounts retrieved successfully",
            data=[account.__dict__ for account in accounts],
            total=len(accounts),
            page=pagination.page,
            per_page=pagination.per_page,
            total_pages=1
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/accounts", response_model=BaseResponse)
async def create_account(account_data: Dict[str, Any]):
    try:
        service = AccountService()
        account = service.create(account_data)
        return BaseResponse(
            success=True,
            message="Account created successfully",
            data={"id": account.id}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/accounts/{account_id}", response_model=BaseResponse)
async def get_account(account_id: int):
    try:
        service = AccountService()
        account = service.get_by_id(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        return BaseResponse(
            success=True,
            message="Account retrieved successfully",
            data=account.__dict__
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/accounts/{account_id}", response_model=BaseResponse)
async def update_account(account_id: int, account_data: Dict[str, Any]):
    try:
        service = AccountService()
        account = service.update(account_id, account_data)
        return BaseResponse(
            success=True,
            message="Account updated successfully",
            data={"id": account.id}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/accounts/{account_id}", response_model=BaseResponse)
async def delete_account(account_id: int):
    try:
        service = AccountService()
        service.delete(account_id)
        return BaseResponse(
            success=True,
            message="Account deleted successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))