from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from typing import Optional
from api.middleware.auth_middleware import get_current_user
from api.schemas.people_schema.employee_schemas import (
    EmployeeCreate, EmployeeUpdate, EmployeeResponse, 
    EmployeeListResponse, EmployeeImportRow
)
from api.schemas.common import BaseResponse, PaginatedResponse
from modules.people_module.services.employee_service import EmployeeService
import io, csv

router = APIRouter(prefix="/employees")
employee_service = EmployeeService()

@router.get("", response_model=PaginatedResponse)
def get_employees(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    employee_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get paginated list of employees with filtering"""
    try:
        result = employee_service.get_all(
            tenant_id=current_user['tenant_id'],
            page=page,
            per_page=per_page,
            search=search,
            status=status,
            employee_type=employee_type
        )
        
        return PaginatedResponse(
            success=True,
            message="Employees retrieved successfully",
            data=result["items"],
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"],
            total_pages=result["total_pages"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{employee_id}", response_model=BaseResponse)
def get_employee(
    employee_id: int, 
    current_user: dict = Depends(get_current_user)
):
    """Get employee by ID"""
    try:
        employee = employee_service.get_by_id(
            employee_id=employee_id,
            tenant_id=current_user['tenant_id']
        )
        
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        return BaseResponse(
            success=True,
            message="Employee retrieved successfully",
            data=employee
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("", response_model=BaseResponse)
def create_employee(
    employee: EmployeeCreate, 
    current_user: dict = Depends(get_current_user)
):
    """Create new employee with optional user account"""
    try:
        employee_response = employee_service.create(
            employee_data=employee,
            tenant_id=current_user['tenant_id'],
            created_by=current_user['username']
        )
        
        return BaseResponse(
            success=True,
            message="Employee created successfully",
            data=employee_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{employee_id}", response_model=BaseResponse)
def update_employee(
    employee_id: int, 
    employee: EmployeeUpdate, 
    current_user: dict = Depends(get_current_user)
):
    """Update employee"""
    try:
        employee_response = employee_service.update(
            employee_id=employee_id,
            employee_data=employee,
            tenant_id=current_user['tenant_id'],
            updated_by=current_user['username']
        )
        
        if not employee_response:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        return BaseResponse(
            success=True,
            message="Employee updated successfully",
            data=employee_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{employee_id}", response_model=BaseResponse)
def delete_employee(
    employee_id: int, 
    current_user: dict = Depends(get_current_user)
):
    """Delete employee"""
    try:
        deleted = employee_service.delete(
            employee_id=employee_id,
            tenant_id=current_user['tenant_id'],
            updated_by=current_user['username']
        )
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        return BaseResponse(
            success=True,
            message="Employee deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import", response_model=BaseResponse)
async def import_employees(
    file: UploadFile = File(...), 
    current_user: dict = Depends(get_current_user)
):
    """Import employees from CSV file"""
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")
        
        content = await file.read()
        csv_data = csv.DictReader(io.StringIO(content.decode()))
        
        # Convert CSV rows to Pydantic models
        import_rows = []
        for row in csv_data:
            try:
                import_row = EmployeeImportRow(**row)
                import_rows.append(import_row)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")
        
        result = employee_service.import_employees(
            import_data=import_rows,
            tenant_id=current_user['tenant_id'],
            created_by=current_user['username']
        )
        
        return BaseResponse(
            success=True,
            message=f"Import completed. {result['imported_count']}/{result['total_rows']} employees imported",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export-template")
def export_employees_template(current_user: dict = Depends(get_current_user)):
    """Export employees CSV template"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['employee_code', 'employee_name', 'employee_type', 'phone', 'email', 'qualification', 'specialization', 'employment_type', 'status'])
    writer.writerow(['EMP-001', 'John Doe', 'ADMIN', '1234567890', 'john@example.com', 'MBA', 'Management', 'INTERNAL', 'ACTIVE'])
    writer.writerow(['DOC-001', 'Dr. Smith', 'DOCTOR', '0987654321', 'smith@example.com', 'MBBS', 'Cardiology', 'INTERNAL', 'ACTIVE'])
    output.seek(0)
    return output.getvalue()