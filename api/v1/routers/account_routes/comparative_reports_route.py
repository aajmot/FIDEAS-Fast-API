from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from datetime import datetime
from api.schemas.common import BaseResponse
from api.middleware.auth_middleware import get_current_user
from core.database.connection import db_manager
from modules.account_module.models.entities import AccountMaster, AccountGroup, Ledger, Budget
from modules.admin_module.models.entities import FinancialYear
from sqlalchemy import func, and_

router = APIRouter()

@router.get("/comparative-pl", response_model=BaseResponse)
async def get_comparative_profit_loss(
    period1_start: str = Query(...),
    period1_end: str = Query(...),
    period2_start: str = Query(...),
    period2_end: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """Compare Profit & Loss between two periods"""
    with db_manager.get_session() as session:
        def get_pl_data(start_date, end_date):
            query = session.query(
                AccountMaster.name,
                AccountGroup.account_type,
                func.sum(Ledger.debit_amount).label('debit'),
                func.sum(Ledger.credit_amount).label('credit')
            ).join(AccountGroup).join(Ledger).filter(
                AccountMaster.tenant_id == current_user['tenant_id'],
                AccountGroup.account_type.in_(['INCOME', 'EXPENSE']),
                Ledger.transaction_date >= datetime.fromisoformat(start_date),
                Ledger.transaction_date <= datetime.fromisoformat(end_date)
            ).group_by(AccountMaster.name, AccountGroup.account_type).all()
            
            income = sum((r.credit - r.debit) for r in query if r.account_type == 'INCOME')
            expense = sum((r.debit - r.credit) for r in query if r.account_type == 'EXPENSE')
            return {'income': float(income), 'expense': float(expense), 'profit': float(income - expense)}
        
        period1 = get_pl_data(period1_start, period1_end)
        period2 = get_pl_data(period2_start, period2_end)
        
        return BaseResponse(
            success=True,
            message="Comparative P&L retrieved",
            data={
                'period1': period1,
                'period2': period2,
                'variance': {
                    'income': period2['income'] - period1['income'],
                    'expense': period2['expense'] - period1['expense'],
                    'profit': period2['profit'] - period1['profit']
                },
                'variance_percent': {
                    'income': ((period2['income'] - period1['income']) / period1['income'] * 100) if period1['income'] else 0,
                    'expense': ((period2['expense'] - period1['expense']) / period1['expense'] * 100) if period1['expense'] else 0,
                    'profit': ((period2['profit'] - period1['profit']) / period1['profit'] * 100) if period1['profit'] else 0
                }
            }
        )

@router.get("/budget-vs-actual", response_model=BaseResponse)
async def get_budget_vs_actual(
    fiscal_year_id: Optional[int] = Query(None),
    account_id: Optional[int] = Query(None),
    cost_center_id: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Compare Budget vs Actual spending"""
    with db_manager.get_session() as session:
        query = session.query(
            Budget.id,
            Budget.name,
            AccountMaster.name.label('account_name'),
            Budget.budget_amount,
            FinancialYear.start_date,
            FinancialYear.end_date
        ).join(AccountMaster).join(FinancialYear).filter(
            Budget.tenant_id == current_user['tenant_id']
        )
        
        if fiscal_year_id:
            query = query.filter(Budget.fiscal_year_id == fiscal_year_id)
        if account_id:
            query = query.filter(Budget.account_id == account_id)
        if cost_center_id:
            query = query.filter(Budget.cost_center_id == cost_center_id)
        
        budgets = query.all()
        results = []
        
        for budget in budgets:
            actual = session.query(
                func.coalesce(func.sum(Ledger.debit_amount), 0) - func.coalesce(func.sum(Ledger.credit_amount), 0)
            ).join(AccountMaster).filter(
                AccountMaster.id == budget.id,
                Ledger.transaction_date >= budget.start_date,
                Ledger.transaction_date <= budget.end_date,
                Ledger.tenant_id == current_user['tenant_id']
            ).scalar() or 0
            
            variance = float(budget.budget_amount) - float(actual)
            variance_percent = (variance / float(budget.budget_amount) * 100) if budget.budget_amount else 0
            
            results.append({
                'budget_name': budget.name,
                'account': budget.account_name,
                'budget_amount': float(budget.budget_amount),
                'actual_amount': float(actual),
                'variance': variance,
                'variance_percent': variance_percent,
                'status': 'Under Budget' if variance > 0 else 'Over Budget'
            })
        
        return BaseResponse(
            success=True,
            message="Budget vs Actual retrieved",
            data=results
        )

@router.get("/year-over-year", response_model=BaseResponse)
async def get_year_over_year(
    account_type: str = Query(..., regex="^(INCOME|EXPENSE|ASSET|LIABILITY)$"),
    current_user: dict = Depends(get_current_user)
):
    """Year-over-year comparison for last 3 years"""
    with db_manager.get_session() as session:
        current_year = datetime.now().year
        years_data = []
        
        for year in range(current_year - 2, current_year + 1):
            start = datetime(year, 1, 1)
            end = datetime(year, 12, 31)
            
            total = session.query(
                func.coalesce(func.sum(Ledger.debit_amount), 0) - func.coalesce(func.sum(Ledger.credit_amount), 0)
            ).join(AccountMaster).join(AccountGroup).filter(
                AccountGroup.account_type == account_type,
                Ledger.transaction_date >= start,
                Ledger.transaction_date <= end,
                Ledger.tenant_id == current_user['tenant_id']
            ).scalar() or 0
            
            years_data.append({'year': year, 'amount': float(total)})
        
        return BaseResponse(
            success=True,
            message="Year-over-year data retrieved",
            data=years_data
        )
