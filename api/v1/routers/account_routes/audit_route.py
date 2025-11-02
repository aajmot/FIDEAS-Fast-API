from fastapi import APIRouter, Depends, Query
from typing import Optional
from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user
import math

router = APIRouter()


@router.get("/audit-trail", response_model=PaginatedResponse)
async def get_audit_trail(
    pagination: PaginationParams = Depends(),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    from core.database.connection import db_manager
    from modules.account_module.models.audit_trail import AuditTrail
    from sqlalchemy import or_

    with db_manager.get_session() as session:
        query = session.query(AuditTrail).filter(
            AuditTrail.tenant_id == current_user['tenant_id']
        )
        
        if entity_type:
            query = query.filter(AuditTrail.entity_type == entity_type)
        if entity_id:
            query = query.filter(AuditTrail.entity_id == entity_id)
        if pagination.search:
            query = query.filter(or_(
                AuditTrail.username.ilike(f"%{pagination.search}%"),
                AuditTrail.remarks.ilike(f"%{pagination.search}%")
            ))
        
        total = query.count()
        entries = query.order_by(AuditTrail.created_at.desc()).offset(pagination.offset).limit(pagination.per_page).all()
        audit_data = [{
            'id': entry.id,
            'entity_type': entry.entity_type,
            'entity_id': entry.entity_id,
            'action': entry.action,
            'username': entry.username,
            'created_at': entry.created_at.isoformat(),
            'remarks': entry.remarks,
            'old_value': entry.old_value,
            'new_value': entry.new_value
        } for entry in entries]
        
        return PaginatedResponse(
            success=True,
            message="Audit trail retrieved successfully",
            data=audit_data,
            total=total,
            page=pagination.page,
            per_page=pagination.per_page,
            total_pages=math.ceil(total / pagination.per_page) if total else 0
        )
