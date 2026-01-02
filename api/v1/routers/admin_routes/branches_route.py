# api/v1/routers/admin_routes/branches_route.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from api.middleware.auth_middleware import get_current_user
from api.schemas.admin_schema.branch_schemas import BranchCreate, BranchUpdate, BranchResponse
from api.schemas.common import PaginatedResponse, PaginationParams
from modules.admin_module.services.branch_service import BranchService

router = APIRouter(prefix="/branches", tags=["Branches"])

@router.post("", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
def create_branch(branch: BranchCreate, current_user: dict = Depends(get_current_user)):
    service = BranchService()
    
    # Check duplicate branch_code
    existing = service.get_by_code(branch.branch_code, current_user['tenant_id'])
    if existing:
        raise HTTPException(status_code=400, detail="Branch code already exists")
    
    branch_data = branch.model_dump()
    branch_data['tenant_id'] = current_user['tenant_id']
    branch_data['created_by'] = current_user['username']
    branch_data['updated_by'] = current_user['username']
    
    return service.create(branch_data)

@router.get("", response_model=PaginatedResponse)
def get_branches(
    pagination: PaginationParams = Depends(),
    current_user: dict = Depends(get_current_user)
):
    service = BranchService()
    filters = {'tenant_id': current_user['tenant_id'], 'is_deleted': False}
    
    branches, total = service.get_paginated(
        filters=filters,
        offset=pagination.offset,
        limit=pagination.per_page,
        search=pagination.search
    )
    
    return PaginatedResponse(
        success=True,
        message="Branches retrieved successfully",
        data=[BranchResponse.model_validate(branch) for branch in branches],
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=(total + pagination.per_page - 1) // pagination.per_page
    )

@router.get("/active", response_model=List[BranchResponse])
def get_active_branches(current_user: dict = Depends(get_current_user)):
    service = BranchService()
    return service.get_active_branches(current_user['tenant_id'])

@router.get("/{branch_id}", response_model=BranchResponse)
def get_branch(branch_id: int, current_user: dict = Depends(get_current_user)):
    service = BranchService()
    branch = service.get_by_id(branch_id)
    if not branch or branch.tenant_id != current_user['tenant_id'] or branch.is_deleted:
        raise HTTPException(status_code=404, detail="Branch not found")
    return branch

@router.put("/{branch_id}", response_model=BranchResponse)
def update_branch(branch_id: int, branch: BranchUpdate, current_user: dict = Depends(get_current_user)):
    service = BranchService()
    existing = service.get_by_id(branch_id)
    if not existing or existing.tenant_id != current_user['tenant_id'] or existing.is_deleted:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    branch_data = branch.model_dump(exclude_unset=True)
    branch_data['updated_by'] = current_user['username']
    
    return service.update(branch_id, branch_data)

@router.delete("/{branch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_branch(branch_id: int, current_user: dict = Depends(get_current_user)):
    service = BranchService()
    branch = service.get_by_id(branch_id)
    if not branch or branch.tenant_id != current_user['tenant_id'] or branch.is_deleted:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    service.soft_delete(branch_id, current_user['username'])
