from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from api.middleware.auth_middleware import get_current_user
from api.schemas.people_schema.employee_schemas import EmployeeCreate, EmployeeUpdate, EmployeeResponse, EmployeeType
from api.schemas.common import PaginatedResponse, PaginationParams
from modules.people_module.services.employee_service import EmployeeService

router = APIRouter(prefix="/employees")

@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(employee: EmployeeCreate, current_user: dict = Depends(get_current_user)):
    service = EmployeeService()
    
    existing = service.get_by_code(employee.employee_code, current_user['tenant_id'])
    if existing:
        raise HTTPException(status_code=400, detail="Employee code already exists")
    
    employee_data = employee.model_dump()
    employee_data['tenant_id'] = current_user['tenant_id']
    employee_data['created_by'] = current_user['username']
    employee_data['updated_by'] = current_user['username']
    
    return service.create(employee_data)

@router.get("", response_model=PaginatedResponse)
def get_employees(
    pagination: PaginationParams = Depends(),
    employee_type: Optional[EmployeeType] = Query(None, description="Filter by employee type"),
    current_user: dict = Depends(get_current_user)
):
    service = EmployeeService()
    filters = {'tenant_id': current_user['tenant_id'], 'is_deleted': False}
    
    if employee_type:
        filters['employee_type'] = employee_type
    
    employees, total = service.get_paginated(
        filters=filters,
        offset=pagination.offset,
        limit=pagination.per_page,
        search=pagination.search
    )
    
    return PaginatedResponse(
        success=True,
        message="Employees retrieved successfully",
        data=[EmployeeResponse.model_validate(emp) for emp in employees],
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=(total + pagination.per_page - 1) // pagination.per_page
    )

@router.get("/active", response_model=List[EmployeeResponse])
def get_active_employees(current_user: dict = Depends(get_current_user)):
    service = EmployeeService()
    return service.get_active_employees(current_user['tenant_id'])

@router.get("/by-type/{employee_type}", response_model=List[EmployeeResponse])
def get_employees_by_type(employee_type: EmployeeType, current_user: dict = Depends(get_current_user)):
    service = EmployeeService()
    return service.get_by_type(current_user['tenant_id'], employee_type)

@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(employee_id: int, current_user: dict = Depends(get_current_user)):
    service = EmployeeService()
    employee = service.get_by_id(employee_id)
    if not employee or employee.tenant_id != current_user['tenant_id'] or employee.is_deleted:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(employee_id: int, employee: EmployeeUpdate, current_user: dict = Depends(get_current_user)):
    service = EmployeeService()
    existing = service.get_by_id(employee_id)
    if not existing or existing.tenant_id != current_user['tenant_id'] or existing.is_deleted:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    employee_data = employee.model_dump(exclude_unset=True)
    employee_data['updated_by'] = current_user['username']
    
    return service.update(employee_id, employee_data)

@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(employee_id: int, current_user: dict = Depends(get_current_user)):
    service = EmployeeService()
    employee = service.get_by_id(employee_id)
    if not employee or employee.tenant_id != current_user['tenant_id'] or employee.is_deleted:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    service.soft_delete(employee_id, current_user['username'])
