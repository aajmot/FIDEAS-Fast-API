from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import io
import csv
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from sqlalchemy import or_
from api.middleware.auth_middleware import get_current_user
from modules.inventory_module.services.customer_service import CustomerService

router = APIRouter()


@router.get("/customers", response_model=PaginatedResponse)
async def get_customers(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.inventory_module.models.entities import Customer

    with db_manager.get_session() as session:
        query = session.query(Customer).filter(
            Customer.tenant_id == current_user['tenant_id']
        )

        if pagination.search:
            query = query.filter(or_(
                Customer.name.ilike(f"%{pagination.search}%"),
                Customer.email.ilike(f"%{pagination.search}%"),
                Customer.phone.ilike(f"%{pagination.search}%")
            ))

        total = query.count()
        customers = query.offset(pagination.offset).limit(pagination.per_page).all()

        customer_data = [{
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "age": customer.age,
            "address": customer.address,
            "tax_id": customer.tax_id,
            "is_active": customer.is_active
        } for customer in customers]

    return PaginatedResponse(
        success=True,
        message="Customers retrieved successfully",
        data=customer_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )


@router.post("/customers", response_model=BaseResponse)
async def create_customer(customer_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    customer_service = CustomerService()
    customer = customer_service.create(customer_data)
    return BaseResponse(
        success=True,
        message="Customer created successfully",
        data={"id": customer}
    )


@router.put("/customers/{customer_id}", response_model=BaseResponse)
async def update_customer(customer_id: int, customer_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    customer_service = CustomerService()
    customer = customer_service.update(customer_id, customer_data)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return BaseResponse(success=True, message="Customer updated successfully")


@router.delete("/customers/{customer_id}", response_model=BaseResponse)
async def delete_customer(customer_id: int, current_user: dict = Depends(get_current_user)):
    customer_service = CustomerService()
    success = customer_service.delete(customer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Customer not found")

    return BaseResponse(success=True, message="Customer deleted successfully")


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


@router.post("/customers/import", response_model=BaseResponse)
async def import_customers(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))

    customer_service = CustomerService()
    imported_count = 0

    for row in csv_data:
        try:
            customer_data = {
                "name": row["name"],
                "phone": row["phone"],
                "email": row.get("email", ""),
                "address": row.get("address", ""),
                "tax_id": row.get("tax_id", ""),
                "is_active": row["is_active"].lower() == "true"
            }

            # Add age if present
            if "age" in row and row["age"].strip():
                customer_data["age"] = int(row["age"])

            customer_service.create(customer_data)
            imported_count += 1
        except Exception:
            continue

    return BaseResponse(
        success=True,
        message=f"Imported {imported_count} customers successfully"
    )
