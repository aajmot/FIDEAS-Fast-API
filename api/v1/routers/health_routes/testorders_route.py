from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.schemas.health_schema.test_order_schema import TestOrderCreateSchema, TestOrderUpdateSchema
from api.middleware.auth_middleware import get_current_user
from modules.health_module.services.test_order_service import TestOrderService
from modules.health_module.services.test_result_service import TestResultService

router = APIRouter()

# Test Order endpoints
@router.get("/testorders", response_model=PaginatedResponse)
async def get_test_orders(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    service = TestOrderService()
    result = service.get_paginated(
        tenant_id=current_user["tenant_id"],
        page=pagination.page,
        per_page=pagination.per_page,
        search=pagination.search
    )
    
    return PaginatedResponse(
        success=True,
        message="Test orders retrieved successfully",
        **result
    )

@router.post("/testorders", response_model=BaseResponse)
async def create_test_order(order_data: TestOrderCreateSchema, current_user: dict = Depends(get_current_user)):
    service = TestOrderService()
    order_dict = order_data.dict()
    order_dict["tenant_id"] = current_user["tenant_id"]
    order_dict["created_by"] = current_user["username"]
    
    order = service.create_with_accounting(order_dict, current_user["username"], current_user["tenant_id"])
    
    return BaseResponse(
        success=True,
        message="Test order created successfully",
        data={"id": order.id}
    )

@router.get("/testorders/{order_id}", response_model=BaseResponse)
async def get_test_order(order_id: int, current_user: dict = Depends(get_current_user)):
    service = TestOrderService()
    order_data = service.get_order_with_items(order_id, current_user["tenant_id"])
    
    if not order_data:
        raise HTTPException(status_code=404, detail="Test order not found")
    
    return BaseResponse(
        success=True,
        message="Test order retrieved successfully",
        data=order_data
    )

@router.put("/testorders/{order_id}", response_model=BaseResponse)
async def update_test_order(order_id: int, order_data: TestOrderUpdateSchema, current_user: dict = Depends(get_current_user)):
    service = TestOrderService()
    order_dict = order_data.dict(exclude_unset=True)
    order_dict["updated_by"] = current_user["username"]
    
    order = service.update(order_id, order_dict, current_user["tenant_id"])
    
    if not order:
        raise HTTPException(status_code=404, detail="Test order not found")
    
    return BaseResponse(success=True, message="Test order updated successfully")

@router.delete("/testorders/{order_id}", response_model=BaseResponse)
async def delete_test_order(order_id: int, current_user: dict = Depends(get_current_user)):
    service = TestOrderService()
    success = service.delete(order_id, current_user["tenant_id"])
    
    if not success:
        raise HTTPException(status_code=404, detail="Test order not found")
    
    return BaseResponse(success=True, message="Test order deleted successfully")

# Test Result endpoints
@router.get("/testresults", response_model=PaginatedResponse)
async def get_test_results(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    service = TestResultService()
    result = service.get_paginated(
        tenant_id=current_user["tenant_id"],
        page=pagination.page,
        per_page=pagination.per_page,
        search=pagination.search
    )
    
    return PaginatedResponse(
        success=True,
        message="Test results retrieved successfully",
        **result
    )

@router.post("/testresults", response_model=BaseResponse)
async def create_test_result(result_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    service = TestResultService()
    result_data["tenant_id"] = current_user["tenant_id"]
    result_data["created_by"] = current_user["username"]
    result = service.create(result_data)
    
    return BaseResponse(
        success=True,
        message="Test result created successfully",
        data={"id": result.id}
    )
