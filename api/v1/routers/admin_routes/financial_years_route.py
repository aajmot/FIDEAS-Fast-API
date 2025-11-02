from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import Dict, Any
from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user
import io
import csv
import math

router = APIRouter()


@router.get("/financial-years", response_model=PaginatedResponse)
async def get_financial_years(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import FinancialYear

    with db_manager.get_session() as session:
        query = session.query(FinancialYear).filter(FinancialYear.tenant_id == current_user["tenant_id"])

        if pagination.search:
            query = query.filter(
                FinancialYear.name.ilike(f"%{pagination.search}%")
            )

        query = query.order_by(FinancialYear.start_date.desc())

        total = query.count()
        years = query.offset(pagination.offset).limit(pagination.per_page).all()

        year_data = [{
            "id": year.id,
            "name": year.name,
            "start_date": year.start_date.isoformat() if year.start_date else None,
            "end_date": year.end_date.isoformat() if year.end_date else None,
            "is_active": year.is_active,
            "is_closed": year.is_closed
        } for year in years]

    return PaginatedResponse(
        success=True,
        message="Financial years retrieved successfully",
        data=year_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )


@router.post("/financial-years", response_model=BaseResponse)
async def create_financial_year(year_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import FinancialYear
    from datetime import datetime

    with db_manager.get_session() as session:
        existing = session.query(FinancialYear).filter(
            FinancialYear.tenant_id == current_user["tenant_id"],
            FinancialYear.name == year_data["name"]
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="Financial year name already exists")

        if year_data.get("is_active"):
            session.query(FinancialYear).filter(
                FinancialYear.tenant_id == current_user["tenant_id"],
                FinancialYear.is_active == True
            ).update({"is_active": False})

        year = FinancialYear(
            name=year_data["name"],
            start_date=datetime.fromisoformat(year_data["start_date"]),
            end_date=datetime.fromisoformat(year_data["end_date"]),
            tenant_id=current_user["tenant_id"],
            is_active=year_data.get("is_active", True),
            created_by=current_user["username"]
        )
        session.add(year)
        session.commit()

        return BaseResponse(
            success=True,
            message="Financial year created successfully",
            data={"id": year.id}
        )


@router.put("/financial-years/{year_id}", response_model=BaseResponse)
async def update_financial_year(year_id: int, year_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import FinancialYear
    from datetime import datetime

    with db_manager.get_session() as session:
        year = session.query(FinancialYear).filter(
            FinancialYear.id == year_id,
            FinancialYear.tenant_id == current_user["tenant_id"]
        ).first()

        if not year:
            raise HTTPException(status_code=404, detail="Financial year not found")

        if "name" in year_data:
            existing = session.query(FinancialYear).filter(
                FinancialYear.tenant_id == current_user["tenant_id"],
                FinancialYear.id != year_id,
                FinancialYear.name == year_data.get("name")
            ).first()

            if existing:
                raise HTTPException(status_code=400, detail="Financial year name already exists")

        if year_data.get("is_active") and not year.is_active:
            session.query(FinancialYear).filter(
                FinancialYear.tenant_id == current_user["tenant_id"],
                FinancialYear.is_active == True
            ).update({"is_active": False})

        for key, value in year_data.items():
            if hasattr(year, key) and key not in ['id', 'tenant_id', 'created_at', 'created_by']:
                if key in ['start_date', 'end_date'] and value:
                    setattr(year, key, datetime.fromisoformat(value))
                else:
                    setattr(year, key, value)

        year.updated_by = current_user["username"]
        session.commit()

        return BaseResponse(success=True, message="Financial year updated successfully")


@router.delete("/financial-years/{year_id}", response_model=BaseResponse)
async def delete_financial_year(year_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import FinancialYear

    with db_manager.get_session() as session:
        year = session.query(FinancialYear).filter(
            FinancialYear.id == year_id,
            FinancialYear.tenant_id == current_user["tenant_id"]
        ).first()

        if not year:
            raise HTTPException(status_code=404, detail="Financial year not found")

        session.delete(year)
        session.commit()

        return BaseResponse(success=True, message="Financial year deleted successfully")


@router.get("/financial-years/export-template")
async def export_financial_years_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "start_date", "end_date", "is_active"])
    writer.writerow(["FY 2024-25", "2024-04-01", "2025-03-31", "true"])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=financial_years_template.csv"}
    )


@router.post("/financial-years/import", response_model=BaseResponse)
async def import_financial_years(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.entities import FinancialYear
    from datetime import datetime

    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))

    imported_count = 0

    with db_manager.get_session() as session:
        for row in csv_data:
            try:
                if row.get("is_active", "false").lower() == "true":
                    session.query(FinancialYear).filter(
                        FinancialYear.tenant_id == current_user["tenant_id"],
                        FinancialYear.is_active == True
                    ).update({"is_active": False})

                year = FinancialYear(
                    name=row["name"],
                    start_date=datetime.fromisoformat(row["start_date"]),
                    end_date=datetime.fromisoformat(row["end_date"]),
                    tenant_id=current_user["tenant_id"],
                    is_active=row.get("is_active", "true").lower() == "true",
                    created_by=current_user["username"]
                )
                session.add(year)
                imported_count += 1
            except Exception:
                continue

        session.commit()

    return BaseResponse(
        success=True,
        message=f"Imported {imported_count} financial years successfully"
    )
