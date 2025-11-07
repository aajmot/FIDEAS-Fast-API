from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from api.schemas.common import BaseResponse
from api.middleware.auth_middleware import get_current_user
from modules.account_module.models.account_configuration_key_schemas import (
    AccountConfigurationKeyRequest,
    AccountConfigurationKeyUpdate,
    AccountConfigurationKeyResponse,
    AccountConfigurationKeyListResponse
)
from modules.account_module.services.account_configuration_key_service import AccountConfigurationKeyService

router = APIRouter()
config_key_service = AccountConfigurationKeyService()


@router.get(
    "/account-configuration-keys",
    response_model=AccountConfigurationKeyListResponse,
    summary="Get all account configuration keys",
    description="Retrieve all account configuration keys with pagination and filters"
)
async def get_configuration_keys(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=500, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by code, name, or description"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    sort_by: str = Query('code', description="Sort by field (code, name, created_at)"),
    sort_order: str = Query('asc', regex='^(asc|desc)$', description="Sort order (asc or desc)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all account configuration keys
    
    Returns a paginated list of account configuration keys with optional filters:
    - Search across code, name, and description
    - Filter by active status
    - Sort by various fields
    
    Configuration keys are system-wide settings that define types of accounts
    (e.g., CASH, BANK, INVENTORY, GST_INPUT) that can be mapped to tenant-specific accounts.
    """
    result = config_key_service.get_all(
        page=page,
        limit=limit,
        search=search,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return result


@router.get(
    "/account-configuration-keys/{key_id}",
    response_model=AccountConfigurationKeyResponse,
    summary="Get configuration key by ID",
    description="Retrieve a specific account configuration key by its ID"
)
async def get_configuration_key(
    key_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific account configuration key by ID"""
    try:
        config_key = config_key_service.get_by_id(key_id)
        return config_key
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve configuration key: {str(e)}")


@router.get(
    "/account-configuration-keys/by-code/{code}",
    response_model=AccountConfigurationKeyResponse,
    summary="Get configuration key by code",
    description="Retrieve a specific account configuration key by its code"
)
async def get_configuration_key_by_code(
    code: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific account configuration key by code (e.g., CASH, BANK, INVENTORY)"""
    try:
        config_key = config_key_service.get_by_code(code.upper())
        return config_key
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve configuration key: {str(e)}")


@router.post(
    "/account-configuration-keys",
    response_model=AccountConfigurationKeyResponse,
    summary="Create configuration key",
    description="Create a new account configuration key"
)
async def create_configuration_key(
    config_key: AccountConfigurationKeyRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new account configuration key
    
    Configuration keys define system-wide account types that can be mapped
    to specific accounts per tenant. Examples: CASH, BANK, INVENTORY, GST_INPUT, etc.
    """
    try:
        result = config_key_service.create(config_key.dict())
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create configuration key: {str(e)}")


@router.put(
    "/account-configuration-keys/{key_id}",
    response_model=AccountConfigurationKeyResponse,
    summary="Update configuration key",
    description="Update an existing account configuration key"
)
async def update_configuration_key(
    key_id: int,
    config_key: AccountConfigurationKeyUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing account configuration key (partial update supported)"""
    try:
        result = config_key_service.update(key_id, config_key.dict(exclude_unset=True))
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update configuration key: {str(e)}")


@router.delete(
    "/account-configuration-keys/{key_id}",
    response_model=BaseResponse,
    summary="Delete configuration key",
    description="Soft delete an account configuration key"
)
async def delete_configuration_key(
    key_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Soft delete a configuration key
    
    Note: This will not delete associated account configurations for tenants.
    Consider the impact before deleting system-wide configuration keys.
    """
    try:
        result = config_key_service.delete(key_id)
        return BaseResponse(
            success=True,
            message=result["message"],
            data={"id": key_id}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete configuration key: {str(e)}")
