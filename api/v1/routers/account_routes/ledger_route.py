from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
import math
from api.schemas.common import PaginatedResponse, BaseResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.get("/ledger", response_model=PaginatedResponse)
async def get_ledger(
    pagination: PaginationParams = Depends(),
    account_id: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    voucher_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Ledger, Voucher, AccountMaster, VoucherType
    from sqlalchemy import or_
    from datetime import datetime

    with db_manager.get_session() as session:
        query = session.query(Ledger).join(Voucher).join(AccountMaster).join(VoucherType, Voucher.voucher_type_id == VoucherType.id).filter(
            Ledger.tenant_id == current_user['tenant_id']
        )

        if account_id and account_id.strip():
            try:
                query = query.filter(Ledger.account_id == int(account_id))
            except ValueError:
                pass

        if from_date and from_date.strip():
            try:
                from_dt = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
                query = query.filter(Ledger.transaction_date >= from_dt)
            except ValueError:
                pass

        if to_date and to_date.strip():
            try:
                to_dt = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
                query = query.filter(Ledger.transaction_date <= to_dt)
            except ValueError:
                pass

        if voucher_type and voucher_type.strip():
            query = query.filter(VoucherType.name.ilike(f"%{voucher_type}%"))

        if pagination.search:
            query = query.filter(or_(
                Voucher.voucher_number.ilike(f"%{pagination.search}%"),
                AccountMaster.name.ilike(f"%{pagination.search}%"),
                Ledger.narration.ilike(f"%{pagination.search}%")
            ))

        query = query.order_by(Ledger.transaction_date.desc(), Ledger.id.desc())

        total = query.count()
        ledger_entries = query.offset(pagination.offset).limit(pagination.per_page).all()

        ledger_data = []
        for entry in ledger_entries:
            try:
                debit_amount = float(entry.debit_amount) if entry.debit_amount is not None else 0.0
                credit_amount = float(entry.credit_amount) if entry.credit_amount is not None else 0.0
                balance_amount = float(entry.balance) if entry.balance is not None else 0.0

                ledger_data.append({
                    "id": entry.id,
                    "date": entry.transaction_date.isoformat() if entry.transaction_date else None,
                    "voucher_type": entry.voucher.voucher_type.name if entry.voucher and entry.voucher.voucher_type else "",
                    "voucher_number": entry.voucher.voucher_number if entry.voucher else "",
                    "voucher_id": entry.voucher_id if entry.voucher_id else None,
                    "description": entry.narration or "",
                    "debit": debit_amount,
                    "credit": credit_amount,
                    "balance": balance_amount
                })
            except Exception:
                continue

    return PaginatedResponse(
        success=True,
        message="Ledger retrieved successfully",
        data=ledger_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )


@router.get("/ledger/summary", response_model=BaseResponse)
async def get_ledger_summary(
    account_id: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    voucher_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Ledger, Voucher, AccountMaster, VoucherType
    from sqlalchemy import func
    from datetime import datetime

    with db_manager.get_session() as session:
        query = session.query(
            func.sum(Ledger.debit_amount).label('total_debit'),
            func.sum(Ledger.credit_amount).label('Total_credit')
        ).join(Voucher).join(AccountMaster).join(VoucherType, Voucher.voucher_type_id == VoucherType.id).filter(
            Ledger.tenant_id == current_user['tenant_id']
        )

        if account_id and account_id.strip():
            try:
                query = query.filter(Ledger.account_id == int(account_id))
            except ValueError:
                pass

        if from_date and from_date.strip():
            try:
                from_dt = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
                query = query.filter(Ledger.transaction_date >= from_dt)
            except ValueError:
                pass

        if to_date and to_date.strip():
            try:
                to_dt = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
                query = query.filter(Ledger.transaction_date <= to_dt)
            except ValueError:
                pass

        if voucher_type and voucher_type.strip():
            query = query.filter(VoucherType.name.ilike(f"%{voucher_type}%"))

        result = query.first()
        total_debit = float(result.total_debit or 0)
        total_credit = float(result.total_credit or 0)
        closing_balance = total_debit - total_credit

        summary_data = {
            "total_debit": total_debit,
            "total_credit": total_credit,
            "closing_balance": closing_balance
        }

    return BaseResponse(
        success=True,
        message="Ledger summary retrieved successfully",
        data=summary_data
    )


@router.post("/ledger/recalculate-balances", response_model=BaseResponse)
async def recalculate_ledger_balances(current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Ledger, AccountMaster
    from sqlalchemy import func

    with db_manager.get_session() as session:
        try:
            accounts = session.query(AccountMaster).filter(
                AccountMaster.tenant_id == current_user['tenant_id']
            ).all()

            updated_accounts = 0
            updated_entries = 0

            for account in accounts:
                ledger_entries = session.query(Ledger).filter(
                    Ledger.account_id == account.id,
                    Ledger.tenant_id == current_user['tenant_id']
                ).order_by(Ledger.transaction_date.asc(), Ledger.id.asc()).all()

                running_balance = 0.0
                for entry in ledger_entries:
                    debit = float(entry.debit_amount or 0)
                    credit = float(entry.credit_amount or 0)
                    running_balance += debit - credit
                    if entry.balance != running_balance:
                        entry.balance = running_balance
                        updated_entries += 1

                if account.current_balance != running_balance:
                    account.current_balance = running_balance
                    updated_accounts += 1

            session.commit()

            return BaseResponse(
                success=True,
                message=f"Recalculated balances for {updated_accounts} accounts and {updated_entries} ledger entries"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to recalculate balances: {str(e)}")
