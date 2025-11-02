from fastapi import APIRouter, Depends
from typing import List, Dict, Any

from api.schemas.common import BaseResponse
from api.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.get("/transaction-templates", response_model=BaseResponse)
async def get_transaction_templates(current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from sqlalchemy import text

    with db_manager.get_session() as session:
        result = session.execute(text("""
            SELECT id, name, code, transaction_type, description, is_active
            FROM transaction_templates
            WHERE tenant_id = :tenant_id
            ORDER BY name
        """), {"tenant_id": current_user["tenant_id"]})

        templates = [{
            "id": row[0],
            "name": row[1],
            "code": row[2],
            "transaction_type": row[3],
            "description": row[4],
            "is_active": row[5]
        } for row in result]

        return BaseResponse(
            success=True,
            message="Templates retrieved successfully",
            data=templates
        )


@router.get("/transaction-templates/{template_id}/rules", response_model=BaseResponse)
async def get_transaction_template_rules(template_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from sqlalchemy import text

    with db_manager.get_session() as session:
        result = session.execute(text("""
            SELECT ttr.id, ttr.line_number, ttr.account_type, ttr.account_id, ttr.entry_type, 
                   ttr.amount_source, ttr.narration, am.name as account_name
            FROM transaction_template_rules ttr
            LEFT JOIN account_masters am ON ttr.account_id = am.id
            WHERE ttr.template_id = :template_id AND ttr.tenant_id = :tenant_id
            ORDER BY ttr.line_number
        """), {"template_id": template_id, "tenant_id": current_user["tenant_id"]})

        rules = [{
            "id": row[0],
            "line_number": row[1],
            "account_type": row[2],
            "account_id": row[3],
            "entry_type": row[4],
            "amount_source": row[5],
            "narration": row[6],
            "account_name": row[7]
        } for row in result]

        return BaseResponse(
            success=True,
            message="Rules retrieved successfully",
            data=rules
        )


@router.put("/transaction-templates/{template_id}/rules", response_model=BaseResponse)
async def update_transaction_template_rules(template_id: int, rules: List[Dict[str, Any]], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from sqlalchemy import text

    with db_manager.get_session() as session:
        session.execute(text("""
            DELETE FROM transaction_template_rules
            WHERE template_id = :template_id AND tenant_id = :tenant_id
        """), {"template_id": template_id, "tenant_id": current_user["tenant_id"]})

        for rule in rules:
            session.execute(text("""
                INSERT INTO transaction_template_rules
                (template_id, line_number, account_type, account_id, entry_type, amount_source, narration, tenant_id)
                VALUES (:template_id, :line_number, :account_type, :account_id, :entry_type, :amount_source, :narration, :tenant_id)
            """), {
                "template_id": template_id,
                "line_number": rule["line_number"],
                "account_type": rule.get("account_type"),
                "account_id": rule.get("account_id"),
                "entry_type": rule["entry_type"],
                "amount_source": rule["amount_source"],
                "narration": rule["narration"],
                "tenant_id": current_user["tenant_id"]
            })

        session.commit()

        return BaseResponse(
            success=True,
            message="Rules updated successfully"
        )
