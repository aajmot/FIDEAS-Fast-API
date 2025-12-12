from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List
import math
from datetime import datetime
from api.schemas.common import PaginatedResponse, BaseResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user
from modules.account_module.services.ledger_service import LedgerService
from modules.account_module.models.ledger_schemas import LedgerResponse, LedgerSummary, BookType
from core.database.connection import db_manager
from modules.account_module.models.ledger_entity import Ledger
from modules.account_module.models.entities import Voucher, AccountMaster, VoucherType
from sqlalchemy import or_, and_

router = APIRouter()
ledger_service = LedgerService()


@router.get("/ledger", response_model=PaginatedResponse)
async def get_ledger(
    pagination: PaginationParams = Depends(),
    account_id: Optional[int] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    is_reconciled: Optional[bool] = Query(None),
    reference_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    filters = {}
    if account_id:
        filters['account_id'] = account_id
    if from_date:
        try:
            filters['from_date'] = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
        except ValueError:
            pass
    if to_date:
        try:
            filters['to_date'] = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
        except ValueError:
            pass
    if is_reconciled is not None:
        filters['is_reconciled'] = is_reconciled
    if reference_type:
        filters['reference_type'] = reference_type
    
    pagination_params = {
        'offset': pagination.offset,
        'per_page': pagination.per_page
    }
    
    entries, total = ledger_service.get_ledger_entries(filters, pagination_params)
    
    ledger_data = []
    for entry in entries:
        ledger_data.append({
            "id": entry['id'],
            "account_id": entry['account_id'],
            "account_name": entry['account_name'],
            "voucher_id": entry['voucher_id'],
            "voucher_number": entry['voucher_number'],
            "voucher_type": entry['voucher_type'],
            "transaction_date": entry['transaction_date'].isoformat() if entry['transaction_date'] else None,
            "debit_amount": float(entry['debit_amount']),
            "credit_amount": float(entry['credit_amount']),
            "balance": float(entry['balance']),
            "narration": entry['narration'],
            "reference_type": entry['reference_type'],
            "reference_number": entry['reference_number'],
            "is_reconciled": entry['is_reconciled'],
            "currency_id": entry['currency_id'],
            "debit_foreign": float(entry['debit_foreign']) if entry['debit_foreign'] else None,
            "credit_foreign": float(entry['credit_foreign']) if entry['credit_foreign'] else None
        })
    
    return PaginatedResponse(
        success=True,
        message="Ledger retrieved successfully",
        data=ledger_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page) if total > 0 else 0
    )


@router.get("/ledger/summary", response_model=BaseResponse)
async def get_ledger_summary(
    account_id: Optional[int] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    filters = {}
    if account_id:
        filters['account_id'] = account_id
    if from_date:
        try:
            filters['from_date'] = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
        except ValueError:
            pass
    if to_date:
        try:
            filters['to_date'] = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
        except ValueError:
            pass
    
    summary = ledger_service.get_ledger_summary(filters)
    
    return BaseResponse(
        success=True,
        message="Ledger summary retrieved successfully",
        data=summary
    )


@router.post("/ledger/recalculate-balances", response_model=BaseResponse)
async def recalculate_ledger_balances(current_user: dict = Depends(get_current_user)):
    try:
        result = ledger_service.recalculate_all_balances()
        return BaseResponse(
            success=True,
            message=f"Recalculated {result['updated_accounts']} accounts and {result['updated_entries']} ledger entries",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to recalculate balances: {str(e)}")


@router.post("/ledger/reconcile", response_model=BaseResponse)
async def reconcile_ledger_entries(
    ledger_ids: List[int],
    reconciliation_ref: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    try:
        count = ledger_service.mark_reconciled(ledger_ids, reconciliation_ref)
        return BaseResponse(
            success=True,
            message=f"Marked {count} ledger entries as reconciled",
            data={"reconciled_count": count}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reconcile entries: {str(e)}")


@router.get("/ledger/account/{account_id}", response_model=PaginatedResponse)
async def get_account_ledger(
    account_id: int,
    pagination: PaginationParams = Depends(),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    filters = {'account_id': account_id}
    if from_date:
        try:
            filters['from_date'] = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
        except ValueError:
            pass
    if to_date:
        try:
            filters['to_date'] = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
        except ValueError:
            pass
    
    pagination_params = {
        'offset': pagination.offset,
        'per_page': pagination.per_page
    }
    
    entries, total = ledger_service.get_ledger_entries(filters, pagination_params)
    
    ledger_data = []
    for entry in entries:
        ledger_data.append({
            "id": entry['id'],
            "transaction_date": entry['transaction_date'].isoformat(),
            "voucher_number": entry['voucher_number'],
            "debit_amount": float(entry['debit_amount']),
            "credit_amount": float(entry['credit_amount']),
            "balance": float(entry['balance']),
            "narration": entry['narration']
        })
    
    return PaginatedResponse(
        success=True,
        message="Account ledger retrieved successfully",
        data=ledger_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page) if total > 0 else 0
    )


@router.get("/books", response_model=PaginatedResponse)
async def get_books(
    book_type: BookType = Query(..., description="Book type: DAILY_BOOK, CASH_BOOK, PETTY_CASH_BOOK"),
    pagination: PaginationParams = Depends(),
    account_id: Optional[int] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    reference_type: Optional[str] = Query(None),
    voucher_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get book entries - Daily Book, Cash Book, or Petty Cash Book"""
    
    filters = {}
    if account_id:
        filters['account_id'] = account_id
    if from_date:
        try:
            filters['from_date'] = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
        except ValueError:
            pass
    if to_date:
        try:
            filters['to_date'] = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
        except ValueError:
            pass
    if reference_type:
        filters['reference_type'] = reference_type
    if voucher_type:
        filters['voucher_type'] = voucher_type
    
    pagination_params = {
        'offset': pagination.offset,
        'per_page': pagination.per_page
    }
    
    entries, total = ledger_service.get_book_entries(book_type.value, filters, pagination_params)
    
    book_data = []
    for entry in entries:
        book_data.append({
            "id": entry['id'],
            "account_id": entry['account_id'],
            "account_name": entry['account_name'],
            "account_code": entry['account_code'],
            "voucher_id": entry['voucher_id'],
            "voucher_number": entry['voucher_number'],
            "voucher_type": entry['voucher_type'],
            "voucher_type_code": entry['voucher_type_code'],
            "transaction_date": entry['transaction_date'].isoformat() if entry['transaction_date'] else None,
            "posting_date": entry['posting_date'].isoformat() if entry['posting_date'] else None,
            "debit_amount": float(entry['debit_amount']),
            "credit_amount": float(entry['credit_amount']),
            "balance": float(entry['balance']),
            "narration": entry['narration'],
            "reference_type": entry['reference_type'],
            "reference_number": entry['reference_number'],
            "currency_id": entry['currency_id'],
            "debit_foreign": float(entry['debit_foreign']) if entry['debit_foreign'] else None,
            "credit_foreign": float(entry['credit_foreign']) if entry['credit_foreign'] else None
        })
    
    book_name = book_type.value.replace('_', ' ').title()
    return PaginatedResponse(
        success=True,
        message=f"{book_name} retrieved successfully",
        data=book_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page) if total > 0 else 0
    )
