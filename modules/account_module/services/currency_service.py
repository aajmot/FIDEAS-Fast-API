from typing import List, Dict, Optional
from datetime import datetime
from core.database.connection import db_manager

class CurrencyService:
    @staticmethod
    def get_currencies(tenant_id: int) -> List[Dict]:
        with db_manager.get_session() as session:
            result = session.execute(
                "SELECT currency_id, currency_code, currency_name, symbol, exchange_rate, is_base "
                "FROM currencies WHERE tenant_id = :tid AND is_active = true ORDER BY is_base DESC, currency_code",
                {"tid": tenant_id}
            )
            return [{"currency_id": r[0], "currency_code": r[1], "currency_name": r[2],
                    "symbol": r[3], "exchange_rate": float(r[4]), "is_base": r[5]} for r in result.fetchall()]

    @staticmethod
    def convert_amount(amount: float, from_currency_id: int, to_currency_id: int, tenant_id: int) -> float:
        with db_manager.get_session() as session:
            from_rate = session.execute(
                "SELECT exchange_rate FROM currencies WHERE currency_id = :cid AND tenant_id = :tid",
                {"cid": from_currency_id, "tid": tenant_id}
            ).fetchone()[0]
            to_rate = session.execute(
                "SELECT exchange_rate FROM currencies WHERE currency_id = :cid AND tenant_id = :tid",
                {"cid": to_currency_id, "tid": tenant_id}
            ).fetchone()[0]
            return (amount / float(from_rate)) * float(to_rate)

    @staticmethod
    def update_exchange_rate(currency_id: int, rate: float, tenant_id: int):
        with db_manager.get_session() as session:
            session.execute(
                "UPDATE currencies SET exchange_rate = :rate, updated_at = :now WHERE currency_id = :cid AND tenant_id = :tid",
                {"rate": rate, "now": datetime.now(), "cid": currency_id, "tid": tenant_id}
            )

    @staticmethod
    def calculate_forex_gain_loss(voucher_id: int, tenant_id: int) -> float:
        with db_manager.get_session() as session:
            result = session.execute(
                "SELECT v.amount, v.currency_id, v.exchange_rate, c.exchange_rate as current_rate "
                "FROM vouchers v JOIN currencies c ON v.currency_id = c.currency_id "
                "WHERE v.voucher_id = :vid AND v.tenant_id = :tid",
                {"vid": voucher_id, "tid": tenant_id}
            )
            row = result.fetchone()
            if row:
                amount, _, original_rate, current_rate = row
                return float(amount) * float(current_rate) - float(amount) * float(original_rate)
            return 0.0
