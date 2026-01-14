from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from typing import Optional
from api.middleware.auth_middleware import get_current_user
from api.schemas.people_schema.department_schemas import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse, 
    DepartmentListResponse, DepartmentImportRow
)
from api.schemas.common import BaseResponse, PaginatedResponse
from modules.people_module.services.department_service import DepartmentService
import io, csv

router = APIRouter(prefix="/departments")
department_service = DepartmentService()

@router.post("", response_model=BaseResponse)
def create_department(
    department: DepartmentCreate, 
    current_user: dict = Depends(get_current_user)
):
    """Create new department"""
    try:
        department_response = department_service.create(
            department_data=department,
            tenant_id=current_user['tenant_id'],
            created_by=current_user['username']
        )
        
        return BaseResponse(
            success=True,
            message="Department created successfully",
            data=department_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=PaginatedResponse)
def get_departments(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get paginated list of departments with filtering"""
    try:
        result = department_service.get_all(
            tenant_id=current_user['tenant_id'],
            page=page,
            per_page=per_page,
            search=search,
            status=status
        )
        
        return PaginatedResponse(
            success=True,
            message="Departments retrieved successfully",
            data=result["items"],
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"],
            total_pages=result["total_pages"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active", response_model=BaseResponse)
def get_active_departments(current_user: dict = Depends(get_current_user)):
    """Get active departments"""
    try:
        result = department_service.get_all(
            tenant_id=current_user['tenant_id'],
            status='ACTIVE'
        )
        
        return BaseResponse(
            success=True,
            message="Active departments retrieved successfully",
            data=result["items"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{department_id}", response_model=BaseResponse)
def get_department(
    department_id: int, 
    current_user: dict = Depends(get_current_user)
):
    """Get department by ID"""
    try:
        department = department_service.get_by_id(
            department_id=department_id,
            tenant_id=current_user['tenant_id']
        )
        
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
        
        return BaseResponse(
            success=True,
            message="Department retrieved successfully",
            data=department
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{department_id}", response_model=BaseResponse)
def update_department(
    department_id: int, 
    department: DepartmentUpdate, 
    current_user: dict = Depends(get_current_user)
):
    """Update department"""
    try:
        department_response = department_service.update(
            department_id=department_id,
            department_data=department,
            tenant_id=current_user['tenant_id'],
            updated_by=current_user['username']
        )
        
        if not department_response:
            raise HTTPException(status_code=404, detail="Department not found")
        
        return BaseResponse(
            success=True,
            message="Department updated successfully",
            data=department_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{department_id}", response_model=BaseResponse)
def delete_department(
    department_id: int, 
    current_user: dict = Depends(get_current_user)
):
    """Delete department"""
    try:
        deleted = department_service.delete(
            department_id=department_id,
            tenant_id=current_user['tenant_id'],
            updated_by=current_user['username']
        )
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Department not found")
        
        return BaseResponse(
            success=True,
            message="Department deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hierarchy", response_model=BaseResponse)
def get_department_hierarchy(current_user: dict = Depends(get_current_user)):
    """Get department hierarchy"""
    try:
        hierarchy = department_service.get_hierarchy(
            tenant_id=current_user['tenant_id']
        )
        
        return BaseResponse(
            success=True,
            message="Department hierarchy retrieved successfully",
            data=hierarchy
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import", response_model=BaseResponse)
async def import_departments(
    file: UploadFile = File(...), 
    current_user: dict = Depends(get_current_user)
):
    """Import departments from CSV file"""
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")
        
        content = await file.read()
        csv_data = csv.DictReader(io.StringIO(content.decode()))
        
        # Convert CSV rows to Pydantic models
        import_rows = []
        for row in csv_data:
            try:
                import_row = DepartmentImportRow(**row)
                import_rows.append(import_row)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")
        
        result = department_service.import_departments(
            import_data=import_rows,
            tenant_id=current_user['tenant_id'],
            created_by=current_user['username']
        )
        
        return BaseResponse(
            success=True,
            message=f"Import completed. {result['imported_count']}/{result['total_rows']} departments imported",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export-template")
def export_departments_template(current_user: dict = Depends(get_current_user)):
    """Export departments CSV template"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['department_code', 'department_name', 'parent_code', 'description', 'org_unit_type', 'status'])
    writer.writerow(['DEPT-001', 'Main Department', '', 'Main department description', 'DIVISION', 'ACTIVE'])
    writer.writerow(['DEPT-002', 'Sub Department', 'DEPT-001', 'Sub department description', 'DEPARTMENT', 'ACTIVE'])
    output.seek(0)
    return output.getvalue()