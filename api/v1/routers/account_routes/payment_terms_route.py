from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from core.database.connection import db_manager
from sqlalchemy import text, or_
import math

router = APIRouter()

# Payment Terms
@router.get("/payment-terms", response_model=PaginatedResponse)
async def get_payment_terms(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        query = "SELECT * FROM payment_terms WHERE tenant_id = :tenant_id"
        params = {"tenant_id": current_user['tenant_id']}
        
        if pagination.search:
            query += " AND name ILIKE :search"
            params["search"] = f"%{pagination.search}%"
        
        total = session.execute(text(query.replace("*", "COUNT(*)")), params).scalar()
        query += f" ORDER BY name LIMIT :limit OFFSET :offset"
        params.update({"limit": pagination.per_page, "offset": pagination.offset})
        
        result = session.execute(text(query), params)
        data = [dict(row._mapping) for row in result]
    
    return PaginatedResponse(success=True, message="Payment terms retrieved", data=data, 
                           total=total, page=pagination.page, per_page=pagination.per_page,
                           total_pages=math.ceil(total / pagination.per_page))

@router.post("/payment-terms", response_model=BaseResponse)
async def create_payment_term(data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        result = session.execute(text("""
            INSERT INTO payment_terms (name, code, days, description, tenant_id, created_by)
            VALUES (:name, :code, :days, :description, :tenant_id, :created_by)
            RETURNING id
        """), {**data, "tenant_id": current_user['tenant_id'], "created_by": current_user['username']})
        session.commit()
        return BaseResponse(success=True, message="Payment term created", data={"id": result.scalar()})
