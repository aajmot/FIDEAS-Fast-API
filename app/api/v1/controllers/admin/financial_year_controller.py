from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Dict, Any
from sqlalchemy.orm import Session
import io
import csv
import math

from app.db.base import get_db
from app.core.auth.oauth2_scheme import get_current_user
from app.core.utils.api_response import APIResponse
from app.core.utils.pagination import PaginationParams, PaginatedResponse

router = APIRouter()

@router.get("/financial-years")
async def get_financial_years(
    pagination: PaginationParams = Depends(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return PaginatedResponse.create(
        items=[],
        total=0,
        page=pagination.page,
        size=pagination.size
    )

@router.post("/financial-years")
async def create_financial_year(
    year_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return APIResponse.created({"id": 1})

@router.put("/financial-years/{year_id}")
async def update_financial_year(
    year_id: int,
    year_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return APIResponse.success(message="Financial year updated successfully")

@router.delete("/financial-years/{year_id}")
async def delete_financial_year(
    year_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return APIResponse.success(message="Financial year deleted successfully")

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

@router.post("/financial-years/import")
async def import_financial_years(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return APIResponse.success(message="Imported 0 financial years successfully")