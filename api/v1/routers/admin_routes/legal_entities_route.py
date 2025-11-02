from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import io
import csv
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from sqlalchemy import or_
from api.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.get("/legal-entities", response_model=PaginatedResponse)
async def get_legal_entities(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import LegalEntity

    with db_manager.get_session() as session:
        query = session.query(LegalEntity).filter(LegalEntity.tenant_id == current_user["tenant_id"])

        if pagination.search:
            query = query.filter(or_(
                LegalEntity.name.ilike(f"%{pagination.search}%"),
                LegalEntity.code.ilike(f"%{pagination.search}%")
            ))

        total = query.count()
        entities = query.offset(pagination.offset).limit(pagination.per_page).all()

        entity_data = [{
            "id": e.id,
            "name": e.name,
            "code": e.code,
            "registration_number": getattr(e, "registration_number", None),
            "address": getattr(e, "address", None),
            "is_active": e.is_active
        } for e in entities]

    return PaginatedResponse(
        success=True,
        message="Legal entities retrieved successfully",
        data=entity_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )


@router.post("/legal-entities/import", response_model=BaseResponse)
async def import_legal_entities(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import LegalEntity, User

    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))

    imported_count = 0

    with db_manager.get_session() as session:
        for row in csv_data:
            try:
                name_value = row.get("name", "").strip().lower()
                if name_value in ["name", "entity name", "legal entity name", "company name"] or not name_value:
                    continue

                admin_user = None
                if row.get("admin_username"):
                    admin_user = session.query(User).filter(
                        User.username == row["admin_username"],
                        User.tenant_id == current_user["tenant_id"]
                    ).first()

                entity = LegalEntity(
                    name=row["name"],
                    code=row.get("code"),
                    registration_number=row.get("registration_number"),
                    address=row.get("address"),
                    logo=row.get("logo"),
                    admin_user_id=admin_user.id if admin_user else None,
                    tenant_id=current_user["tenant_id"],
                    is_active=row.get("is_active", "true").lower() == "true",
                    created_by=current_user["username"]
                )
                session.add(entity)
                imported_count += 1
            except Exception:
                continue

        session.commit()

    return BaseResponse(
        success=True,
        message=f"Imported {imported_count} legal entities successfully"
    )
