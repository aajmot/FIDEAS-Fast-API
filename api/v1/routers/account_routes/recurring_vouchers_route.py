from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import math
from api.schemas.common import PaginatedResponse, BaseResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.get("/recurring-vouchers", response_model=PaginatedResponse)
async def get_recurring_vouchers(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from sqlalchemy import text

    with db_manager.get_session() as session:
        query = text("""
            SELECT id, name, voucher_type, frequency, start_date, end_date, description, is_active
            FROM recurring_vouchers
            WHERE tenant_id = :tenant_id
            ORDER BY created_at DESC
        """)

        result = session.execute(query, {"tenant_id": current_user['tenant_id']})
        rows = result.fetchall()

        voucher_data = [{
            "id": row[0],
            "name": row[1],
            "voucher_type": row[2],
            "frequency": row[3],
            "start_date": row[4].isoformat() if row[4] else None,
            "end_date": row[5].isoformat() if row[5] else None,
            "description": row[6] or "",
            "is_active": row[7]
        } for row in rows]

        return PaginatedResponse(
            success=True,
            message="Recurring vouchers retrieved successfully",
            data=voucher_data,
            total=len(voucher_data),
            page=pagination.page,
            per_page=pagination.per_page,
            total_pages=math.ceil(len(voucher_data) / pagination.per_page) if len(voucher_data) > 0 else 0
        )


@router.post("/recurring-vouchers", response_model=BaseResponse)
async def create_recurring_voucher(voucher_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from sqlalchemy import text

    with db_manager.get_session() as session:
        try:
            query = text("""
                INSERT INTO recurring_vouchers (name, voucher_type, frequency, start_date, end_date, description, is_active, tenant_id, created_by, created_at)
                VALUES (:name, :voucher_type, :frequency, :start_date, :end_date, :description, :is_active, :tenant_id, :created_by, NOW())
                RETURNING id
            """)

            result = session.execute(query, {
                "name": voucher_data['name'],
                "voucher_type": voucher_data['voucher_type'],
                "frequency": voucher_data['frequency'],
                "start_date": voucher_data['start_date'],
                "end_date": voucher_data.get('end_date') if voucher_data.get('end_date') else None,
                "description": voucher_data.get('description', ''),
                "is_active": voucher_data.get('is_active', True),
                "tenant_id": current_user['tenant_id'],
                "created_by": current_user['username']
            })

            voucher_id = result.fetchone()[0]
            session.commit()

            return BaseResponse(
                success=True,
                message="Recurring voucher created successfully",
                data={"id": voucher_id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))


@router.put("/recurring-vouchers/{voucher_id}", response_model=BaseResponse)
async def update_recurring_voucher(voucher_id: int, voucher_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from sqlalchemy import text

    with db_manager.get_session() as session:
        try:
            query = text("""
                UPDATE recurring_vouchers
                SET name = :name, voucher_type = :voucher_type, frequency = :frequency,
                    start_date = :start_date, end_date = :end_date, description = :description,
                    is_active = :is_active, updated_at = NOW(), updated_by = :updated_by
                WHERE id = :id AND tenant_id = :tenant_id
            """)

            session.execute(query, {
                "id": voucher_id,
                "name": voucher_data['name'],
                "voucher_type": voucher_data['voucher_type'],
                "frequency": voucher_data['frequency'],
                "start_date": voucher_data['start_date'],
                "end_date": voucher_data.get('end_date') if voucher_data.get('end_date') else None,
                "description": voucher_data.get('description', ''),
                "is_active": voucher_data.get('is_active', True),
                "updated_by": current_user['username'],
                "tenant_id": current_user['tenant_id']
            })

            session.commit()

            return BaseResponse(
                success=True,
                message="Recurring voucher updated successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))


@router.delete("/recurring-vouchers/{voucher_id}", response_model=BaseResponse)
async def delete_recurring_voucher(voucher_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from sqlalchemy import text

    with db_manager.get_session() as session:
        try:
            query = text("""
                DELETE FROM recurring_vouchers
                WHERE id = :id AND tenant_id = :tenant_id
            """)

            session.execute(query, {
                "id": voucher_id,
                "tenant_id": current_user['tenant_id']
            })

            session.commit()

            return BaseResponse(
                success=True,
                message="Recurring voucher deleted successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))
