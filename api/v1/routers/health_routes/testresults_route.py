from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from sqlalchemy import or_
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user
from modules.diagnostic_module.services.test_panel_service import TestPanelService
from modules.diagnostic_module.services.test_result_service import TestResultService

router = APIRouter()

@router.get("/testresults/{result_id}", response_model=BaseResponse)
async def get_test_result(result_id: int, current_user: dict = Depends(get_current_user)):
    service = TestResultService()
    result = service.get_by_id(result_id, current_user["tenant_id"])
    
    if not result:
        raise HTTPException(status_code=404, detail="Test result not found")
    
    details = service.get_details(result_id, current_user["tenant_id"])
    files = service.get_files(result_id, current_user["tenant_id"])
    
    return BaseResponse(
        success=True,
        message="Test result retrieved successfully",
        data={
            "id": result.id,
            "result_number": result.result_number,
            "test_order_id": result.test_order_id,
            "result_date": result.result_date.isoformat() if result.result_date else None,
            "overall_report": result.overall_report,
            "performed_by": result.performed_by,
            "result_type": result.result_type,
            "notes": result.notes,
            "doctor_id": result.doctor_id,
            "license_number": result.license_number,
            "created_at": result.created_at.isoformat() if result.created_at else None,
            "created_by": result.created_by,
            "updated_at": result.updated_at.isoformat() if result.updated_at else None,
            "updated_by": result.updated_by,
            "details": [{
                "id": detail.id,
                "parameter_id": detail.parameter_id,
                "parameter_name": detail.parameter_name,
                "unit": detail.unit,
                "parameter_value": detail.parameter_value,
                "reference_value": detail.reference_value,
                "verdict": detail.verdict,
                "notes": detail.notes
            } for detail in details],
            "files": [{
                "id": file.id,
                "file_name": file.file_name,
                "file_path": file.file_path,
                "file_format": file.file_format,
                "file_size": file.file_size,
                "acquisition_date": file.acquisition_date.isoformat() if file.acquisition_date else None,
                "description": file.description,
                "storage_system": file.storage_system
            } for file in files]
        }
    )

@router.put("/testresults/{result_id}", response_model=BaseResponse)
async def update_test_result(result_id: int, result_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    service = TestResultService()
    result_data["updated_by"] = current_user["username"]
    
    result = service.update(result_id, result_data)
    
    if not result:
        raise HTTPException(status_code=404, detail="Test result not found")
    
    return BaseResponse(success=True, message="Test result updated successfully")

@router.delete("/testresults/{result_id}", response_model=BaseResponse)
async def delete_test_result(result_id: int, current_user: dict = Depends(get_current_user)):
    service = TestResultService()
    success = service.delete(result_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Test result not found")
    
    return BaseResponse(success=True, message="Test result deleted successfully")

@router.get("/testresults/order/{order_id}", response_model=BaseResponse)
async def get_test_results_by_order(order_id: int, current_user: dict = Depends(get_current_user)):
    service = TestResultService()
    results = service.get_by_order_id(order_id, current_user["tenant_id"])
    
    return BaseResponse(
        success=True,
        message="Test results retrieved successfully",
        data=[{
            "id": result.id,
            "result_number": result.result_number,
            "test_order_id": result.test_order_id,
            "result_date": result.result_date.isoformat() if result.result_date else None,
            "overall_report": result.overall_report,
            "performed_by": result.performed_by,
            "result_type": result.result_type,
            "notes": result.notes,
            "created_at": result.created_at.isoformat() if result.created_at else None
        } for result in results]
    )
