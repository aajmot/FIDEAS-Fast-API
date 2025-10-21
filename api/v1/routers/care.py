from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Dict, Any
from sqlalchemy import or_
import math
import io
import csv

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user
from modules.care_module.services.test_category_service import TestCategoryService
from modules.care_module.services.test_service import TestService

router = APIRouter()

@router.get("/testcategories", response_model=PaginatedResponse)
async def get_test_categories(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.care_module.models.entities import TestCategory
    
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

# Test endpoints
@router.get("/tests", response_model=PaginatedResponse)
async def get_tests(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.care_module.models.entities import Test, TestCategory
    
    with db_manager.get_session() as session:
        query = session.query(Test).filter(
            Test.tenant_id == current_user["tenant_id"],
            Test.is_deleted == False
        )
        
        if pagination.search:
            query = query.filter(or_(
                Test.name.ilike(f"%{pagination.search}%"),
                Test.body_part.ilike(f"%{pagination.search}%"),
                Test.description.ilike(f"%{pagination.search}%")
            ))
        
        total = query.count()
        tests = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        test_data = []
        for test in tests:
            category = session.query(TestCategory).filter(TestCategory.id == test.category_id).first() if test.category_id else None
            test_data.append({
                "id": test.id,
                "name": test.name,
                "category_id": test.category_id,
                "category_name": category.name if category else None,
                "body_part": test.body_part,
                "description": test.description,
                "typical_duration": test.typical_duration,
                "preparation_instruction": test.preparation_instruction,
                "rate": float(test.rate) if test.rate else None,
                "hsn_code": test.hsn_code,
                "gst": float(test.gst) if test.gst else None,
                "cess": float(test.cess) if test.cess else None,
                "commission_type": test.commission_type,
                "commission_value": float(test.commission_value) if test.commission_value else None,
                "is_active": test.is_active,
                "created_at": test.created_at.isoformat() if test.created_at else None,
                "created_by": test.created_by,
                "updated_at": test.updated_at.isoformat() if test.updated_at else None,
                "updated_by": test.updated_by
            })
    
    return PaginatedResponse(
        success=True,
        message="Tests retrieved successfully",
        data=test_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/tests", response_model=BaseResponse)
async def create_test(test_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    # Validate commission_type
    commission_type = test_data.get('commission_type')
    if commission_type and commission_type not in ['', 'Percentage', 'Fixed']:
        raise HTTPException(status_code=400, detail="commission_type must be null/empty, 'Percentage', or 'Fixed'")
    
    service = TestService()
    test_data["tenant_id"] = current_user["tenant_id"]
    test_data["created_by"] = current_user["username"]
    test = service.create(test_data)
    
    return BaseResponse(
        success=True,
        message="Test created successfully",
        data={"id": test.id}
    )

@router.get("/tests/export-template")
async def export_tests_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "category_name", "body_part", "description", "typical_duration", "preparation_instruction", "rate", "hsn_code", "gst", "cess", "commission_type", "commission_value", "is_active", "parameter_names", "parameter_units", "parameter_ranges"])
    writer.writerow(["Complete Blood Count", "Blood Tests", "Blood", "CBC test", "2 hours", "Fasting required", "500.00", "9018", "5.00", "0.00", "Percentage", "10.00", "true", "Hemoglobin#WBC Count", "g/dL#cells/mcL", "12-16#4000-11000"])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=tests_template.csv"}
    )

@router.post("/tests/import", response_model=BaseResponse)
async def import_tests(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.care_module.models.entities import TestCategory
    
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    service = TestService()
    imported_count = 0
    
    with db_manager.get_session() as session:
        for row in csv_data:
            try:
                category_id = None
                if row.get("category_name"):
                    category = session.query(TestCategory).filter(
                        TestCategory.name == row["category_name"],
                        TestCategory.tenant_id == current_user["tenant_id"]
                    ).first()
                    category_id = category.id if category else None
                
                # Parse parameters
                parameters = []
                param_names = row.get("parameter_names", "").split("#") if row.get("parameter_names") else []
                param_units = row.get("parameter_units", "").split("#") if row.get("parameter_units") else []
                param_ranges = row.get("parameter_ranges", "").split("#") if row.get("parameter_ranges") else []
                
                for i, name in enumerate(param_names):
                    if name.strip():
                        parameters.append({
                            "name": name.strip(),
                            "unit": param_units[i].strip() if i < len(param_units) else "",
                            "normal_range": param_ranges[i].strip() if i < len(param_ranges) else "",
                            "is_active": True,
                            "created_by": current_user["username"]
                        })
                
                service.create({
                    "name": row["name"],
                    "category_id": category_id,
                    "body_part": row.get("body_part", ""),
                    "description": row.get("description", ""),
                    "typical_duration": row.get("typical_duration", ""),
                    "preparation_instruction": row.get("preparation_instruction", ""),
                    "rate": float(row["rate"]) if row.get("rate") else None,
                    "hsn_code": row.get("hsn_code", ""),
                    "gst": float(row["gst"]) if row.get("gst") else None,
                    "cess": float(row["cess"]) if row.get("cess") else None,
                    "commission_type": row.get("commission_type", "") if row.get("commission_type") else None,
                    "commission_value": float(row["commission_value"]) if row.get("commission_value") else None,
                    "is_active": row.get("is_active", "true").lower() == "true",
                    "tenant_id": current_user["tenant_id"],
                    "created_by": current_user["username"],
                    "parameters": parameters
                })
                imported_count += 1
            except Exception:
                continue
    
    return BaseResponse(
        success=True,
        message=f"Imported {imported_count} tests successfully"
    )

@router.get("/tests/{test_id}", response_model=BaseResponse)
async def get_test(test_id: int, current_user: dict = Depends(get_current_user)):
    service = TestService()
    test = service.get_by_id(test_id, current_user["tenant_id"])
    
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    parameters = service.get_parameters(test_id, current_user["tenant_id"])
    
    return BaseResponse(
        success=True,
        message="Test retrieved successfully",
        data={
            "id": test.id,
            "name": test.name,
            "category_id": test.category_id,
            "body_part": test.body_part,
            "description": test.description,
            "typical_duration": test.typical_duration,
            "preparation_instruction": test.preparation_instruction,
            "rate": float(test.rate) if test.rate else None,
            "hsn_code": test.hsn_code,
            "gst": float(test.gst) if test.gst else None,
            "cess": float(test.cess) if test.cess else None,
            "commission_type": test.commission_type,
            "commission_value": float(test.commission_value) if test.commission_value else None,
            "is_active": test.is_active,
            "created_at": test.created_at.isoformat() if test.created_at else None,
            "created_by": test.created_by,
            "updated_at": test.updated_at.isoformat() if test.updated_at else None,
            "updated_by": test.updated_by,
            "parameters": [{
                "id": p.id,
                "name": p.name,
                "unit": p.unit,
                "normal_range": p.normal_range,
                "is_active": p.is_active
            } for p in parameters]
        }
    )

@router.put("/tests/{test_id}", response_model=BaseResponse)
async def update_test(test_id: int, test_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    # Validate commission_type
    commission_type = test_data.get('commission_type')
    if commission_type and commission_type not in ['', 'Percentage', 'Fixed']:
        raise HTTPException(status_code=400, detail="commission_type must be null/empty, 'Percentage', or 'Fixed'")
    
    service = TestService()
    test_data["updated_by"] = current_user["username"]
    
    # Convert empty strings to None for numeric and integer fields
    for field in ['rate', 'gst', 'cess', 'commission_value']:
        if field in test_data and test_data[field] == '':
            test_data[field] = None
    
    if 'category_id' in test_data and test_data['category_id'] == '':
        test_data['category_id'] = None
    
    test = service.update(test_id, test_data)
    
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    return BaseResponse(success=True, message="Test updated successfully")

@router.delete("/tests/{test_id}", response_model=BaseResponse)
async def delete_test(test_id: int, current_user: dict = Depends(get_current_user)):
    service = TestService()
    success = service.delete(test_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Test not found")
    
    return BaseResponse(success=True, message="Test deleted successfully")

@router.get("/tests/{test_id}/parameters", response_model=BaseResponse)
async def get_test_parameters(test_id: int, current_user: dict = Depends(get_current_user)):
    service = TestService()
    parameters = service.get_parameters(test_id, current_user["tenant_id"])
    
    return BaseResponse(
        success=True,
        message="Test parameters retrieved successfully",
        data=[{
            "id": p.id,
            "name": p.name,
            "unit": p.unit,
            "normal_range": p.normal_range,
            "is_active": p.is_active,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "created_by": p.created_by,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            "updated_by": p.updated_by
        } for p in parameters]
    )
