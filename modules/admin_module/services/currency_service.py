from typing import List, Dict
from datetime import datetime
from core.database.connection import db_manager
# import ORM models (adjust path if your models are located elsewhere)
from modules.account_module.models.entities import Voucher
from modules.admin_module.models.currency import Currency, ExchangeRate

class CurrencyService:
    @staticmethod
    def get_currencies(tenant_id: int) -> List[Dict]:
        with db_manager.get_session() as session:
            # ORM query replacing raw SQL
            currencies = (
                session.query(Currency)
                .filter(Currency.is_active == True)
                .order_by(Currency.is_base.desc(), Currency.code)
                .all()
            )
            # attempt to fetch a tenant-specific latest exchange rate to the base currency
            base_currency = session.query(Currency).filter(Currency.is_base == True).one_or_none()
            results = []
            for c in currencies:
                current_rate = None
                if base_currency and c.id != base_currency.id:
                    er = (
                        session.query(ExchangeRate)
                        .filter(
                            ExchangeRate.from_currency_id == c.id,
                            ExchangeRate.to_currency_id == base_currency.id,
                            ExchangeRate.tenant_id == tenant_id,
                        )
                        .order_by(ExchangeRate.effective_date.desc())
                        .first()
                    )
                    if er:
                        current_rate = float(er.rate)

                results.append({
                    "currency_id": c.id,
                    "currency_code": c.code,
                    "currency_name": c.name,
                    "symbol": c.symbol,
                    "exchange_rate": current_rate,
                    "is_base": c.is_base,
                })

            return results

    @staticmethod
    def convert_amount(amount: float, from_currency_id: int, to_currency_id: int, tenant_id: int) -> float:
        with db_manager.get_session() as session:
            # Find the latest exchange rate from 'from_currency' -> 'to_currency' for the tenant
            er = (
                session.query(ExchangeRate)
                .filter(
                    ExchangeRate.from_currency_id == from_currency_id,
                    ExchangeRate.to_currency_id == to_currency_id,
                    ExchangeRate.tenant_id == tenant_id,
                )
                .order_by(ExchangeRate.effective_date.desc())
                .first()
            )

            if not er or er.rate in (0, None):
                return 0.0

            return amount * float(er.rate)

    @staticmethod
    def update_exchange_rate(currency_id: int, rate: float, tenant_id: int):
        with db_manager.get_session() as session:
            # update via ORM
            # create a new exchange rate record for today to keep history
            from datetime import date

            base_currency = session.query(Currency).filter(Currency.is_base == True).one_or_none()
            if not base_currency:
                return

            er = ExchangeRate(
                from_currency_id=currency_id,
                to_currency_id=base_currency.id,
                rate=rate,
                effective_date=date.today(),
                tenant_id=tenant_id,
            )
            session.add(er)
            # session commit handled by db_manager context manager

    @staticmethod
    def calculate_forex_gain_loss(voucher_id: int, tenant_id: int) -> float:
        with db_manager.get_session() as session:
            # join vouchers and currencies via ORM to compute gain/loss
            row = (
                session.query(Voucher.total_amount, Voucher.currency_id, Voucher.exchange_rate)
                .filter(Voucher.id == voucher_id, Voucher.tenant_id == tenant_id)
                .one_or_none()
            )
            if not row:
                return 0.0

            amount = float(row.total_amount or 0.0)
            original_rate = float(row.exchange_rate or 0.0)

            # find current rate to base currency
            base_currency = session.query(Currency).filter(Currency.is_base == True).one_or_none()
            if not base_currency:
                return 0.0

            er = (
                session.query(ExchangeRate)
                .filter(
                    ExchangeRate.from_currency_id == row.currency_id,
                    ExchangeRate.to_currency_id == base_currency.id,
                    ExchangeRate.tenant_id == tenant_id,
                )
                .order_by(ExchangeRate.effective_date.desc())
                .first()
            )

            current_rate = float(er.rate) if er and er.rate is not None else 0.0

            return amount * current_rate - amount * original_rate
