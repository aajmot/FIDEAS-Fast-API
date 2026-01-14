from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from typing import Dict, Any, Optional, List
from api.schemas.common import BaseResponse, PaginatedResponse
from api.schemas.account_schema.cost_center_schemas import (
    CostCenterCreate, CostCenterUpdate, CostCenterResponse, 
    CostCenterListResponse, CostCenterImportRow
)
from api.middleware.auth_middleware import get_current_user
from modules.account_module.services.cost_center_service import CostCenterService
import io, csv

router = APIRouter()
cost_center_service = CostCenterService()


@router.get("/cost-centers", response_model=PaginatedResponse)
async def get_cost_centers(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get paginated list of cost centers with filtering"""
    try:
        result = cost_center_service.get_all(
            tenant_id=current_user['tenant_id'],
            page=page,
            per_page=per_page,
            search=search,
            is_active=is_active
        )
        
        return PaginatedResponse(
            success=True,
            message="Cost centers retrieved successfully",
            data=result["items"],
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"],
            total_pages=result["total_pages"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cost-centers/{cost_center_id}", response_model=BaseResponse)
async def get_cost_center(
    cost_center_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get cost center by ID"""
    try:
        cost_center = cost_center_service.get_by_id(
            cost_center_id=cost_center_id,
            tenant_id=current_user['tenant_id']
        )
        
        if not cost_center:
            raise HTTPException(status_code=404, detail="Cost center not found")
        
        return BaseResponse(
            success=True,
            message="Cost center retrieved successfully",
            data=cost_center
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cost-centers", response_model=BaseResponse)
async def create_cost_center(
    cost_center_data: CostCenterCreate, 
    current_user: dict = Depends(get_current_user)
):
    """Create new cost center"""
    try:
        cost_center = cost_center_service.create(
            cost_center_data=cost_center_data,
            tenant_id=current_user['tenant_id'],
            created_by=current_user.get('user_id')
        )
        
        return BaseResponse(
            success=True,
            message="Cost center created successfully",
            data=cost_center
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/cost-centers/{cost_center_id}", response_model=BaseResponse)
async def update_cost_center(
    cost_center_id: int, 
    cost_center_data: CostCenterUpdate, 
    current_user: dict = Depends(get_current_user)
):
    """Update cost center"""
    try:
        cost_center = cost_center_service.update(
            cost_center_id=cost_center_id,
            cost_center_data=cost_center_data,
            tenant_id=current_user['tenant_id']
        )
        
        if not cost_center:
            raise HTTPException(status_code=404, detail="Cost center not found")
        
        return BaseResponse(
            success=True,
            message="Cost center updated successfully",
            data=cost_center
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cost-centers/{cost_center_id}", response_model=BaseResponse)
async def delete_cost_center(
    cost_center_id: int, 
    current_user: dict = Depends(get_current_user)
):
    """Delete cost center"""
    try:
        deleted = cost_center_service.delete(
            cost_center_id=cost_center_id,
            tenant_id=current_user['tenant_id']
        )
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Cost center not found")
        
        return BaseResponse(
            success=True,
            message="Cost center deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cost-centers/hierarchy", response_model=BaseResponse)
async def get_cost_center_hierarchy(current_user: dict = Depends(get_current_user)):
    """Get cost center hierarchy"""
    try:
        hierarchy = cost_center_service.get_hierarchy(
            tenant_id=current_user['tenant_id']
        )
        
        return BaseResponse(
            success=True,
            message="Cost center hierarchy retrieved successfully",
            data=hierarchy
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cost-centers/import", response_model=BaseResponse)
async def import_cost_centers(
    file: UploadFile = File(...), 
    current_user: dict = Depends(get_current_user)
):
    """Import cost centers from CSV file"""
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")
        
        content = await file.read()
        csv_data = csv.DictReader(io.StringIO(content.decode()))
        
        # Convert CSV rows to Pydantic models
        import_rows = []
        for row in csv_data:
            try:
                import_row = CostCenterImportRow(**row)
                import_rows.append(import_row)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")
        
        result = cost_center_service.import_cost_centers(
            import_data=import_rows,
            tenant_id=current_user['tenant_id'],
            created_by=current_user.get('user_id')
        )
        
        return BaseResponse(
            success=True,
            message=f"Import completed. {result['imported_count']}/{result['total_rows']} cost centers imported",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cost-centers/export-template")
async def export_cost_centers_template(current_user: dict = Depends(get_current_user)):
    """Export cost centers CSV template"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['code', 'name', 'description', 'parent_code', 'category', 'is_active', 'lock_posting', 'currency_code'])
    writer.writerow(['CC-001', 'Main Cost Center', 'Main cost center description', '', 'ADMIN', 'true', 'false', 'USD'])
    writer.writerow(['CC-002', 'Production Center', 'Production cost center', 'CC-001', 'PRODUCTION', 'true', 'false', ''])
    output.seek(0)
    return output.getvalue()
