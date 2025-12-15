from fastapi import APIRouter, Depends, Query
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse
from modules.dashboard.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/kpis", response_model=BaseResponse)
async def get_dashboard_kpis(current_user: dict = Depends(get_current_user)):
    """Get dashboard KPIs"""
    kpis = DashboardService.get_kpis(current_user["tenant_id"])
    return BaseResponse(success=True, message="KPIs retrieved successfully", data=kpis)


@router.get("/revenue-trend", response_model=BaseResponse)
async def get_revenue_trend(current_user: dict = Depends(get_current_user)):
    """Get revenue trend for last 12 months"""
    trend = DashboardService.get_revenue_trend(current_user["tenant_id"])
    return BaseResponse(
        success=True,
        message="Revenue trend retrieved successfully",
        data=trend,
    )


@router.get("/top-products", response_model=BaseResponse)
async def get_top_products(limit: int = Query(10), current_user: dict = Depends(get_current_user)):
    """Get top selling products"""
    products = DashboardService.get_top_products(current_user["tenant_id"], limit)
    return BaseResponse(
        success=True,
        message="Top products retrieved successfully",
        data=products,
    )

@router.get("/recent-transactions", response_model=BaseResponse)
async def get_recent_transactions(limit: int = Query(10), current_user: dict = Depends(get_current_user)):
    """Get recent transactions"""
    transactions = DashboardService.get_recent_transactions(current_user["tenant_id"], limit)
    return BaseResponse(
        success=True,
        message="Recent transactions retrieved successfully",
        data=transactions,
    )
