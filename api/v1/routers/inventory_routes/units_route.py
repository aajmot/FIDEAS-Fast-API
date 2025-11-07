from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import io
import csv
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from sqlalchemy import or_
from api.middleware.auth_middleware import get_current_user
from modules.inventory_module.services.unit_service import UnitService

router = APIRouter()


@router.get("/units", response_model=PaginatedResponse)
async def get_units(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.inventory_module.models.entities import Unit

    with db_manager.get_session() as session:
        query = session.query(Unit).filter(
            Unit.tenant_id == current_user['tenant_id']
        )

        if pagination.search:
            search_term = f"%{pagination.search}%"
            query = query.filter(or_(
                Unit.name.ilike(search_term),
                Unit.symbol.ilike(search_term)
            ))

        total = query.count()
        units = query.offset(pagination.offset).limit(pagination.per_page).all()

        unit_data = [{
            "id": unit.id,
            "name": unit.name,
            "symbol": unit.symbol,
            "parent_id": unit.parent_id,
            "conversion_factor": float(unit.conversion_factor) if unit.conversion_factor else 1.0,
            "is_active": unit.is_active
        } for unit in units]

    return PaginatedResponse(
        success=True,
        message="Units retrieved successfully",
        data=unit_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page) if total > 0 else 0
    )


@router.post("/units", response_model=BaseResponse)
async def create_unit(unit_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    unit_service = UnitService()
    unit = unit_service.create(unit_data)
    unit_id = unit.id
    return BaseResponse(
        success=True,
        message="Unit created successfully",
        data={"id": unit_id}
    )


@router.put("/units/{unit_id}", response_model=BaseResponse)
async def update_unit(unit_id: int, unit_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    unit_service = UnitService()
    unit = unit_service.update(unit_id, unit_data)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    return BaseResponse(success=True, message="Unit updated successfully")


@router.delete("/units/{unit_id}", response_model=BaseResponse)
async def delete_unit(unit_id: int, current_user: dict = Depends(get_current_user)):
    unit_service = UnitService()
    success = unit_service.delete(unit_id)
    if not success:
        raise HTTPException(status_code=404, detail="Unit not found")

    return BaseResponse(success=True, message="Unit deleted successfully")


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


@router.post("/units/import", response_model=BaseResponse)
async def import_units(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))

    from core.database.connection import db_manager
    from modules.inventory_module.models.entities import Unit

    imported_count = 0
    with db_manager.get_session() as session:
        for row in csv_data:
            try:
                # Skip header rows - check if name field contains header-like values
                name_value = row.get("name", "").strip().lower()
                if name_value in ["name", "unit name", "unit"] or not name_value:
                    continue

                unit = Unit(
                    name=row["name"],
                    symbol=row["symbol"],
                    tenant_id=current_user['tenant_id'],
                    is_active=row["is_active"].lower() == "true"
                )
                session.add(unit)
                imported_count += 1
            except Exception as e:
                print(f"Error importing unit: {e}")
                continue
        session.commit()

    return BaseResponse(
        success=True,
        message=f"Imported {imported_count} units successfully"
    )
