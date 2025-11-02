from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from api.schemas.common import BaseResponse
from api.middleware.auth_middleware import get_current_user
from sqlalchemy import func
import math
from datetime import datetime

router = APIRouter()


@router.get("/trial-balance", response_model=BaseResponse)
async def get_trial_balance(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import AccountMaster, AccountGroup, Ledger

    with db_manager.get_session() as session:
        query = session.query(
            AccountMaster.id,
            AccountMaster.name,
            AccountMaster.code,
            AccountGroup.account_type,
            func.sum(Ledger.debit_amount).label('total_debit'),
            func.sum(Ledger.credit_amount).label('total_credit')
        ).join(AccountGroup).outerjoin(Ledger).filter(
            AccountMaster.tenant_id == current_user['tenant_id']
        )

        if from_date:
            query = query.filter(Ledger.transaction_date >= datetime.fromisoformat(from_date))
        if to_date:
            query = query.filter(Ledger.transaction_date <= datetime.fromisoformat(to_date))

        query = query.group_by(AccountMaster.id, AccountMaster.name, AccountMaster.code, AccountGroup.account_type)

        results = query.all()

        trial_balance_data = []
        grand_total_debit = 0
        grand_total_credit = 0

        for row in results:
            debit = float(row.total_debit or 0)
            credit = float(row.total_credit or 0)
            balance = debit - credit

            trial_balance_data.append({
                "account_id": row.id,
                "account_name": row.name,
                "account_code": row.code,
                "account_type": row.account_type,
                "debit": debit,
                "credit": credit,
                "balance": balance
            })

            grand_total_debit += debit
            grand_total_credit += credit

        return BaseResponse(
            success=True,
            message="Trial balance retrieved successfully",
            data={
                "accounts": trial_balance_data,
                "grand_total_debit": grand_total_debit,
                "grand_total_credit": grand_total_credit,
                "difference": grand_total_debit - grand_total_credit
            }
        )


@router.get("/profit-loss", response_model=BaseResponse)
async def get_profit_loss(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import AccountMaster, AccountGroup, Ledger

    with db_manager.get_session() as session:
        query = session.query(
            AccountMaster.name,
            AccountGroup.account_type,
            func.sum(Ledger.debit_amount).label('total_debit'),
            func.sum(Ledger.credit_amount).label('total_credit')
        ).join(AccountGroup).join(Ledger).filter(
            AccountMaster.tenant_id == current_user['tenant_id'],
            AccountGroup.account_type.in_(['INCOME', 'EXPENSE'])
        )

        if from_date:
            query = query.filter(Ledger.transaction_date >= datetime.fromisoformat(from_date))
        if to_date:
            query = query.filter(Ledger.transaction_date <= datetime.fromisoformat(to_date))

        query = query.group_by(AccountMaster.name, AccountGroup.account_type)

        results = query.all()

        income_accounts = []
        expense_accounts = []
        total_income = 0
        total_expense = 0

        for row in results:
            debit = float(row.total_debit or 0)
            credit = float(row.total_credit or 0)

            if row.account_type == 'INCOME':
                amount = credit - debit
                income_accounts.append({"name": row.name, "amount": amount})
                total_income += amount
            else:
                amount = debit - credit
                expense_accounts.append({"name": row.name, "amount": amount})
                total_expense += amount

        net_profit = total_income - total_expense

        return BaseResponse(
            success=True,
            message="Profit & Loss statement retrieved successfully",
            data={
                "income": income_accounts,
                "expenses": expense_accounts,
                "total_income": total_income,
                "total_expense": total_expense,
                "net_profit": net_profit
            }
        )


@router.get("/cash-flow", response_model=BaseResponse)
async def get_cash_flow(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Payment

    with db_manager.get_session() as session:
        query = session.query(Payment).filter(
            Payment.tenant_id == current_user['tenant_id']
        )

        if from_date:
            query = query.filter(Payment.payment_date >= datetime.fromisoformat(from_date))
        if to_date:
            query = query.filter(Payment.payment_date <= datetime.fromisoformat(to_date))

        payments = query.all()

        cash_inflows = []
        cash_outflows = []
        total_inflows = 0
        total_outflows = 0

        for payment in payments:
            amount = float(payment.amount or 0)
            if payment.payment_mode == 'RECEIVED':
                cash_inflows.append({"description": payment.remarks or payment.reference_type, "amount": amount})
                total_inflows += amount
            else:
                cash_outflows.append({"description": payment.remarks or payment.reference_type, "amount": amount})
                total_outflows += amount

        net_cash_flow = total_inflows - total_outflows

        return BaseResponse(
            success=True,
            message="Cash flow statement retrieved successfully",
            data={
                "inflows": cash_inflows,
                "outflows": cash_outflows,
                "total_inflows": total_inflows,
                "total_outflows": total_outflows,
                "net_cash_flow": net_cash_flow
            }
        )


@router.get("/balance-sheet", response_model=BaseResponse)
async def get_balance_sheet(
    as_of_date: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import AccountMaster, AccountGroup, Ledger

    with db_manager.get_session() as session:
        query = session.query(
            AccountMaster.name,
            AccountGroup.account_type,
            func.sum(Ledger.debit_amount).label('total_debit'),
            func.sum(Ledger.credit_amount).label('total_credit')
        ).join(AccountGroup).outerjoin(Ledger).filter(
            AccountMaster.tenant_id == current_user['tenant_id'],
            AccountGroup.account_type.in_(['ASSET', 'LIABILITY', 'EQUITY'])
        )

        if as_of_date:
            query = query.filter(Ledger.transaction_date <= datetime.fromisoformat(as_of_date))

        query = query.group_by(AccountMaster.name, AccountGroup.account_type)

        results = query.all()

        assets = []
        liabilities = []
        equity = []
        total_assets = 0
        total_liabilities = 0
        total_equity = 0

        for row in results:
            debit = float(row.total_debit or 0)
            credit = float(row.total_credit or 0)
            balance = debit - credit

            if row.account_type == 'ASSET':
                assets.append({"name": row.name, "amount": balance})
                total_assets += balance
            elif row.account_type == 'LIABILITY':
                liabilities.append({"name": row.name, "amount": -balance})
                total_liabilities += -balance
            else:
                equity.append({"name": row.name, "amount": -balance})
                total_equity += -balance

        return BaseResponse(
            success=True,
            message="Balance sheet retrieved successfully",
            data={
                "assets": assets,
                "liabilities": liabilities,
                "equity": equity,
                "total_assets": total_assets,
                "total_liabilities": total_liabilities,
                "total_equity": total_equity,
                "total_liabilities_equity": total_liabilities + total_equity
            }
        )
