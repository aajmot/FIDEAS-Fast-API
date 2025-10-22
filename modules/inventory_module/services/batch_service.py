from datetime import datetime, timedelta
from typing import List, Dict, Optional
from core.database.connection import db_manager

class BatchService:
    @staticmethod
    def create_batch(product_id: int, batch_no: str, mfg_date: str, exp_date: str, 
                     quantity: float, mrp: float, tenant_id: int) -> int:
        with db_manager.get_session() as session:
            result = session.execute(
                "INSERT INTO product_batches (product_id, batch_no, mfg_date, exp_date, quantity, mrp, tenant_id, is_active) "
                "VALUES (:pid, :bno, :mfg, :exp, :qty, :mrp, :tid, true) RETURNING batch_id",
                {"pid": product_id, "bno": batch_no, "mfg": mfg_date, "exp": exp_date, "qty": quantity, "mrp": mrp, "tid": tenant_id}
            )
            return result.fetchone()[0]

    @staticmethod
    def get_near_expiry_batches(days: int, tenant_id: int) -> List[Dict]:
        with db_manager.get_session() as session:
            exp_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
            result = session.execute(
                "SELECT pb.batch_id, pb.batch_no, p.product_name, pb.exp_date, pb.quantity, pb.mrp "
                "FROM product_batches pb JOIN products p ON pb.product_id = p.product_id "
                "WHERE pb.tenant_id = :tid AND pb.exp_date <= :exp AND pb.quantity > 0 AND pb.is_active = true ORDER BY pb.exp_date",
                {"tid": tenant_id, "exp": exp_date}
            )
            return [{"batch_id": r[0], "batch_no": r[1], "product_name": r[2], 
                    "exp_date": r[3], "quantity": r[4], "mrp": r[5]} for r in result.fetchall()]

    @staticmethod
    def get_batch_stock(product_id: int, tenant_id: int) -> List[Dict]:
        with db_manager.get_session() as session:
            result = session.execute(
                "SELECT batch_id, batch_no, mfg_date, exp_date, quantity, mrp FROM product_batches "
                "WHERE product_id = :pid AND tenant_id = :tid AND quantity > 0 AND is_active = true ORDER BY exp_date",
                {"pid": product_id, "tid": tenant_id}
            )
            return [{"batch_id": r[0], "batch_no": r[1], "mfg_date": r[2], 
                    "exp_date": r[3], "quantity": r[4], "mrp": r[5]} for r in result.fetchall()]

    @staticmethod
    def update_batch_quantity(batch_id: int, quantity_change: float, tenant_id: int):
        with db_manager.get_session() as session:
            session.execute(
                "UPDATE product_batches SET quantity = quantity + :change WHERE batch_id = :bid AND tenant_id = :tid",
                {"change": quantity_change, "bid": batch_id, "tid": tenant_id}
            )
