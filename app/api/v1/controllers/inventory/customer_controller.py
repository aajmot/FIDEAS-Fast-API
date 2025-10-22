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
from app.modules.inventory.services.customer_service import CustomerService

router = APIRouter()

@router.get("/customers")
async def get_customers(
    pagination: PaginationParams = Depends(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer_service = CustomerService(db)
    customers, total = customer_service.get_customers_paginated(
        current_user["tenant_id"],
        pagination.search,
        pagination.offset,
        pagination.size
    )
    
    return PaginatedResponse.create(
        items=customers,
        total=total,
        page=pagination.page,
        size=pagination.size
    )

@router.post("/customers")
async def create_customer(
    customer_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer_service = CustomerService(db)
    customer_data["tenant_id"] = current_user["tenant_id"]
    customer_data["created_by"] = current_user["username"]
    customer = customer_service.create(customer_data)
    
    return APIResponse.created({"id": customer.id})

@router.put("/customers/{customer_id}")
async def update_customer(
    customer_id: int,
    customer_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer_service = CustomerService(db)
    customer_data["updated_by"] = current_user["username"]
    customer = customer_service.update(customer_id, customer_data)
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return APIResponse.success(message="Customer updated successfully")

@router.delete("/customers/{customer_id}")
async def delete_customer(
    customer_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer_service = CustomerService(db)
    success = customer_service.delete(customer_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return APIResponse.success(message="Customer deleted successfully")

@router.get("/customers/export-template")
async def export_customers_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "phone", "email", "age", "address", "tax_id", "is_active"])
    writer.writerow(["John Customer", "123-456-7890", "john@customer.com", "30", "123 Main St", "TAX001", "true"])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=customers_template.csv"}
    )

@router.post("/customers/import")
async def import_customers(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    customer_service = CustomerService(db)
    customers_data = list(csv_data)
    imported_count = customer_service.import_customers(
        customers_data,
        current_user["tenant_id"],
        current_user["username"]
    )
    
    return APIResponse.success(message=f"Imported {imported_count} customers successfully")