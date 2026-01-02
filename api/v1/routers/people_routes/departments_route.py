from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from api.middleware.auth_middleware import get_current_user
from api.schemas.people_schema.department_schemas import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from api.schemas.common import PaginatedResponse, PaginationParams
from modules.people_module.services.department_service import DepartmentService

router = APIRouter(prefix="/departments")

@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(department: DepartmentCreate, current_user: dict = Depends(get_current_user)):
    service = DepartmentService()
    
    existing = service.get_by_code(department.department_code, current_user['tenant_id'])
    if existing:
        raise HTTPException(status_code=400, detail="Department code already exists")
    
    department_data = department.model_dump()
    department_data['tenant_id'] = current_user['tenant_id']
    department_data['created_by'] = current_user['username']
    department_data['updated_by'] = current_user['username']
    
    return service.create(department_data)

@router.get("", response_model=PaginatedResponse)
def get_departments(
    pagination: PaginationParams = Depends(),
    current_user: dict = Depends(get_current_user)
):
    service = DepartmentService()
    filters = {'tenant_id': current_user['tenant_id'], 'is_deleted': False}
    
    departments, total = service.get_paginated(
        filters=filters,
        offset=pagination.offset,
        limit=pagination.per_page,
        search=pagination.search
    )
    
    return PaginatedResponse(
        success=True,
        message="Departments retrieved successfully",
        data=[DepartmentResponse.model_validate(dept) for dept in departments],
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=(total + pagination.per_page - 1) // pagination.per_page
    )

@router.get("/active", response_model=List[DepartmentResponse])
def get_active_departments(current_user: dict = Depends(get_current_user)):
    service = DepartmentService()
    return service.get_active_departments(current_user['tenant_id'])

@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department(department_id: int, current_user: dict = Depends(get_current_user)):
    service = DepartmentService()
    department = service.get_by_id(department_id)
    if not department or department.tenant_id != current_user['tenant_id'] or department.is_deleted:
        raise HTTPException(status_code=404, detail="Department not found")
    return department

@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(department_id: int, department: DepartmentUpdate, current_user: dict = Depends(get_current_user)):
    service = DepartmentService()
    existing = service.get_by_id(department_id)
    if not existing or existing.tenant_id != current_user['tenant_id'] or existing.is_deleted:
        raise HTTPException(status_code=404, detail="Department not found")
    
    department_data = department.model_dump(exclude_unset=True)
    department_data['updated_by'] = current_user['username']
    
    return service.update(department_id, department_data)

@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(department_id: int, current_user: dict = Depends(get_current_user)):
    service = DepartmentService()
    department = service.get_by_id(department_id)
    if not department or department.tenant_id != current_user['tenant_id'] or department.is_deleted:
        raise HTTPException(status_code=404, detail="Department not found")
    
    service.soft_delete(department_id, current_user['username'])
