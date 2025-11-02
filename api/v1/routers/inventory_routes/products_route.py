from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import io
import csv

from api.schemas.common import BaseResponse
from api.middleware.auth_middleware import get_current_user
from modules.inventory_module.services.product_service import ProductService
from core.shared.utils.session_manager import session_manager
from core.database.connection import db_manager

router = APIRouter()


@router.get("/products/export-template", response_class=StreamingResponse)
async def export_products_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "code", "category", "unit", "mrp_price", "selling_price", "gst_rate", "tags", "composition", "hsn_id", "schedule", "manufacturer"])
    writer.writerow(["Paracetamol 500mg", "PAR500", "Pharmacy", "Tablet", "30.00", "25.50", "12.0", "#fever #pain", "Paracetamol 500mg", "1", "OTC", "ABC Pharma"])
    writer.writerow(["Vitamin C Tablets", "VITC100", "Nutrition & Supplements", "Tablet", "160.00", "150.00", "18.0", "#vitamin #immunity", "Ascorbic Acid 100mg", "2", "OTC", "XYZ Health"])
    writer.writerow(["Cough Syrup", "COUGH250", "Pharmacy", "Bottle", "90.00", "85.00", "12.0", "#cough #cold", "Dextromethorphan 15mg", "1", "Schedule H", "MediCorp"])
    
    content = output.getvalue()
    return StreamingResponse(
        io.BytesIO(content.encode('utf-8')),
        media_type="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=products_import_template.csv"}
    )


@router.post("/products/import", response_model=BaseResponse)
async def import_products(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))

    from modules.inventory_module.models.entities import Category, Unit

    product_service = ProductService()
    imported_count = 0
    errors = []

    for row_num, row in enumerate(csv_data, start=2):
        try:
            name = str(row.get('name', '')).strip()
            category_name = str(row.get('category', '')).strip()
            unit_name = str(row.get('unit', '')).strip()
            price = row.get('price', '')
            
            if not name or not category_name or not unit_name or not price:
                errors.append(f"Row {row_num}: Missing required fields")
                continue
            
            # Find category and unit by name
            with db_manager.get_session() as session:
                tenant_id = session_manager.get_current_tenant_id()
                category = session.query(Category).filter(
                    Category.name == category_name,
                    Category.tenant_id == tenant_id
                ).first()
                
                if not category:
                    errors.append(f"Row {row_num}: Category '{category_name}' not found")
                    continue
                
                unit = session.query(Unit).filter(
                    Unit.name == unit_name
                ).first()
                
                if not unit:
                    errors.append(f"Row {row_num}: Unit '{unit_name}' not found")
                    continue
                
                product_data = {
                    'name': name,
                    'code': str(row.get('code', '')).strip(),
                    'category_id': category.id,
                    'unit_id': unit.id,
                    'mrp_price': float(row.get('mrp_price', price)),
                    'selling_price': float(row.get('selling_price', price)),
                    'gst_rate': float(row.get('gst_rate', row.get('gst_percentage', 0))),
                    'tags': str(row.get('tags', '')).strip(),
                    'composition': str(row.get('composition', '')).strip(),
                    'hsn_id': int(row.get('hsn_id')) if row.get('hsn_id') and row.get('hsn_id').strip().isdigit() else None,
                    'schedule': str(row.get('schedule', 'OTC')).strip(),
                    'manufacturer': str(row.get('manufacturer', '')).strip()
                }
                
                product_service.create(product_data)
                imported_count += 1
        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")
            continue
    
    message = f"Imported {imported_count} products successfully"
    if errors:
        message += f". {len(errors)} errors occurred"
    
    return BaseResponse(
        success=True,
        message=message
    )
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import io
import csv

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from sqlalchemy import or_
import math
from api.middleware.auth_middleware import get_current_user
from modules.inventory_module.services.product_service import ProductService


router = APIRouter()


