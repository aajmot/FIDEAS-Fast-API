from fastapi import APIRouter, Depends

from api.schemas.common import BaseResponse
from api.middleware.auth_middleware import get_current_user
from modules.account_module.models.account_configuration_schemas import (
    AccountConfigurationRequest,
    AccountConfigurationResponse
)

router = APIRouter()


@router.get(
    "/account-configurations", 
    response_model=BaseResponse,
    summary="Get all account configurations",
    description="Retrieve all account configurations for the current tenant. Returns configuration key mappings to account masters with optional module-specific settings."
)
async def get_account_configurations(current_user: dict = Depends(get_current_user)):
    """
    Get all account configurations
    
    Returns a list of all account configurations including:
    - Configuration key (code and name)
    - Mapped account details (ID, name, code)
    - Module-specific configuration (if applicable)
    
    Example response data:
    ```json
    [
        {
            "id": 1,
            "config_key": "INVENTORY",
            "config_name": "Inventory Account",
            "account_id": 501,
            "account_name": "Stock Inventory",
            "account_code": "INV001",
            "module": "PURCHASE"
        }
    ]
    ```
    """
    from core.database.connection import db_manager
    from sqlalchemy import text

    with db_manager.get_session() as session:
        result = session.execute(text("""
            SELECT ac.id, ack.code as config_key, ack.name as config_name, ac.account_id, 
                   am.name as account_name, am.code as account_code, ac.module
            FROM account_configurations ac
            JOIN account_configuration_keys ack ON ac.config_key_id = ack.id
            JOIN account_masters am ON ac.account_id = am.id
            WHERE ac.tenant_id = :tenant_id AND ac.is_deleted = FALSE
            ORDER BY ack.code, ac.module
        """), {"tenant_id": current_user["tenant_id"]})

        configurations = [{
            "id": row[0],
            "config_key": row[1],
            "config_name": row[2],
            "account_id": row[3],
            "account_name": row[4],
            "account_code": row[5],
            "module": row[6]
        } for row in result]

        return BaseResponse(
            success=True,
            message="Account configurations retrieved successfully",
            data=configurations
        )


@router.put(
    "/account-configurations/{config_key}", 
    response_model=BaseResponse,
    summary="Create or update account configuration",
    description="Create or update an account configuration mapping for a specific configuration key. Supports module-specific configurations."
)
async def update_account_configuration(
    config_key: str, 
    data: AccountConfigurationRequest, 
    current_user: dict = Depends(get_current_user)
):
    """
    Create or update account configuration
    
    Maps a configuration key to an account master. If a module is specified,
    the configuration will be module-specific (e.g., separate INVENTORY account for PURCHASE vs SALES).
    
    **Path Parameters:**
    - config_key: Configuration key code (e.g., INVENTORY, GST_OUTPUT, ACCOUNTS_RECEIVABLE)
    
    **Request Body:**
    - account_id: ID of the account master to map
    - module: (Optional) Module-specific configuration (PURCHASE, SALES, INVENTORY, etc.)
    
    **Example:**
    ```json
    {
        "account_id": 501,
        "module": "PURCHASE"
    }
    ```
    """
    from core.database.connection import db_manager
    from sqlalchemy import text

    with db_manager.get_session() as session:
        # Get config_key_id
        config_key_result = session.execute(text("""
            SELECT id FROM account_configuration_keys
            WHERE code = :config_key
        """), {"config_key": config_key}).fetchone()

        if not config_key_result:
            return BaseResponse(
                success=False,
                message=f"Configuration key '{config_key}' not found"
            )

        config_key_id = config_key_result[0]
        module = data.module

        # Check if configuration exists
        existing = session.execute(text("""
            SELECT id FROM account_configurations
            WHERE config_key_id = :config_key_id 
            AND tenant_id = :tenant_id 
            AND (module = :module OR (module IS NULL AND :module IS NULL))
            AND is_deleted = FALSE
        """), {
            "config_key_id": config_key_id,
            "tenant_id": current_user["tenant_id"],
            "module": module
        }).fetchone()

        if existing:
            session.execute(text("""
                UPDATE account_configurations
                SET account_id = :account_id,
                    updated_by = :updated_by,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """), {
                "account_id": data.account_id,
                "updated_by": current_user["username"],
                "id": existing[0]
            })
        else:
            session.execute(text("""
                INSERT INTO account_configurations (config_key_id, account_id, module, tenant_id, created_by)
                VALUES (:config_key_id, :account_id, :module, :tenant_id, :created_by)
            """), {
                "config_key_id": config_key_id,
                "account_id": data.account_id,
                "module": module,
                "tenant_id": current_user["tenant_id"],
                "created_by": current_user["username"]
            })

        session.commit()

        return BaseResponse(
            success=True,
            message="Account configuration updated successfully"
        )


@router.delete(
    "/account-configurations/{config_id}", 
    response_model=BaseResponse,
    summary="Delete account configuration",
    description="Soft delete an account configuration by ID. The configuration will be marked as deleted but retained in the database."
)
async def delete_account_configuration(config_id: int, current_user: dict = Depends(get_current_user)):
    """
    Delete account configuration
    
    Performs a soft delete of the account configuration. The record is marked as deleted
    but retained in the database for audit purposes.
    
    **Path Parameters:**
    - config_id: ID of the configuration to delete
    """
    from core.database.connection import db_manager
    from sqlalchemy import text

    with db_manager.get_session() as session:
        # Soft delete the configuration
        result = session.execute(text("""
            UPDATE account_configurations
            SET is_deleted = TRUE,
                updated_by = :updated_by,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :config_id AND tenant_id = :tenant_id
        """), {
            "config_id": config_id,
            "tenant_id": current_user["tenant_id"],
            "updated_by": current_user["username"]
        })

        if result.rowcount == 0:
            return BaseResponse(
                success=False,
                message="Account configuration not found"
            )

        session.commit()

        return BaseResponse(
            success=True,
            message="Account configuration deleted successfully"
        )
