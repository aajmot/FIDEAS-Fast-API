from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import io
import csv
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from sqlalchemy import or_
from api.middleware.auth_middleware import get_current_user
from modules.inventory_module.services.supplier_service import SupplierService

router = APIRouter()


@router.get("/suppliers", response_model=PaginatedResponse)
async def get_suppliers(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.inventory_module.models.entities import Supplier

    with db_manager.get_session() as session:
        query = session.query(Supplier).filter(
            Supplier.tenant_id == current_user['tenant_id']
        )

        if pagination.search:
            query = query.filter(or_(
                Supplier.name.ilike(f"%{pagination.search}%"),
                Supplier.email.ilike(f"%{pagination.search}%"),
                Supplier.phone.ilike(f"%{pagination.search}%")
            ))

        total = query.count()
        suppliers = query.offset(pagination.offset).limit(pagination.per_page).all()

        supplier_data = [{
            "id": supplier.id,
            "name": supplier.name,
            "phone": supplier.phone,
            "email": supplier.email,
            "tax_id": supplier.tax_id,
            "contact_person": supplier.contact_person,
            "address": supplier.address,
            "is_active": supplier.is_active
        } for supplier in suppliers]

    return PaginatedResponse(
        success=True,
        message="Suppliers retrieved successfully",
        data=supplier_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )


@router.post("/suppliers", response_model=BaseResponse)
async def create_supplier(supplier_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    supplier_service = SupplierService()
    supplier = supplier_service.create(supplier_data)
    return BaseResponse(
        success=True,
        message="Supplier created successfully",
        data={"id": supplier}
    )


@router.put("/suppliers/{supplier_id}", response_model=BaseResponse)
async def update_supplier(supplier_id: int, supplier_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    supplier_service = SupplierService()
    supplier = supplier_service.update(supplier_id, supplier_data)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    return BaseResponse(success=True, message="Supplier updated successfully")


@router.delete("/suppliers/{supplier_id}", response_model=BaseResponse)
async def delete_supplier(supplier_id: int, current_user: dict = Depends(get_current_user)):
    supplier_service = SupplierService()
    success = supplier_service.delete(supplier_id)
    if not success:
        raise HTTPException(status_code=404, detail="Supplier not found")

    return BaseResponse(success=True, message="Supplier deleted successfully")


@router.get("/suppliers/export-template")
async def export_suppliers_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "phone", "email", "tax_id", "contact_person", "address", "is_active"])
    writer.writerow(["ABC Supplier", "123-456-7890", "abc@supplier.com", "TAX001", "John Doe", "456 Supply St", "true"])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=suppliers_template.csv"}
    )


@router.post("/suppliers/import", response_model=BaseResponse)
async def import_suppliers(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))

    supplier_service = SupplierService()
    imported_count = 0

    for row in csv_data:
        try:
            supplier_data = {
                "name": row["name"],
                "phone": row["phone"],
                "email": row.get("email", ""),
                "tax_id": row.get("tax_id", ""),
                "contact_person": row.get("contact_person", ""),
                "address": row.get("address", ""),
                "is_active": row["is_active"].lower() == "true"
            }

            supplier_service.create(supplier_data)
            imported_count += 1
        except Exception:
            continue

    return BaseResponse(
        success=True,
        message=f"Imported {imported_count} suppliers successfully"
    )
