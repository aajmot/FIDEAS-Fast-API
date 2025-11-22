from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime, timedelta
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse
from core.database.connection import db_manager
from sqlalchemy import text, func

router = APIRouter()

@router.get("/kpis", response_model=BaseResponse)
async def get_dashboard_kpis(current_user: dict = Depends(get_current_user)):
    """Get dashboard KPIs"""
    with db_manager.get_session() as session:
        today = datetime.now().date()
        month_start = today.replace(day=1)
        year_start = today.replace(month=1, day=1)
        
        # Revenue (from sales orders)
        # sales_orders schema uses 'net_amount' as final payable
        revenue_today = session.execute(text("""
            SELECT COALESCE(SUM(net_amount), 0) FROM sales_orders 
            WHERE tenant_id = :tenant_id AND order_date = :today AND is_deleted = FALSE
        """), {"tenant_id": current_user['tenant_id'], "today": today}).scalar() or 0
        
        revenue_month = session.execute(text("""
            SELECT COALESCE(SUM(net_amount), 0) FROM sales_orders 
            WHERE tenant_id = :tenant_id AND order_date >= :month_start AND is_deleted = FALSE
        """), {"tenant_id": current_user['tenant_id'], "month_start": month_start}).scalar() or 0
        
        revenue_year = session.execute(text("""
            SELECT COALESCE(SUM(net_amount), 0) FROM sales_orders 
            WHERE tenant_id = :tenant_id AND order_date >= :year_start AND is_deleted = FALSE
        """), {"tenant_id": current_user['tenant_id'], "year_start": year_start}).scalar() or 0
        
        # Expenses (from purchase orders)
        expense_today = session.execute(text("""
            SELECT COALESCE(SUM(net_amount), 0) FROM purchase_orders 
            WHERE tenant_id = :tenant_id AND order_date = :today AND is_deleted = FALSE
        """), {"tenant_id": current_user['tenant_id'], "today": today}).scalar() or 0
        
        expense_month = session.execute(text("""
            SELECT COALESCE(SUM(net_amount), 0) FROM purchase_orders 
            WHERE tenant_id = :tenant_id AND order_date >= :month_start AND is_deleted = FALSE
        """), {"tenant_id": current_user['tenant_id'], "month_start": month_start}).scalar() or 0
        
        expense_year = session.execute(text("""
            SELECT COALESCE(SUM(net_amount), 0) FROM purchase_orders 
            WHERE tenant_id = :tenant_id AND order_date >= :year_start AND is_deleted = FALSE
        """), {"tenant_id": current_user['tenant_id'], "year_start": year_start}).scalar() or 0
        
        # Stock value
        stock_value = session.execute(text("""
            SELECT COALESCE(SUM(sb.total_quantity * sb.average_cost), 0) 
            FROM stock_balances sb
            WHERE sb.tenant_id = :tenant_id
        """), {"tenant_id": current_user['tenant_id']}).scalar() or 0
        
        # Receivables (AR balance)
        receivables = session.execute(text("""
            SELECT COALESCE(current_balance, 0) FROM account_masters 
            WHERE code = 'AR001' AND tenant_id = :tenant_id
        """), {"tenant_id": current_user['tenant_id']}).scalar() or 0
        
        # Payables (AP balance)
        payables = session.execute(text("""
            SELECT COALESCE(current_balance, 0) FROM account_masters 
            WHERE code = 'AP001' AND tenant_id = :tenant_id
        """), {"tenant_id": current_user['tenant_id']}).scalar() or 0
        
        return BaseResponse(
            success=True,
            message="KPIs retrieved successfully",
            data={
                "revenue": {
                    "today": float(revenue_today),
                    "month": float(revenue_month),
                    "year": float(revenue_year)
                },
                "expenses": {
                    "today": float(expense_today),
                    "month": float(expense_month),
                    "year": float(expense_year)
                },
                "profit": {
                    "today": float(revenue_today - expense_today),
                    "month": float(revenue_month - expense_month),
                    "year": float(revenue_year - expense_year)
                },
                "stock_value": float(stock_value),
                "receivables": float(receivables),
                "payables": float(payables)
            }
        )

@router.get("/revenue-trend", response_model=BaseResponse)
async def get_revenue_trend(current_user: dict = Depends(get_current_user)):
    """Get revenue trend for last 12 months"""
    with db_manager.get_session() as session:
        result = session.execute(text("""
            SELECT 
                TO_CHAR(order_date, 'Mon YYYY') as month,
                SUM(net_amount) as revenue
            FROM sales_orders
            WHERE tenant_id = :tenant_id 
                AND order_date >= CURRENT_DATE - INTERVAL '12 months'
                AND is_deleted = FALSE
            GROUP BY TO_CHAR(order_date, 'Mon YYYY'), DATE_TRUNC('month', order_date)
            ORDER BY DATE_TRUNC('month', order_date)
        """), {"tenant_id": current_user['tenant_id']})
        
        trend = [{"month": row[0], "revenue": float(row[1])} for row in result]
        
        return BaseResponse(
            success=True,
            message="Revenue trend retrieved successfully",
            data=trend
        )

@router.get("/top-products", response_model=BaseResponse)
async def get_top_products(limit: int = Query(10), current_user: dict = Depends(get_current_user)):
    """Get top selling products"""
    with db_manager.get_session() as session:
        result = session.execute(text("""
            SELECT 
                p.name,
                SUM(soi.quantity) as total_quantity,
                SUM(soi.total_price) as total_revenue
            FROM sales_order_items soi
            JOIN products p ON soi.product_id = p.id
            JOIN sales_orders so ON soi.sales_order_id = so.id
            WHERE so.tenant_id = :tenant_id AND so.is_deleted = FALSE
            GROUP BY p.name
            ORDER BY total_revenue DESC
            LIMIT :limit
        """), {"tenant_id": current_user['tenant_id'], "limit": limit})
        
        products = [{"name": row[0], "quantity": float(row[1]), "revenue": float(row[2])} for row in result]
        
        return BaseResponse(
            success=True,
            message="Top products retrieved successfully",
            data=products
        )

@router.get("/recent-transactions", response_model=BaseResponse)
async def get_recent_transactions(limit: int = Query(10), current_user: dict = Depends(get_current_user)):
    """Get recent transactions"""
    with db_manager.get_session() as session:
        result = session.execute(text("""
            SELECT 
                v.voucher_number,
                vt.name as voucher_type,
                v.voucher_date,
                v.base_total_amount,
                v.narration
            FROM vouchers v
            JOIN voucher_types vt ON v.voucher_type_id = vt.id
            WHERE v.tenant_id = :tenant_id AND v.is_deleted = FALSE
            ORDER BY v.voucher_date DESC, v.id DESC
            LIMIT :limit
        """), {"tenant_id": current_user['tenant_id'], "limit": limit})
        
        transactions = [{
            "voucher_number": row[0],
            "type": row[1],
            "date": row[2].isoformat() if row[2] else None,
            "amount": float(row[3]) if row[3] else 0.0,
            "description": row[4] or ""
        } for row in result]
        
        return BaseResponse(
            success=True,
            message="Recent transactions retrieved successfully",
            data=transactions
        )
