from fastapi import APIRouter, Depends

from api.schemas.common import BaseResponse
from api.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.get("/accounts", response_model=BaseResponse)
async def get_accounts(current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from sqlalchemy import text

    with db_manager.get_session() as session:
        result = session.execute(text("""
            SELECT am.id, am.name, am.code, ag.name as group_name
            FROM account_masters am
            JOIN account_groups ag ON am.account_group_id = ag.id
            WHERE am.tenant_id = :tenant_id AND am.is_active = true
            ORDER BY am.code
        """), {"tenant_id": current_user["tenant_id"]})

        accounts = [{
            "id": row[0],
            "name": row[1],
            "code": row[2],
            "group_name": row[3]
        } for row in result]

        return BaseResponse(
            success=True,
            message="Accounts retrieved successfully",
            data=accounts
        )
