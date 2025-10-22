from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Dict, Any
from sqlalchemy.orm import Session
import io
import csv

from app.db.base import get_db
from app.core.auth.oauth2_scheme import get_current_user
from app.core.utils.api_response import APIResponse
from app.core.utils.pagination import PaginationParams, PaginatedResponse
from app.modules.admin.services.legal_entity_service import LegalEntityService

router = APIRouter()

@router.get("/legal-entities")
async def get_legal_entities(
    pagination: PaginationParams = Depends(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    legal_entity_service = LegalEntityService(db)
    entity_data, total = legal_entity_service.get_entities_paginated(
        current_user["tenant_id"],
        pagination.search,
        pagination.offset,
        pagination.size
    )
    
    return PaginatedResponse.create(
        items=entity_data,
        total=total,
        page=pagination.page,
        size=pagination.size
    )

@router.post("/legal-entities")
async def create_legal_entity(
    entity_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    legal_entity_service = LegalEntityService(db)
    entity_data["tenant_id"] = current_user["tenant_id"]
    entity_data["created_by"] = current_user["username"]
    entity = legal_entity_service.create(entity_data)
    
    return APIResponse.created({"id": entity.id})

@router.put("/legal-entities/{entity_id}")
async def update_legal_entity(
    entity_id: int,
    entity_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    legal_entity_service = LegalEntityService(db)
    entity_data["updated_by"] = current_user["username"]
    entity = legal_entity_service.update(entity_id, entity_data)
    
    if not entity:
        raise HTTPException(status_code=404, detail="Legal entity not found")
    
    return APIResponse.success(message="Legal entity updated successfully")

@router.delete("/legal-entities/{entity_id}")
async def delete_legal_entity(
    entity_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    legal_entity_service = LegalEntityService(db)
    success = legal_entity_service.delete(entity_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Legal entity not found")
    
    return APIResponse.success(message="Legal entity deleted successfully")

@router.get("/legal-entities/export-template")
async def export_legal_entities_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "code", "registration_number", "address", "logo", "admin_username", "is_active"])
    writer.writerow(["ABC Corp", "ABC001", "REG123456", "123 Main St", "logo.png", "admin_user", "true"])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=legal_entities_template.csv"}
    )

@router.post("/legal-entities/import")
async def import_legal_entities(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    legal_entity_service = LegalEntityService(db)
    entities_data = list(csv_data)
    imported_count = legal_entity_service.import_entities(
        entities_data,
        current_user["tenant_id"],
        current_user["username"]
    )
    
    return APIResponse.success(message=f"Imported {imported_count} legal entities successfully")