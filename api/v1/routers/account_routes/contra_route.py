from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from core.database.connection import db_manager
from sqlalchemy import text
import math

router = APIRouter()


# Contra Voucher Endpoints
@router.post("/contra", response_model=BaseResponse)
async def create_contra(contra_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    """Create contra voucher for cash/bank transfers"""
    from modules.account_module.models.entities import Voucher, VoucherType, Ledger, AccountMaster

    with db_manager.get_session() as session:
        try:
            # Validate accounts are cash/bank type
            from_account = session.query(AccountMaster).filter(AccountMaster.id == contra_data['from_account_id']).first()
            to_account = session.query(AccountMaster).filter(AccountMaster.id == contra_data['to_account_id']).first()

            if not from_account or not to_account:
                raise HTTPException(status_code=400, detail="Invalid accounts")

            # Get Contra voucher type
            voucher_type = session.query(VoucherType).filter(
                VoucherType.code == 'CONTRA',
                VoucherType.tenant_id == current_user['tenant_id']
            ).first()

            # Create voucher
            voucher = Voucher(
                voucher_number=contra_data['voucher_number'],
                voucher_type_id=voucher_type.id,
                voucher_date=datetime.fromisoformat(contra_data['date']),
                narration=contra_data.get('narration', ''),
                total_amount=contra_data['amount'],
                is_posted=True,
                tenant_id=current_user['tenant_id'],
                created_by=current_user['username']
            )
            session.add(voucher)
            session.flush()

            # Create ledger entries (debit to_account, credit from_account)
            ledger_to = Ledger(
                account_id=contra_data['to_account_id'],
                voucher_id=voucher.id,
                transaction_date=datetime.fromisoformat(contra_data['date']),
                debit_amount=contra_data['amount'],
                credit_amount=0,
                narration=contra_data.get('narration', ''),
                tenant_id=current_user['tenant_id']
            )
            session.add(ledger_to)

            ledger_from = Ledger(
                account_id=contra_data['from_account_id'],
                voucher_id=voucher.id,
                transaction_date=datetime.fromisoformat(contra_data['date']),
                debit_amount=0,
                credit_amount=contra_data['amount'],
                narration=contra_data.get('narration', ''),
                tenant_id=current_user['tenant_id']
            )
            session.add(ledger_from)

            session.commit()

            return BaseResponse(
                success=True,
                message="Contra voucher created successfully",
                data={"id": voucher.id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))


@router.get("/contra", response_model=PaginatedResponse)
async def get_contra_vouchers(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    """Get all contra vouchers"""
    with db_manager.get_session() as session:
        result = session.execute(text("""
            SELECT v.id, v.voucher_number, v.voucher_date, v.total_amount, v.narration
            FROM vouchers v
            JOIN voucher_types vt ON v.voucher_type_id = vt.id
            WHERE vt.code = 'CONTRA' AND v.tenant_id = :tenant_id AND v.is_deleted = FALSE
            ORDER BY v.voucher_date DESC
            LIMIT :limit OFFSET :offset
        """), {"tenant_id": current_user['tenant_id'], "limit": pagination.per_page, "offset": pagination.offset})

        vouchers = [{"id": r[0], "voucher_number": r[1], "date": r[2].isoformat(), "amount": float(r[3]), "narration": r[4]} for r in result]

        total = session.execute(text("""
            SELECT COUNT(*) FROM vouchers v
            JOIN voucher_types vt ON v.voucher_type_id = vt.id
            WHERE vt.code = 'CONTRA' AND v.tenant_id = :tenant_id AND v.is_deleted = FALSE
        """), {"tenant_id": current_user['tenant_id']}).scalar()

        return PaginatedResponse(
            success=True,
            message="Contra vouchers retrieved successfully",
            data=vouchers,
            total=total,
            page=pagination.page,
            per_page=pagination.per_page,
            total_pages=math.ceil(total / pagination.per_page)
        )
