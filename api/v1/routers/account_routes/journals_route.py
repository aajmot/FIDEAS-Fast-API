from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import math
from api.schemas.common import PaginatedResponse, BaseResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.get("/journal-entries", response_model=PaginatedResponse)
async def get_journal_entries(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Journal, Voucher
    from sqlalchemy import or_

    with db_manager.get_session() as session:
        query = session.query(Journal).join(Voucher).filter(
            Journal.tenant_id == current_user['tenant_id']
        )

        if pagination.search:
            query = query.filter(
                Voucher.voucher_number.ilike(f"%{pagination.search}%")
            )

        query = query.order_by(Voucher.voucher_date.desc(), Journal.id.desc())

        total = query.count()
        journals = query.offset(pagination.offset).limit(pagination.per_page).all()

        entry_data = [{
            "id": journal.id,
            "date": journal.voucher.voucher_date.isoformat() if journal.voucher.voucher_date else None,
            "voucher_number": journal.voucher.voucher_number or "",
            "description": journal.voucher.narration or "",
            "total_amount": float(journal.total_debit or 0),
            "status": "Posted" if journal.voucher.is_posted else "Draft"
        } for journal in journals]

    return PaginatedResponse(
        success=True,
        message="Journal entries retrieved successfully",
        data=entry_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )


@router.post("/journal-entries", response_model=BaseResponse)
async def create_journal_entry(entry_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Voucher, VoucherType, Journal, JournalDetail, Ledger
    from modules.account_module.services.validation_service import ValidationService
    from modules.account_module.services.audit_service import AuditService
    from datetime import datetime
    from sqlalchemy import func

    with db_manager.get_session() as session:
        try:
            ValidationService.validate_financial_year(
                session,
                datetime.fromisoformat(entry_data['date']),
                current_user['tenant_id']
            )

            voucher_type = session.query(VoucherType).filter(
                VoucherType.code == 'JV',
                VoucherType.tenant_id == current_user['tenant_id']
            ).first()

            if not voucher_type:
                voucher_type = VoucherType(
                    name='Journal',
                    code='JV',
                    prefix='JV-',
                    tenant_id=current_user['tenant_id']
                )
                session.add(voucher_type)
                session.flush()

            voucher = Voucher(
                voucher_number=entry_data['voucher_number'],
                voucher_type_id=voucher_type.id,
                voucher_date=datetime.fromisoformat(entry_data['date']),
                narration=entry_data.get('description', ''),
                total_amount=entry_data['total_amount'],
                is_posted=entry_data.get('is_posted', False),
                tenant_id=current_user['tenant_id'],
                created_by=current_user['username']
            )
            session.add(voucher)
            session.flush()

            journal = Journal(
                voucher_id=voucher.id,
                journal_date=datetime.fromisoformat(entry_data['date']),
                total_debit=entry_data['total_amount'],
                total_credit=entry_data['total_amount'],
                tenant_id=current_user['tenant_id']
            )
            session.add(journal)
            session.flush()

            for line in entry_data['lines']:
                if line['account_id'] and (line['debit'] or line['credit']):
                    journal_detail = JournalDetail(
                        journal_id=journal.id,
                        account_id=line['account_id'],
                        debit_amount=line['debit'],
                        credit_amount=line['credit'],
                        narration=line.get('description', ''),
                        tenant_id=current_user['tenant_id']
                    )
                    session.add(journal_detail)

                    current_balance = float(ValidationService.calculate_ledger_balance(
                        session, line['account_id'], datetime.fromisoformat(entry_data['date']), current_user['tenant_id']
                    ))
                    new_balance = current_balance + float(line['debit'] or 0) - float(line['credit'] or 0)

                    ledger_entry = Ledger(
                        account_id=line['account_id'],
                        voucher_id=voucher.id,
                        transaction_date=datetime.fromisoformat(entry_data['date']),
                        debit_amount=line['debit'],
                        credit_amount=line['credit'],
                        balance=new_balance,
                        narration=line.get('description', ''),
                        tenant_id=current_user['tenant_id']
                    )
                    session.add(ledger_entry)

            session.flush()

            from modules.account_module.models.entities import AccountMaster
            for line in entry_data['lines']:
                if line['account_id'] and (line['debit'] or line['credit']):
                    account = session.query(AccountMaster).with_for_update().filter(
                        AccountMaster.id == line['account_id']
                    ).first()
                    if account:
                        total_balance = session.query(
                            func.coalesce(func.sum(Ledger.debit_amount), 0) - func.coalesce(func.sum(Ledger.credit_amount), 0)
                        ).filter(
                            Ledger.account_id == line['account_id'],
                            Ledger.tenant_id == current_user['tenant_id']
                        ).scalar() or 0
                        account.current_balance = float(total_balance)

            AuditService.log_action(
                session, 'JOURNAL', journal.id, 'CREATE',
                new_value={'voucher_number': voucher.voucher_number, 'amount': float(journal.total_debit)}
            )

            session.commit()

            return BaseResponse(
                success=True,
                message="Journal entry created successfully",
                data={"id": journal.id}
            )

        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))


@router.post("/journal-entries/{journal_id}/post", response_model=BaseResponse)
async def post_journal_entry(journal_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Journal, Voucher

    with db_manager.get_session() as session:
        try:
            journal = session.query(Journal).filter(
                Journal.id == journal_id,
                Journal.tenant_id == current_user['tenant_id']
            ).first()

            if not journal:
                raise HTTPException(status_code=404, detail="Journal entry not found")

            if journal.voucher:
                journal.voucher.is_posted = True
                session.commit()

            return BaseResponse(
                success=True,
                message="Journal entry posted successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))


@router.post("/journal-entries/{journal_id}/unpost", response_model=BaseResponse)
async def unpost_journal_entry(journal_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Journal, Voucher

    with db_manager.get_session() as session:
        try:
            journal = session.query(Journal).filter(
                Journal.id == journal_id,
                Journal.tenant_id == current_user['tenant_id']
            ).first()

            if not journal:
                raise HTTPException(status_code=404, detail="Journal entry not found")

            if journal.voucher:
                journal.voucher.is_posted = False
                session.commit()

            return BaseResponse(
                success=True,
                message="Journal entry unposted successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))


@router.delete("/journal-entries/{journal_id}", response_model=BaseResponse)
async def delete_journal_entry(journal_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Journal, Voucher

    with db_manager.get_session() as session:
        try:
            journal = session.query(Journal).filter(
                Journal.id == journal_id,
                Journal.tenant_id == current_user['tenant_id']
            ).first()

            if not journal:
                raise HTTPException(status_code=404, detail="Journal entry not found")

            if journal.voucher and journal.voucher.is_posted:
                raise HTTPException(status_code=400, detail="Cannot delete posted journal entry. Please unpost it first.")

            if journal.voucher:
                journal.voucher.is_deleted = True
                session.commit()

            return BaseResponse(
                success=True,
                message="Journal entry deleted successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))
