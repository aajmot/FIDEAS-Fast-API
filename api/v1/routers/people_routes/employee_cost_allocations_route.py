from fastapi import APIRouter, Depends, HTTPException
from typing import List
from api.middleware.auth_middleware import get_current_user
from api.schemas.people_schema.employee_schemas import (
    CostAllocationCreate, CostAllocationUpdate, CostAllocationResponse
)
from api.schemas.common import BaseResponse
from modules.people_module.services.employee_cost_allocation_service import EmployeeCostAllocationService

router = APIRouter(prefix="/employee-cost-allocations")
cost_allocation_service = EmployeeCostAllocationService()

@router.get("/employee/{employee_id}", response_model=BaseResponse)
def get_employee_cost_allocations(
    employee_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get all cost allocations for an employee"""
    try:
        allocations = cost_allocation_service.get_by_employee(
            employee_id=employee_id,
            tenant_id=current_user['tenant_id']
        )
        
        return BaseResponse(
            success=True,
            message="Cost allocations retrieved successfully",
            data=allocations
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{allocation_id}", response_model=BaseResponse)
def get_cost_allocation(
    allocation_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get cost allocation by ID"""
    try:
        allocation = cost_allocation_service.get_by_id(
            allocation_id=allocation_id,
            tenant_id=current_user['tenant_id']
        )
        
        if not allocation:
            raise HTTPException(status_code=404, detail="Cost allocation not found")
        
        return BaseResponse(
            success=True,
            message="Cost allocation retrieved successfully",
            data=allocation
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("", response_model=BaseResponse)
def create_cost_allocation(
    allocation: CostAllocationCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create new cost allocation"""
    try:
        allocation_response = cost_allocation_service.create(
            allocation_data=allocation,
            tenant_id=current_user['tenant_id'],
            created_by=current_user['username']
        )
        
        return BaseResponse(
            success=True,
            message="Cost allocation created successfully",
            data=allocation_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{allocation_id}", response_model=BaseResponse)
def update_cost_allocation(
    allocation_id: int,
    allocation: CostAllocationUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update cost allocation"""
    try:
        allocation_response = cost_allocation_service.update(
            allocation_id=allocation_id,
            allocation_data=allocation,
            tenant_id=current_user['tenant_id'],
            updated_by=current_user['username']
        )
        
        if not allocation_response:
            raise HTTPException(status_code=404, detail="Cost allocation not found")
        
        return BaseResponse(
            success=True,
            message="Cost allocation updated successfully",
            data=allocation_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{allocation_id}", response_model=BaseResponse)
def delete_cost_allocation(
    allocation_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete cost allocation"""
    try:
        deleted = cost_allocation_service.delete(
            allocation_id=allocation_id,
            tenant_id=current_user['tenant_id']
        )
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Cost allocation not found")
        
        return BaseResponse(
            success=True,
            message="Cost allocation deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))