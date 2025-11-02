from fastapi import APIRouter, Depends
from typing import Dict, Any

from api.schemas.common import BaseResponse
from api.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.get("/account-type-mappings", response_model=BaseResponse)
async def get_account_type_mappings(current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from sqlalchemy import text

    with db_manager.get_session() as session:
        result = session.execute(text("""
            SELECT atm.id, atm.account_type, atm.account_id, am.name as account_name, am.code as account_code
            FROM account_type_mappings atm
            JOIN account_masters am ON atm.account_id = am.id
            WHERE atm.tenant_id = :tenant_id
            ORDER BY atm.account_type
        """), {"tenant_id": current_user["tenant_id"]})

        mappings = [{
            "id": row[0],
            "account_type": row[1],
            "account_id": row[2],
            "account_name": row[3],
            "account_code": row[4]
        } for row in result]

        return BaseResponse(
            success=True,
            message="Account type mappings retrieved successfully",
            data=mappings
        )


@router.put("/account-type-mappings/{account_type}", response_model=BaseResponse)
async def update_account_type_mapping(account_type: str, data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from sqlalchemy import text

    with db_manager.get_session() as session:
        existing = session.execute(text("""
            SELECT id FROM account_type_mappings
            WHERE account_type = :account_type AND tenant_id = :tenant_id
        """), {"account_type": account_type, "tenant_id": current_user["tenant_id"]}).fetchone()

        if existing:
            session.execute(text("""
                UPDATE account_type_mappings
                SET account_id = :account_id
                WHERE account_type = :account_type AND tenant_id = :tenant_id
            """), {
                "account_id": data["account_id"],
                "account_type": account_type,
                "tenant_id": current_user["tenant_id"]
            })
        else:
            session.execute(text("""
                INSERT INTO account_type_mappings (account_type, account_id, tenant_id, created_by)
                VALUES (:account_type, :account_id, :tenant_id, :created_by)
            """), {
                "account_type": account_type,
                "account_id": data["account_id"],
                "tenant_id": current_user["tenant_id"],
                "created_by": current_user["username"]
            })

        session.commit()

        return BaseResponse(
            success=True,
            message="Account type mapping updated successfully"
        )
