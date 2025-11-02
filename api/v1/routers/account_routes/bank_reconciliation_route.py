from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import math
from api.schemas.common import PaginatedResponse, BaseResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.get("/bank-reconciliations", response_model=PaginatedResponse)
async def get_bank_reconciliations(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import BankReconciliation, AccountMaster

    with db_manager.get_session() as session:
        query = session.query(BankReconciliation).join(AccountMaster).filter(
            BankReconciliation.tenant_id == current_user['tenant_id']
        ).order_by(BankReconciliation.statement_date.desc())

        total = query.count()
        reconciliations = query.offset(pagination.offset).limit(pagination.per_page).all()

        recon_data = [{
            "id": recon.id,
            "bank_account_name": recon.bank_account.name,
            "statement_date": recon.statement_date.isoformat(),
            "statement_balance": float(recon.statement_balance),
            "book_balance": float(recon.book_balance),
            "reconciled_balance": float(recon.reconciled_balance),
            "status": recon.status,
            "difference": float(recon.statement_balance - recon.book_balance)
        } for recon in reconciliations]

    return PaginatedResponse(
        success=True,
        message="Bank reconciliations retrieved successfully",
        data=recon_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )


@router.post("/bank-reconciliations", response_model=BaseResponse)
async def create_bank_reconciliation(recon_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import BankReconciliation, Ledger
    from datetime import datetime
    from sqlalchemy import func

    with db_manager.get_session() as session:
        try:
            book_balance = session.query(
                func.coalesce(func.sum(Ledger.debit_amount), 0) - func.coalesce(func.sum(Ledger.credit_amount), 0)
            ).filter(
                Ledger.account_id == recon_data['bank_account_id'],
                Ledger.transaction_date <= datetime.fromisoformat(recon_data['statement_date']),
                Ledger.tenant_id == current_user['tenant_id']
            ).scalar() or 0

            recon = BankReconciliation(
                bank_account_id=recon_data['bank_account_id'],
                statement_date=datetime.fromisoformat(recon_data['statement_date']).date(),
                statement_balance=recon_data['statement_balance'],
                book_balance=float(book_balance),
                tenant_id=current_user['tenant_id'],
                created_by=current_user['username']
            )
            session.add(recon)
            session.flush()
            recon_id = recon.id
            session.commit()

            return BaseResponse(
                success=True,
                message="Bank reconciliation created successfully",
                data={"id": recon_id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))


@router.get("/bank-reconciliations/{recon_id}/unmatched-items", response_model=BaseResponse)
async def get_unmatched_items(recon_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import BankReconciliation, Ledger, BankReconciliationItem

    with db_manager.get_session() as session:
        recon = session.query(BankReconciliation).filter(
            BankReconciliation.id == recon_id,
            BankReconciliation.tenant_id == current_user['tenant_id']
        ).first()

        if not recon:
            raise HTTPException(status_code=404, detail="Reconciliation not found")

        matched_ledger_ids = session.query(BankReconciliationItem.ledger_id).filter(
            BankReconciliationItem.reconciliation_id == recon_id,
            BankReconciliationItem.is_matched == True
        ).all()
        matched_ids = [lid[0] for lid in matched_ledger_ids if lid[0]]

        unmatched = session.query(Ledger).filter(
            Ledger.account_id == recon.bank_account_id,
            Ledger.transaction_date <= recon.statement_date,
            Ledger.id.notin_(matched_ids) if matched_ids else True,
            Ledger.tenant_id == current_user['tenant_id']
        ).all()

        items = [{
            "ledger_id": entry.id,
            "date": entry.transaction_date.isoformat(),
            "description": entry.narration,
            "debit": float(entry.debit_amount),
            "credit": float(entry.credit_amount),
            "amount": float(entry.debit_amount - entry.credit_amount)
        } for entry in unmatched]

        return BaseResponse(
            success=True,
            message="Unmatched items retrieved successfully",
            data={"items": items}
        )


@router.post("/bank-reconciliations/{recon_id}/match", response_model=BaseResponse)
async def match_reconciliation_item(recon_id: int, match_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import BankReconciliationItem
    from datetime import datetime

    with db_manager.get_session() as session:
        try:
            item = BankReconciliationItem(
                reconciliation_id=recon_id,
                ledger_id=match_data.get('ledger_id'),
                statement_amount=match_data['statement_amount'],
                statement_date=datetime.fromisoformat(match_data['statement_date']).date(),
                statement_reference=match_data.get('statement_reference'),
                is_matched=True,
                match_type=match_data.get('match_type', 'MANUAL'),
                tenant_id=current_user['tenant_id']
            )
            session.add(item)
            session.commit()

            return BaseResponse(
                success=True,
                message="Item matched successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))
