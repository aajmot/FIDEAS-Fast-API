from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import Dict, Any
from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from fastapi.responses import StreamingResponse
from api.middleware.auth_middleware import get_current_user
import io
import csv
import math

router = APIRouter()


@router.get("/agencies", response_model=PaginatedResponse)
async def get_agencies(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.agency import Agency
    from sqlalchemy import or_

    with db_manager.get_session() as session:
        query = session.query(Agency).filter(
            Agency.tenant_id == current_user['tenant_id'],
            Agency.is_deleted == False
        )

        if pagination.search:
            query = query.filter(or_(
                Agency.name.ilike(f"%{pagination.search}%"),
                Agency.email.ilike(f"%{pagination.search}%"),
                Agency.phone.ilike(f"%{pagination.search}%")
            ))

        total = query.count()
        agencies = query.offset(pagination.offset).limit(pagination.per_page).all()

        agency_data = [{
            "id": agency.id,
            "name": agency.name,
            "phone": agency.phone,
            "email": agency.email,
            "address": agency.address,
            "tax_id": agency.tax_id,
            "created_at": agency.created_at.isoformat() if agency.created_at else None,
            "created_by": agency.created_by,
            "updated_at": agency.updated_at.isoformat() if agency.updated_at else None,
            "updated_by": agency.updated_by
        } for agency in agencies]

    return PaginatedResponse(
        success=True,
        message="Agencies retrieved successfully",
        data=agency_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )


@router.post("/agencies", response_model=BaseResponse)
async def create_agency(agency_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from modules.admin_module.services.agency_service import AgencyService

    agency_service = AgencyService()
    agency = agency_service.create(agency_data)
    return BaseResponse(
        success=True,
        message="Agency created successfully",
        data={"id": agency}
    )


@router.put("/agencies/{agency_id}", response_model=BaseResponse)
async def update_agency(agency_id: int, agency_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from modules.admin_module.services.agency_service import AgencyService

    agency_service = AgencyService()
    agency = agency_service.update(agency_id, agency_data)
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")

    return BaseResponse(success=True, message="Agency updated successfully")


@router.delete("/agencies/{agency_id}", response_model=BaseResponse)
async def delete_agency(agency_id: int, current_user: dict = Depends(get_current_user)):
    from modules.admin_module.services.agency_service import AgencyService

    agency_service = AgencyService()
    success = agency_service.delete(agency_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agency not found")

    return BaseResponse(success=True, message="Agency deleted successfully")


@router.get("/agencies/export-template")
async def export_agencies_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "phone", "email", "address", "tax_id"])
    writer.writerow(["ABC Agency", "123-456-7890", "abc@agency.com", "123 Main St", "TAX001"])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=agencies_template.csv"}
    )


@router.post("/agencies/import", response_model=BaseResponse)
async def import_agencies(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))

    from modules.admin_module.services.agency_service import AgencyService

    agency_service = AgencyService()
    imported_count = 0

    for row in csv_data:
        try:
            agency_data = {
                "name": row["name"],
                "phone": row["phone"],
                "email": row.get("email", ""),
                "address": row.get("address", ""),
                "tax_id": row.get("tax_id", "")
            }

            agency_service.create(agency_data)
            imported_count += 1
        except Exception:
            continue

    return BaseResponse(
        success=True,
        message=f"Imported {imported_count} agencies successfully"
    )
