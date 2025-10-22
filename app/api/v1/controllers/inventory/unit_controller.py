from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
import io
import csv

from app.db.base import get_db
from app.core.auth.oauth2_scheme import get_current_user
from app.core.utils.api_response import APIResponse
from app.core.utils.pagination import PaginationParams, PaginatedResponse
from app.modules.inventory.services.unit_service import UnitService

router = APIRouter()

@router.get("/units")
async def get_units(
    pagination: PaginationParams = Depends(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    unit_service = UnitService(db)
    units, total = unit_service.get_units_paginated(
        current_user["tenant_id"],
        pagination.search,
        pagination.offset,
        pagination.size
    )
    
    return PaginatedResponse.create(
        items=units,
        total=total,
        page=pagination.page,
        size=pagination.size
    )

@router.post("/units")
async def create_unit(
    unit_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    unit_service = UnitService(db)
    unit_data["tenant_id"] = current_user["tenant_id"]
    unit_data["created_by"] = current_user["username"]
    unit = unit_service.create(unit_data)
    
    return APIResponse.created({"id": unit.id})

@router.put("/units/{unit_id}")
async def update_unit(
    unit_id: int,
    unit_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    unit_service = UnitService(db)
    unit_data["updated_by"] = current_user["username"]
    unit = unit_service.update(unit_id, unit_data)
    
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    return APIResponse.success(message="Unit updated successfully")

@router.delete("/units/{unit_id}")
async def delete_unit(
    unit_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    unit_service = UnitService(db)
    success = unit_service.delete(unit_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    return APIResponse.success(message="Unit deleted successfully")

@router.get("/units/export-template")
async def export_units_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "symbol", "is_active"])
    writer.writerow(["Kilogram", "kg", "true"])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=units_template.csv"}
    )

@router.post("/units/import")
async def import_units(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    unit_service = UnitService(db)
    units_data = list(csv_data)
    imported_count = unit_service.import_units(
        units_data,
        current_user["tenant_id"],
        current_user["username"]
    )
    
    return APIResponse.success(message=f"Imported {imported_count} units successfully")