# Product endpoints (moved from inventory.py)
@router.get("/products", response_model=PaginatedResponse)
async def get_products(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.inventory_module.models.entities import Product
    from core.shared.utils.session_manager import session_manager

    with db_manager.get_session() as session:
        query = session.query(Product)

        # Apply tenant filter
        tenant_id = session_manager.get_current_tenant_id()
        if tenant_id:
            query = query.filter(Product.tenant_id == tenant_id)

        # Apply search filter
        if pagination.search:
            search_term = f"%{pagination.search}%"
            query = query.filter(or_(
                Product.name.ilike(search_term),
                Product.code.ilike(search_term),
                Product.composition.ilike(search_term),
                Product.tags.ilike(search_term),
                Product.manufacturer.ilike(search_term),
                Product.hsn_code.ilike(search_term)
            ))

        total = query.count()
        products = query.offset(pagination.offset).limit(pagination.per_page).all()

        product_data = [{
            "id": product.id,
            "name": product.name,
            "code": product.code,
            "composition": product.composition,
            "tags": product.tags,
            "hsn_code": getattr(product, 'hsn_code', None),
            "schedule": product.schedule,
            "manufacturer": product.manufacturer,
            "is_discontinued": product.is_discontinued,
            "category_id": product.category_id,
            "unit_id": product.unit_id,
            "mrp_price": float(product.mrp_price) if getattr(product, 'mrp_price', None) is not None else 0,
            "selling_price": float(product.selling_price) if getattr(product, 'selling_price', None) is not None else 0,
            "cost_price": float(product.cost_price) if getattr(product, 'cost_price', None) is not None else 0,
            "is_tax_inclusive": bool(getattr(product, 'is_tax_inclusive', False)),
            "hsn_id": getattr(product, 'hsn_id', None),
            "gst_rate": float(product.gst_rate) if getattr(product, 'gst_rate', None) is not None else 0,
            "igst_rate": float(product.igst_rate) if getattr(product, 'igst_rate', None) is not None else 0,
            "cgst_rate": float(product.cgst_rate) if getattr(product, 'cgst_rate', None) is not None else 0,
            "sgst_rate": float(product.sgst_rate) if getattr(product, 'sgst_rate', None) is not None else 0,
            "commission_type": product.commission_type,
            "commission_value": float(product.commission_value) if product.commission_value else None,
            "description": product.description,
            "is_active": product.is_active
        } for product in products]

    return PaginatedResponse(
        success=True,
        message="Products retrieved successfully",
        data=product_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page) if total > 0 else 0
    )



@router.post("/products", response_model=BaseResponse)
async def create_product(product_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    # Validate commission_type (accept FIXED/PERCENTAGE)
    commission_type = product_data.get('commission_type')
    if commission_type and commission_type.strip().upper() not in ['', 'PERCENTAGE', 'FIXED']:
        raise HTTPException(status_code=400, detail="commission_type must be null/empty, 'PERCENTAGE', or 'FIXED'")

    product_service = ProductService()
    product = product_service.create(product_data)
    product_id = product.id
    return BaseResponse(
        success=True,
        message="Product created successfully",
        data={"id": product_id}
    )



@router.get("/products/get/{product_id}", response_model=BaseResponse)
async def get_product(product_id: int, current_user: dict = Depends(get_current_user)):
    product_service = ProductService()
    product = product_service.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return BaseResponse(
        success=True,
        message="Product retrieved successfully",
        data={
            "id": product.id,
            "name": product.name,
            "code": product.code,
            "composition": product.composition,
            "tags": product.tags,
            "schedule": product.schedule,
            "manufacturer": product.manufacturer,
            "is_discontinued": product.is_discontinued,
            "category_id": product.category_id,
            "unit_id": product.unit_id,
            "mrp_price": float(product.mrp_price) if getattr(product, 'mrp_price', None) is not None else 0,
            "selling_price": float(product.selling_price) if getattr(product, 'selling_price', None) is not None else 0,
            "cost_price": float(product.cost_price) if getattr(product, 'cost_price', None) is not None else 0,
            "is_tax_inclusive": bool(getattr(product, 'is_tax_inclusive', False)),
            "hsn_id": getattr(product, 'hsn_id', None),
            "gst_rate": float(product.gst_rate) if getattr(product, 'gst_rate', None) is not None else 0,
            "igst_rate": float(product.igst_rate) if getattr(product, 'igst_rate', None) is not None else 0,
            "cgst_rate": float(product.cgst_rate) if getattr(product, 'cgst_rate', None) is not None else 0,
            "sgst_rate": float(product.sgst_rate) if getattr(product, 'sgst_rate', None) is not None else 0,
            "commission_type": product.commission_type,
            "commission_value": float(product.commission_value) if product.commission_value else None,
            "description": product.description,
            "is_active": product.is_active
        }
    )



@router.put("/products/update/{product_id}", response_model=BaseResponse)
async def update_product(product_id: int, product_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    # Validate commission_type
    commission_type = product_data.get('commission_type')
    if commission_type and commission_type not in ['', 'Percentage', 'Fixed']:
        raise HTTPException(status_code=400, detail="commission_type must be null/empty, 'Percentage', or 'Fixed'")

    # Convert empty strings to None for numeric fields
    if 'commission_value' in product_data and product_data['commission_value'] == '':
        product_data['commission_value'] = None

    product_service = ProductService()
    product = product_service.update(product_id, product_data)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return BaseResponse(success=True, message="Product updated successfully")



@router.delete("/products/delete/{product_id}", response_model=BaseResponse)
async def delete_product(product_id: int, current_user: dict = Depends(get_current_user)):
    product_service = ProductService()
    success = product_service.delete(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")

    return BaseResponse(success=True, message="Product deleted successfully")



@router.get("/products/export-template", response_class=StreamingResponse)
async def export_products_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "code", "category", "unit", "mrp_price", "selling_price", "gst_rate", "tags", "composition", "hsn_id", "schedule", "manufacturer"])
    writer.writerow(["Paracetamol 500mg", "PAR500", "Pharmacy", "Tablet", "30.00", "25.50", "12.0", "#fever #pain", "Paracetamol 500mg", "1", "OTC", "ABC Pharma"])
    writer.writerow(["Vitamin C Tablets", "VITC100", "Nutrition & Supplements", "Tablet", "160.00", "150.00", "18.0", "#vitamin #immunity", "Ascorbic Acid 100mg", "2", "OTC", "XYZ Health"])
    writer.writerow(["Cough Syrup", "COUGH250", "Pharmacy", "Bottle", "90.00", "85.00", "12.0", "#cough #cold", "Dextromethorphan 15mg", "1", "Schedule H", "MediCorp"])

    content = output.getvalue()
    return StreamingResponse(
        io.BytesIO(content.encode('utf-8')),
        media_type="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=products_import_template.csv"}
    )



