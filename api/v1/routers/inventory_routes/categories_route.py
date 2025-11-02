from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import io
import csv
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from sqlalchemy import or_
from api.middleware.auth_middleware import get_current_user
from modules.inventory_module.services.category_service import CategoryService

router = APIRouter()


@router.get("/categories", response_model=PaginatedResponse)
async def get_categories(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.inventory_module.models.entities import Category
    from core.shared.utils.session_manager import session_manager

    with db_manager.get_session() as session:
        query = session.query(Category)

        # Apply tenant filter
        tenant_id = session_manager.get_current_tenant_id()
        if tenant_id:
            query = query.filter(Category.tenant_id == tenant_id)

        if pagination.search:
            search_term = f"%{pagination.search}%"
            query = query.filter(or_(
                Category.name.ilike(search_term),
                Category.description.ilike(search_term)
            ))

        total = query.count()
        categories = query.offset(pagination.offset).limit(pagination.per_page).all()

        category_data = []
        for category in categories:
            parent_name = None
            if category.parent_id:
                parent = session.query(Category).filter(Category.id == category.parent_id).first()
                if parent:
                    parent_name = parent.name

            category_data.append({
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "parent_id": category.parent_id,
                "parent_name": parent_name,
                "is_active": category.is_active
            })

    return PaginatedResponse(
        success=True,
        message="Categories retrieved successfully",
        data=category_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page) if total > 0 else 0
    )


@router.post("/categories", response_model=BaseResponse)
async def create_category(category_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    category_service = CategoryService()
    category = category_service.create(category_data)
    category_id = category.id  # Access id while session is still active
    return BaseResponse(
        success=True,
        message="Category created successfully",
        data={"id": category_id}
    )


@router.put("/categories/{category_id}", response_model=BaseResponse)
async def update_category(category_id: int, category_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    category_service = CategoryService()
    category = category_service.update(category_id, category_data)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    return BaseResponse(success=True, message="Category updated successfully")


@router.delete("/categories/{category_id}", response_model=BaseResponse)
async def delete_category(category_id: int, current_user: dict = Depends(get_current_user)):
    category_service = CategoryService()
    success = category_service.delete(category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")

    return BaseResponse(success=True, message="Category deleted successfully")


@router.get("/categories/export-template")
async def export_categories_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "parent_id", "description", "is_active"])
    writer.writerow(["Electronics", "", "Electronic products", "true"])
    writer.writerow(["Mobile Phones", "1", "Mobile phone category", "true"])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=categories_template.csv"}
    )


@router.post("/categories/import", response_model=BaseResponse)
async def import_categories(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))

    from core.database.connection import db_manager
    from modules.inventory_module.models.entities import Category

    imported_count = 0
    error_count = 0
    errors = []
    batch_size = 100
    categories_batch = []

    with db_manager.get_session() as session:
        for row_num, row in enumerate(csv_data, start=2):
            try:
                # Skip header rows
                name_value = row.get("name", "").strip()
                if not name_value or name_value.lower() in ["name", "category name", "category"]:
                    continue

                # Validate required fields
                if not row.get("is_active"):
                    errors.append(f"Row {row_num}: Missing is_active field")
                    error_count += 1
                    continue

                parent_id = None
                if row.get("parent_id") and row["parent_id"].strip():
                    try:
                        parent_id = int(row["parent_id"])
                    except ValueError:
                        errors.append(f"Row {row_num}: Invalid parent_id value")
                        error_count += 1
                        continue

                category = Category(
                    name=name_value,
                    parent_id=parent_id,
                    description=row.get("description", "").strip(),
                    tenant_id=current_user["tenant_id"],
                    is_active=row["is_active"].lower() == "true",
                    created_by=current_user["username"]
                )
                categories_batch.append(category)

                # Process batch
                if len(categories_batch) >= batch_size:
                    session.add_all(categories_batch)
                    session.flush()
                    imported_count += len(categories_batch)
                    categories_batch = []

            except Exception as e:
                error_count += 1
                errors.append(f"Row {row_num}: {str(e)}")

        # Process remaining batch
        if categories_batch:
            session.add_all(categories_batch)
            session.flush()
            imported_count += len(categories_batch)

        session.commit()

    message = f"Import completed: {imported_count} categories imported"
    if error_count > 0:
        message += f", {error_count} errors"
        if errors:
            message += f". First few errors: {'; '.join(errors[:3])}"

    return BaseResponse(
        success=True,
        message=message
    )
