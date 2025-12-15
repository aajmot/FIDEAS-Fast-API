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

        # Order by id desc so most recent products appear first
        query = query.order_by(Product.id.desc())

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
            "hsn_code": getattr(product, 'hsn_code', None),
            "gst_rate": float(product.gst_rate) if getattr(product, 'gst_rate', None) is not None else 0,
            "igst_rate": float(product.igst_rate) if getattr(product, 'igst_rate', None) is not None else 0,
            "cgst_rate": float(product.cgst_rate) if getattr(product, 'cgst_rate', None) is not None else 0,
            "sgst_rate": float(product.sgst_rate) if getattr(product, 'sgst_rate', None) is not None else 0,
            "cess_rate": float(product.cess_rate) if getattr(product, 'cess_rate', None) is not None else 0,
            "commission_type": product.commission_type,
            "commission_value": float(product.commission_value) if product.commission_value else None,
            "description": product.description,
            "is_active": product.is_active,
            # Inventory stock level fields
            "is_inventory_item": bool(getattr(product, 'is_inventory_item', True)),
            "reorder_level": float(product.reorder_level) if getattr(product, 'reorder_level', None) is not None else 0,
            "danger_level": float(product.danger_level) if getattr(product, 'danger_level', None) is not None else 0,
            "min_stock": float(product.min_stock) if getattr(product, 'min_stock', None) is not None else 0,
            "max_stock": float(product.max_stock) if getattr(product, 'max_stock', None) is not None else 0,
            # Additional tracking fields
            "barcode": getattr(product, 'barcode', None),
            "is_serialized": bool(getattr(product, 'is_serialized', False)),
            "warranty_months": getattr(product, 'warranty_months', None)
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
    from core.database.connection import db_manager
    from modules.inventory_module.models.entities import Product
    from core.shared.utils.session_manager import session_manager
    
    with db_manager.get_session() as session:
        tenant_id = current_user['tenant_id']
        product = session.query(Product).filter(
            Product.id == product_id,
            Product.tenant_id == tenant_id
        ).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Access all attributes within the session to avoid DetachedInstanceError
        product_data = {
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
            "cess_rate": float(product.cess_rate) if getattr(product, 'cess_rate', None) is not None else 0,
            "commission_type": product.commission_type,
            "commission_value": float(product.commission_value) if product.commission_value else None,
            "description": product.description,
            "is_active": product.is_active,
            # Inventory stock level fields
            "is_inventory_item": bool(getattr(product, 'is_inventory_item', True)),
            "reorder_level": float(product.reorder_level) if getattr(product, 'reorder_level', None) is not None else 0,
            "danger_level": float(product.danger_level) if getattr(product, 'danger_level', None) is not None else 0,
            "min_stock": float(product.min_stock) if getattr(product, 'min_stock', None) is not None else 0,
            "max_stock": float(product.max_stock) if getattr(product, 'max_stock', None) is not None else 0,
            # Additional tracking fields
            "barcode": getattr(product, 'barcode', None),
            "is_serialized": bool(getattr(product, 'is_serialized', False)),
            "warranty_months": getattr(product, 'warranty_months', None)
        }
    
    return BaseResponse(
        success=True,
        message="Product retrieved successfully",
        data=product_data
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
    writer.writerow(["name", "code", "category", "unit", "mrp_price", "selling_price", "gst_rate", "cess_rate", "reorder_level", "danger_level", "min_stock", "max_stock", "tags", "composition", "hsn_code", "hsn_id", "schedule", "manufacturer"])
    writer.writerow(["Paracetamol 500mg", "PAR500", "Pharmacy", "Tablet", "30.00", "25.50", "12.0", "0.0", "10", "5", "0", "100", "#fever #pain", "Paracetamol 500mg", "H1234", "1", "OTC", "ABC Pharma"])
    writer.writerow(["Vitamin C Tablets", "VITC100", "Nutrition & Supplements", "Tablet", "160.00", "150.00", "18.0", "0.0", "20", "10", "0", "200", "#vitamin #immunity", "Ascorbic Acid 100mg", "H2345", "2", "OTC", "XYZ Health"])
    writer.writerow(["Cough Syrup", "COUGH250", "Pharmacy", "Bottle", "90.00", "85.00", "12.0", "0.0", "15", "7", "0", "150", "#cough #cold", "Dextromethorphan 15mg", "H3456", "1", "Schedule H", "MediCorp"])

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

    from core.shared.utils.session_manager import session_manager
    from modules.inventory_module.services.category_service import CategoryService
    from modules.inventory_module.services.unit_service import UnitService

    product_service = ProductService()
    category_service = CategoryService()
    unit_service = UnitService()
    from core.shared.utils.logger import logger

    imported_count = 0
    errors = []

    for row_num, row in enumerate(csv_data, start=2):
        try:
            name = str(row.get('name', '')).strip()
            category_name = str(row.get('category', '')).strip()
            unit_name = str(row.get('unit', '')).strip()
            price = row.get('mrp_price', '') or row.get('price', '')

            if not name or not category_name or not unit_name or not price:
                errors.append(f"Row {row_num}: Missing required fields")
                continue

            # Lookup/create category and unit inside a session to avoid detached-instance issues
            from core.database.connection import db_manager
            from modules.inventory_module.models.entities import Category, Unit
            with db_manager.get_session() as session:
                tenant_id = session_manager.get_current_tenant_id()

                category = session.query(Category).filter(
                    Category.name.ilike(category_name),
                    Category.tenant_id == tenant_id
                ).first()
                if not category:
                    category = Category(name=category_name, tenant_id=tenant_id)
                    session.add(category)
                    session.flush()
                    session.refresh(category)

                unit = session.query(Unit).filter(Unit.name.ilike(unit_name)).first()
                if not unit:
                    unit = Unit(name=unit_name, tenant_id=current_user['tenant_id'])
                    session.add(unit)
                    session.flush()
                    session.refresh(unit)

                category_id = category.id
                unit_id = unit.id

            product_data = {
                'name': name,
                'code': str(row.get('code', '')).strip(),
                'category_id': category_id,
                'unit_id': unit_id,
                'mrp_price': float(row.get('mrp_price', price)),
                'selling_price': float(row.get('selling_price', price)),
                'gst_rate': float(row.get('gst_rate', row.get('gst_percentage', 0))) if row.get('gst_rate') not in (None, '') else float(row.get('gst_percentage', 0)),
                'cess_rate': float(row.get('cess_rate', 0)) if row.get('cess_rate') not in (None, '') else 0,
                'reorder_level': float(row.get('reorder_level', 0)) if row.get('reorder_level') not in (None, '') else 0,
                'danger_level': float(row.get('danger_level', 0)) if row.get('danger_level') not in (None, '') else 0,
                'min_stock': float(row.get('min_stock', 0)) if row.get('min_stock') not in (None, '') else 0,
                'max_stock': float(row.get('max_stock', 0)) if row.get('max_stock') not in (None, '') else 0,
                'tags': str(row.get('tags', '')).strip(),
                'composition': str(row.get('composition', '')).strip(),
                # If hsn_code is provided, let service handle lookup/creation; otherwise use hsn_id if provided
                'hsn_code': str(row.get('hsn_code', '')).strip() if row.get('hsn_code') else None,
                'hsn_id': int(row.get('hsn_id')) if row.get('hsn_id') and str(row.get('hsn_id')).strip().isdigit() and not row.get('hsn_code') else None,
                'schedule': str(row.get('schedule', 'OTC')).strip()[:10],  # Truncate to 10 chars max
                'manufacturer': str(row.get('manufacturer', '')).strip(),
                'tenant_id': tenant_id
            }

            product_service.create(product_data)
            imported_count += 1
        except Exception as e:
            err_msg = f"Row {row_num}: {str(e)}"
            # Log error with row context for easier debugging
            try:
                logger.error(err_msg, "ProductsImport", exc_info=True)
            except Exception:
                pass
            errors.append(err_msg)
            continue

    message = f"Imported {imported_count} products successfully"
    if errors:
        message += f". {len(errors)} errors occurred"

    return BaseResponse(
        success=True,
        message=message,
        data={
            'imported_count': imported_count,
            'errors': errors[:200]  # include first 200 errors to avoid huge responses
        }
    )