@router.post("/products/import", response_model=BaseResponse)
async def import_products(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))

    from core.database.connection import db_manager
    from modules.inventory_module.models.entities import Category, Unit
    from core.shared.utils.session_manager import session_manager

    product_service = ProductService()
    imported_count = 0
    errors = []

    for row_num, row in enumerate(csv_data, start=2):
        try:
            name = str(row.get('name', '')).strip()
            category_name = str(row.get('category', '')).strip()
            unit_name = str(row.get('unit', '')).strip()
            price = row.get('price', '')

            if not name or not category_name or not unit_name or not price:
                errors.append(f"Row {row_num}: Missing required fields")
                continue

            # Find category and unit by name
            with db_manager.get_session() as session:
                tenant_id = session_manager.get_current_tenant_id()
                category = session.query(Category).filter(
                    Category.name == category_name,
                    Category.tenant_id == tenant_id
                ).first()

                if not category:
                    errors.append(f"Row {row_num}: Category '{category_name}' not found")
                    continue

                unit = session.query(Unit).filter(
                    Unit.name == unit_name
                ).first()

                if not unit:
                    errors.append(f"Row {row_num}: Unit '{unit_name}' not found")
                    continue

                product_data = {
                    'name': name,
                    'code': str(row.get('code', '')).strip(),
                    'category_id': category.id,
                    'unit_id': unit.id,
                    'mrp_price': float(row.get('mrp_price', price)),
                    'selling_price': float(row.get('selling_price', price)),
                    'gst_rate': float(row.get('gst_rate', row.get('gst_percentage', 0))),
                    'tags': str(row.get('tags', '')).strip(),
                    'composition': str(row.get('composition', '')).strip(),
                    'hsn_id': int(row.get('hsn_id')) if row.get('hsn_id') and row.get('hsn_id').strip().isdigit() else None,
                    'schedule': str(row.get('schedule', 'OTC')).strip(),
                    'manufacturer': str(row.get('manufacturer', '')).strip()
                }

                product_service.create(product_data)
                imported_count += 1
        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")
            continue

    message = f"Imported {imported_count} products successfully"
    if errors:
        message += f". {len(errors)} errors occurred"

    return BaseResponse(
        success=True,
        message=message
    )
