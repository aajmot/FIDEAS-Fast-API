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
from app.modules.inventory.services.supplier_service import SupplierService

router = APIRouter()

@router.get("/suppliers")
async def get_suppliers(
    pagination: PaginationParams = Depends(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    supplier_service = SupplierService(db)
    suppliers, total = supplier_service.get_suppliers_paginated(
        current_user["tenant_id"],
        pagination.search,
        pagination.offset,
        pagination.size
    )
    
    return PaginatedResponse.create(
        items=suppliers,
        total=total,
        page=pagination.page,
        size=pagination.size
    )

@router.post("/suppliers")
async def create_supplier(
    supplier_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    supplier_service = SupplierService(db)
    supplier_data["tenant_id"] = current_user["tenant_id"]
    supplier_data["created_by"] = current_user["username"]
    supplier = supplier_service.create(supplier_data)
    
    return APIResponse.created({"id": supplier.id})

@router.put("/suppliers/{supplier_id}")
async def update_supplier(
    supplier_id: int,
    supplier_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    supplier_service = SupplierService(db)
    supplier_data["updated_by"] = current_user["username"]
    supplier = supplier_service.update(supplier_id, supplier_data)
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    return APIResponse.success(message="Supplier updated successfully")

@router.delete("/suppliers/{supplier_id}")
async def delete_supplier(
    supplier_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    supplier_service = SupplierService(db)
    success = supplier_service.delete(supplier_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    return APIResponse.success(message="Supplier deleted successfully")

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

@router.post("/suppliers/import")
async def import_suppliers(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    supplier_service = SupplierService(db)
    suppliers_data = list(csv_data)
    imported_count = supplier_service.import_suppliers(
        suppliers_data,
        current_user["tenant_id"],
        current_user["username"]
    )
    
    return APIResponse.success(message=f"Imported {imported_count} suppliers successfully")