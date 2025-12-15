from datetime import datetime, timedelta
from sqlalchemy import text
from core.database.connection import db_manager


class DashboardService:
    """Service for dashboard analytics and KPIs"""

    @staticmethod
    def get_kpis(tenant_id: int) -> dict:
        """Get dashboard KPIs for revenue, expenses, profit, stock, receivables, and payables"""
        with db_manager.get_session() as session:
            today = datetime.now().date()
            month_start = today.replace(day=1)
            year_start = today.replace(month=1, day=1)

            # Revenue (from sales orders)
            revenue_today = session.execute(
                text("""
                    SELECT COALESCE(SUM(net_amount), 0) FROM sales_orders 
                    WHERE tenant_id = :tenant_id AND order_date = :today AND is_deleted = FALSE
                """),
                {"tenant_id": tenant_id, "today": today},
            ).scalar() or 0

            revenue_month = session.execute(
                text("""
                    SELECT COALESCE(SUM(net_amount), 0) FROM sales_orders 
                    WHERE tenant_id = :tenant_id AND order_date >= :month_start AND is_deleted = FALSE
                """),
                {"tenant_id": tenant_id, "month_start": month_start},
            ).scalar() or 0

            revenue_year = session.execute(
                text("""
                    SELECT COALESCE(SUM(net_amount), 0) FROM sales_orders 
                    WHERE tenant_id = :tenant_id AND order_date >= :year_start AND is_deleted = FALSE
                """),
                {"tenant_id": tenant_id, "year_start": year_start},
            ).scalar() or 0

            # Expenses (from purchase orders)
            expense_today = session.execute(
                text("""
                    SELECT COALESCE(SUM(net_amount), 0) FROM purchase_orders 
                    WHERE tenant_id = :tenant_id AND order_date = :today AND is_deleted = FALSE
                """),
                {"tenant_id": tenant_id, "today": today},
            ).scalar() or 0

            expense_month = session.execute(
                text("""
                    SELECT COALESCE(SUM(net_amount), 0) FROM purchase_orders 
                    WHERE tenant_id = :tenant_id AND order_date >= :month_start AND is_deleted = FALSE
                """),
                {"tenant_id": tenant_id, "month_start": month_start},
            ).scalar() or 0

            expense_year = session.execute(
                text("""
                    SELECT COALESCE(SUM(net_amount), 0) FROM purchase_orders 
                    WHERE tenant_id = :tenant_id AND order_date >= :year_start AND is_deleted = FALSE
                """),
                {"tenant_id": tenant_id, "year_start": year_start},
            ).scalar() or 0

            # Stock value
            stock_value = session.execute(
                text("""
                    SELECT COALESCE(SUM(sb.total_quantity * sb.average_cost), 0) 
                    FROM stock_balances sb
                    WHERE sb.tenant_id = :tenant_id
                """),
                {"tenant_id": tenant_id},
            ).scalar() or 0

            # Receivables (AR balance)
            receivables = session.execute(
                text("""
                    SELECT COALESCE(current_balance, 0) FROM account_masters 
                    WHERE code = 'AR001' AND tenant_id = :tenant_id
                """),
                {"tenant_id": tenant_id},
            ).scalar() or 0

            # Payables (AP balance)
            payables = session.execute(
                text("""
                    SELECT COALESCE(current_balance, 0) FROM account_masters 
                    WHERE code = 'AP001' AND tenant_id = :tenant_id
                """),
                {"tenant_id": tenant_id},
            ).scalar() or 0

            return {
                "revenue": {
                    "today": float(revenue_today),
                    "month": float(revenue_month),
                    "year": float(revenue_year),
                },
                "expenses": {
                    "today": float(expense_today),
                    "month": float(expense_month),
                    "year": float(expense_year),
                },
                "profit": {
                    "today": float(revenue_today - expense_today),
                    "month": float(revenue_month - expense_month),
                    "year": float(revenue_year - expense_year),
                },
                "stock_value": float(stock_value),
                "receivables": float(receivables),
                "payables": float(payables),
            }

    @staticmethod
    def get_revenue_trend(tenant_id: int) -> list:
        """Get revenue trend for last 12 months"""
        with db_manager.get_session() as session:
            result = session.execute(
                text("""
                    SELECT 
                        TO_CHAR(order_date, 'Mon YYYY') as month,
                        SUM(net_amount) as revenue
                    FROM sales_orders
                    WHERE tenant_id = :tenant_id 
                        AND order_date >= CURRENT_DATE - INTERVAL '12 months'
                        AND is_deleted = FALSE
                    GROUP BY TO_CHAR(order_date, 'Mon YYYY'), DATE_TRUNC('month', order_date)
                    ORDER BY DATE_TRUNC('month', order_date)
                """),
                {"tenant_id": tenant_id},
            )

            trend = [{"month": row[0], "revenue": float(row[1])} for row in result]
            return trend

    @staticmethod
    def get_top_products(tenant_id: int, limit: int = 10) -> list:
        """Get top selling products from sales invoices"""
        with db_manager.get_session() as session:
            result = session.execute(
                text("""
                    SELECT 
                        p.id,
                        p.name,
                        SUM(sii.quantity) as total_quantity,
                        SUM(sii.total_amount_base) as total_revenue
                    FROM sales_invoice_items sii
                    JOIN products p ON sii.product_id = p.id
                    JOIN sales_invoices si ON sii.invoice_id = si.id
                    WHERE si.tenant_id = :tenant_id 
                        AND p.tenant_id = :tenant_id
                        AND si.is_deleted = FALSE
                    GROUP BY p.id, p.name
                    ORDER BY total_revenue DESC
                    LIMIT :limit
                """),
                {"tenant_id": tenant_id, "limit": limit},
            )

            products = [
                {
                    "id": row[0],
                    "name": row[1],
                    "quantity": float(row[2]),
                    "revenue": float(row[3]),
                }
                for row in result
            ]
            return products

    @staticmethod
    def get_recent_transactions(tenant_id: int, limit: int = 10) -> list:
        """Get recent transactions"""
        with db_manager.get_session() as session:
            result = session.execute(
                text("""
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
                """),
                {"tenant_id": tenant_id, "limit": limit},
            )

            transactions = [
                {
                    "voucher_number": row[0],
                    "type": row[1],
                    "date": row[2].isoformat() if row[2] else None,
                    "amount": float(row[3]) if row[3] else 0.0,
                    "description": row[4] or "",
                }
                for row in result
            ]
            return transactions
