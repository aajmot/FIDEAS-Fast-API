from fastapi import APIRouter, Depends, Query
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.core.auth.oauth2_scheme import get_current_user
from app.core.utils.api_response import APIResponse

router = APIRouter()

@router.get("/kpis")
async def get_dashboard_kpis(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard KPIs"""
    today = datetime.now().date()
    
    # Sample KPI data - implement actual queries based on your models
    kpis = {
        "revenue": {"today": 0.0, "month": 0.0, "year": 0.0},
        "expenses": {"today": 0.0, "month": 0.0, "year": 0.0},
        "profit": {"today": 0.0, "month": 0.0, "year": 0.0},
        "stock_value": 0.0,
        "receivables": 0.0,
        "payables": 0.0
    }
    
    return APIResponse.success(data=kpis)

@router.get("/revenue-trend")
async def get_revenue_trend(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get revenue trend for last 12 months"""
    return APIResponse.success(data=[])

@router.get("/top-products")
async def get_top_products(
    limit: int = Query(10),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get top selling products"""
    return APIResponse.success(data=[])

@router.get("/recent-transactions")
async def get_recent_transactions(
    limit: int = Query(10),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent transactions"""
    return APIResponse.success(data=[])