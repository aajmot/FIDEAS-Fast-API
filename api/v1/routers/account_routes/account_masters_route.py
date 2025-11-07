from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from api.schemas.common import BaseResponse
from api.middleware.auth_middleware import get_current_user
from modules.account_module.models.account_master_schemas import (
    AccountMasterRequest,
    AccountMasterResponse,
    AccountMasterListResponse
)
from modules.account_module.services.account_master_service import AccountMasterService

router = APIRouter()
account_master_service = AccountMasterService()


@router.get(
    "/account-masters",
    response_model=AccountMasterListResponse,
    summary="Get all account masters",
    description="Retrieve all account masters with pagination and filters"
)
async def get_account_masters(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=500, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by code, name, or description"),
    account_type: Optional[str] = Query(None, description="Filter by account type"),
    account_group_id: Optional[int] = Query(None, description="Filter by account group"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    parent_id: Optional[int] = Query(None, description="Filter by parent account (null for root accounts)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all account masters
    
    Returns a paginated list of account masters with optional filters:
    - Search across code, name, and description
    - Filter by account type (ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE)
    - Filter by account group
    - Filter by active status
    - Filter by parent account (use parent_id to get child accounts)
    """
    result = account_master_service.get_all(
        page=page,
        page_size=page_size,
        search=search,
        account_type=account_type,
        account_group_id=account_group_id,
        is_active=is_active,
        parent_id=parent_id
    )
    return result


@router.get(
    "/account-masters/{account_id}",
    response_model=AccountMasterResponse,
    summary="Get account master by ID",
    description="Retrieve a specific account master by its ID"
)
async def get_account_master(
    account_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific account master by ID"""
    account = account_master_service.get_by_id(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account master not found")
    return account


@router.post(
    "/account-masters",
    response_model=AccountMasterResponse,
    summary="Create account master",
    description="Create a new account master entry"
)
async def create_account_master(
    account: AccountMasterRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new account master
    
    Creates a new account in the chart of accounts with:
    - Unique code per tenant
    - Account type and normal balance
    - Optional parent-child hierarchy
    - System account protection
    - Opening and current balances
    """
    try:
        result = account_master_service.create(account.dict())
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating account master: {str(e)}")


@router.put(
    "/account-masters/{account_id}",
    response_model=AccountMasterResponse,
    summary="Update account master",
    description="Update an existing account master"
)
async def update_account_master(
    account_id: int,
    account: AccountMasterRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update an existing account master
    
    Updates account details. System accounts cannot be modified.
    Validates:
    - Account code uniqueness
    - Parent account exists and is not self
    - Account group exists
    """
    try:
        result = account_master_service.update(account_id, account.dict())
        if not result:
            raise HTTPException(status_code=404, detail="Account master not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating account master: {str(e)}")


@router.delete(
    "/account-masters/{account_id}",
    response_model=BaseResponse,
    summary="Delete account master",
    description="Soft delete an account master"
)
async def delete_account_master(
    account_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Soft delete an account master
    
    Marks the account as deleted. Cannot delete:
    - System accounts
    - Accounts with child accounts
    """
    try:
        result = account_master_service.delete(account_id)
        if not result:
            raise HTTPException(status_code=404, detail="Account master not found")
        return BaseResponse(
            success=True,
            message="Account master deleted successfully",
            data={"id": account_id}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting account master: {str(e)}")
