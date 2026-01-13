from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse
from modules.dashboard.services.health_dashboard_service import HealthDashboardService

router = APIRouter()

@router.get("/patient-analytics", response_model=BaseResponse)
async def get_patient_analytics(current_user: dict = Depends(get_current_user)) -> BaseResponse:
    """Get patient analytics for health dashboard"""
    try:
        analytics = HealthDashboardService.get_patient_analytics(current_user["tenant_id"])
        return BaseResponse(success=True, message="Patient analytics retrieved successfully", data=analytics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/appointment-analytics", response_model=BaseResponse)
async def get_appointment_analytics(current_user: dict = Depends(get_current_user)) -> BaseResponse:
    """Get appointment analytics for health dashboard"""
    try:
        analytics = HealthDashboardService.get_appointment_analytics(current_user["tenant_id"])
        return BaseResponse(success=True, message="Appointment analytics retrieved successfully", data=analytics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clinical-operations", response_model=BaseResponse)
async def get_clinical_operations(current_user: dict = Depends(get_current_user)) -> BaseResponse:
    """Get clinical operations metrics for health dashboard"""
    try:
        operations = HealthDashboardService.get_clinical_operations(current_user["tenant_id"])
        return BaseResponse(success=True, message="Clinical operations retrieved successfully", data=operations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/doctor-performance", response_model=BaseResponse)
async def get_doctor_performance(current_user: dict = Depends(get_current_user)) -> BaseResponse:
    """Get doctor performance metrics for health dashboard"""
    try:
        performance = HealthDashboardService.get_doctor_performance(current_user["tenant_id"])
        return BaseResponse(success=True, message="Doctor performance retrieved successfully", data=performance)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-analytics", response_model=BaseResponse)
async def get_test_analytics(current_user: dict = Depends(get_current_user)) -> BaseResponse:
    """Get test analytics for health dashboard"""
    try:
        analytics = HealthDashboardService.get_test_analytics(current_user["tenant_id"])
        return BaseResponse(success=True, message="Test analytics retrieved successfully", data=analytics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))