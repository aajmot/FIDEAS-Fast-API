from typing import List, Dict, Optional
from datetime import datetime
from core.database.connection import db_manager
import csv
from io import StringIO

class ReconciliationService:
    @staticmethod
    def import_bank_statement(csv_content: str, account_id: int, tenant_id: int) -> List[Dict]:
        with db_manager.get_session() as session:
            reader = csv.DictReader(StringIO(csv_content))
            imported = []
            for row in reader:
                result = session.execute(
                    "INSERT INTO bank_statements (account_id, trans_date, description, debit, credit, balance, tenant_id) "
                    "VALUES (:aid, :date, :desc, :debit, :credit, :bal, :tid) RETURNING statement_id",
                    {"aid": account_id, "date": row['date'], "desc": row['description'], 
                     "debit": row.get('debit', 0), "credit": row.get('credit', 0), "bal": row['balance'], "tid": tenant_id}
                )
                imported.append({"statement_id": result.fetchone()[0], "description": row['description']})
            return imported

    @staticmethod
    def auto_match_transactions(account_id: int, tenant_id: int) -> List[Dict]:
        with db_manager.get_session() as session:
            result = session.execute(
                "SELECT bs.statement_id, bs.trans_date, bs.description, bs.debit, bs.credit, "
                "vd.voucher_detail_id, vd.voucher_id, vd.amount FROM bank_statements bs "
                "LEFT JOIN voucher_details vd ON vd.account_id = :aid AND vd.tenant_id = :tid "
                "AND ABS(COALESCE(bs.debit, bs.credit) - vd.amount) < 0.01 AND DATE(vd.created_at) = bs.trans_date "
                "WHERE bs.account_id = :aid AND bs.tenant_id = :tid AND bs.is_reconciled = false",
                {"aid": account_id, "tid": tenant_id}
            )
            matches = []
            for row in result.fetchall():
                if row[5]:
                    session.execute(
                        "UPDATE bank_statements SET is_reconciled = true, voucher_id = :vid, reconciled_at = :now WHERE statement_id = :sid",
                        {"vid": row[6], "now": datetime.now(), "sid": row[0]}
                    )
                    matches.append({"statement_id": row[0], "voucher_id": row[6], "amount": float(row[7])})
            return matches

    @staticmethod
    def manual_reconcile(statement_id: int, voucher_id: int, tenant_id: int):
        with db_manager.get_session() as session:
            session.execute(
                "UPDATE bank_statements SET is_reconciled = true, voucher_id = :vid, reconciled_at = :now "
                "WHERE statement_id = :sid AND tenant_id = :tid",
                {"vid": voucher_id, "now": datetime.now(), "sid": statement_id, "tid": tenant_id}
            )

    @staticmethod
    def get_unreconciled(account_id: int, tenant_id: int) -> List[Dict]:
        with db_manager.get_session() as session:
            result = session.execute(
                "SELECT statement_id, trans_date, description, debit, credit, balance FROM bank_statements "
                "WHERE account_id = :aid AND tenant_id = :tid AND is_reconciled = false ORDER BY trans_date DESC",
                {"aid": account_id, "tid": tenant_id}
            )
            return [{"statement_id": r[0], "trans_date": r[1], "description": r[2],
                    "debit": float(r[3] or 0), "credit": float(r[4] or 0), "balance": float(r[5])} for r in result.fetchall()]
