from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Dict, Any
from sqlalchemy import or_
import math
import io
import csv

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user
from modules.health_module.services.test_category_service import TestCategoryService
from modules.health_module.services.test_service import TestService

router = APIRouter()


@router.get("/testcategories", response_model=PaginatedResponse)
async def get_test_categories(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.health_module.models.care_entities import TestCategory
    
    with db_manager.get_session() as session:
        query = session.query(TestCategory).filter(
            TestCategory.tenant_id == current_user["tenant_id"],
            TestCategory.is_deleted == False
        )
        
        if pagination.search:
            query = query.filter(or_(
                TestCategory.name.ilike(f"%{pagination.search}%"),
                TestCategory.description.ilike(f"%{pagination.search}%")
            ))
        
        total = query.count()
        categories = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        category_data = [{
            "id": cat.id,
            "name": cat.name,
            "description": cat.description,
            "is_active": cat.is_active,
            "created_at": cat.created_at.isoformat() if cat.created_at else None,
            "created_by": cat.created_by,
            "updated_at": cat.updated_at.isoformat() if cat.updated_at else None,
            "updated_by": cat.updated_by
        } for cat in categories]
    
    return PaginatedResponse(
        success=True,
        message="Test categories retrieved successfully",
        data=category_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/testcategories", response_model=BaseResponse)
async def create_test_category(category_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    service = TestCategoryService()
    category_data["tenant_id"] = current_user["tenant_id"]
    category_data["created_by"] = current_user["username"]
    category = service.create(category_data)
    
    return BaseResponse(
        success=True,
        message="Test category created successfully",
        data={"id": category.id}
    )

@router.get("/testcategories/export-template")
async def export_test_categories_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "description", "is_active"])
    writer.writerow(["Blood Tests", "All blood related tests", "true"])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=test_categories_template.csv"}
    )

@router.post("/testcategories/import", response_model=BaseResponse)
async def import_test_categories(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    service = TestCategoryService()
    imported_count = 0
    
    for row in csv_data:
        try:
            service.create({
                "name": row["name"],
                "description": row.get("description", ""),
                "is_active": row.get("is_active", "true").lower() == "true",
                "tenant_id": current_user["tenant_id"],
                "created_by": current_user["username"]
            })
            imported_count += 1
        except Exception:
            continue
    
    return BaseResponse(
        success=True,
        message=f"Imported {imported_count} test categories successfully"
    )

@router.get("/testcategories/{category_id}", response_model=BaseResponse)
async def get_test_category(category_id: int, current_user: dict = Depends(get_current_user)):
    service = TestCategoryService()
    category = service.get_by_id(category_id, current_user["tenant_id"])
    
    if not category:
        raise HTTPException(status_code=404, detail="Test category not found")
    
    return BaseResponse(
        success=True,
        message="Test category retrieved successfully",
        data={
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "is_active": category.is_active,
            "created_at": category.created_at.isoformat() if category.created_at else None,
            "created_by": category.created_by,
            "updated_at": category.updated_at.isoformat() if category.updated_at else None,
            "updated_by": category.updated_by
        }
    )

@router.put("/testcategories/{category_id}", response_model=BaseResponse)
async def update_test_category(category_id: int, category_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    service = TestCategoryService()
    category_data["updated_by"] = current_user["username"]
    category = service.update(category_id, category_data)
    
    if not category:
        raise HTTPException(status_code=404, detail="Test category not found")
    
    return BaseResponse(success=True, message="Test category updated successfully")

@router.delete("/testcategories/{category_id}", response_model=BaseResponse)
async def delete_test_category(category_id: int, current_user: dict = Depends(get_current_user)):
    service = TestCategoryService()
    success = service.delete(category_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Test category not found")
    
    return BaseResponse(success=True, message="Test category deleted successfully")
