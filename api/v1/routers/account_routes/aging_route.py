from fastapi import APIRouter, Depends
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse
from core.database.connection import db_manager
from sqlalchemy import text

router = APIRouter()


@router.get("/aging-analysis/receivables", response_model=BaseResponse)
async def get_receivables_aging(current_user: dict = Depends(get_current_user)):
    """Get receivables aging analysis"""
    with db_manager.get_session() as session:
        result = session.execute(text("""
            SELECT 
                c.name as customer_name,
                SUM(CASE WHEN CURRENT_DATE - so.order_date <= 30 THEN so.total_amount ELSE 0 END) as days_0_30,
                SUM(CASE WHEN CURRENT_DATE - so.order_date BETWEEN 31 AND 60 THEN so.total_amount ELSE 0 END) as days_31_60,
                SUM(CASE WHEN CURRENT_DATE - so.order_date BETWEEN 61 AND 90 THEN so.total_amount ELSE 0 END) as days_61_90,
                SUM(CASE WHEN CURRENT_DATE - so.order_date > 90 THEN so.total_amount ELSE 0 END) as days_90_plus,
                SUM(so.total_amount) as total
            FROM sales_orders so
            JOIN customers c ON so.customer_id = c.id
            WHERE so.tenant_id = :tenant_id AND so.is_deleted = FALSE
            GROUP BY c.name
            ORDER BY total DESC
        """), {"tenant_id": current_user['tenant_id']})

        aging_data = [{
            "customer": r[0],
            "0-30": float(r[1]),
            "31-60": float(r[2]),
            "61-90": float(r[3]),
            "90+": float(r[4]),
            "total": float(r[5])
        } for r in result]

        return BaseResponse(
            success=True,
            message="Receivables aging retrieved successfully",
            data=aging_data
        )


@router.get("/aging-analysis/payables", response_model=BaseResponse)
async def get_payables_aging(current_user: dict = Depends(get_current_user)):
    """Get payables aging analysis"""
    with db_manager.get_session() as session:
        result = session.execute(text("""
            SELECT 
                s.name as supplier_name,
                SUM(CASE WHEN CURRENT_DATE - po.order_date <= 30 THEN po.total_amount ELSE 0 END) as days_0_30,
                SUM(CASE WHEN CURRENT_DATE - po.order_date BETWEEN 31 AND 60 THEN po.total_amount ELSE 0 END) as days_31_60,
                SUM(CASE WHEN CURRENT_DATE - po.order_date BETWEEN 61 AND 90 THEN po.total_amount ELSE 0 END) as days_61_90,
                SUM(CASE WHEN CURRENT_DATE - po.order_date > 90 THEN po.total_amount ELSE 0 END) as days_90_plus,
                SUM(po.total_amount) as total
            FROM purchase_orders po
            JOIN suppliers s ON po.supplier_id = s.id
            WHERE po.tenant_id = :tenant_id AND po.is_deleted = FALSE
            GROUP BY s.name
            ORDER BY total DESC
        """), {"tenant_id": current_user['tenant_id']})

        aging_data = [{
            "supplier": r[0],
            "0-30": float(r[1]),
            "31-60": float(r[2]),
            "61-90": float(r[3]),
            "90+": float(r[4]),
            "total": float(r[5])
        } for r in result]

        return BaseResponse(
            success=True,
            message="Payables aging retrieved successfully",
            data=aging_data
        )
