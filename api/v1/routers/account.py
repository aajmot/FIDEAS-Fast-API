from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
import io
import csv
from datetime import datetime

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from sqlalchemy import or_
import math
from api.middleware.auth_middleware import get_current_user
from modules.account_module.services.account_service import AccountService
from modules.account_module.services.voucher_service import VoucherService
from modules.account_module.services.payment_service import PaymentService
from modules.account_module.services.audit_service import AuditService
from sqlalchemy import func

router = APIRouter()

# Account endpoints
@router.get("/accounts", response_model=PaginatedResponse)
async def get_accounts(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import AccountMaster, AccountGroup
    
    with db_manager.get_session() as session:
        query = session.query(AccountMaster, AccountGroup).outerjoin(
            AccountGroup, AccountMaster.account_group_id == AccountGroup.id
        ).filter(
            AccountMaster.tenant_id == current_user['tenant_id']
        )
        
        if pagination.search:
            query = query.filter(or_(
                AccountMaster.name.ilike(f"%{pagination.search}%"),
                AccountMaster.code.ilike(f"%{pagination.search}%")
            ))
        
        total = query.count()
        results = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        account_data = [{
            "id": account.id,
            "name": account.name or "",
            "code": account.code or "",
            "account_group_id": account.account_group_id,
            "account_group_name": group.name if group else "",
            "account_type": group.account_type if group else "",
            "current_balance": float(account.current_balance or 0),
            "is_active": account.is_active
        } for account, group in results]
    
    return PaginatedResponse(
        success=True,
        message="Accounts retrieved successfully",
        data=account_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/accounts", response_model=BaseResponse)
async def create_account(account_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import AccountMaster, AccountGroup
    
    with db_manager.get_session() as session:
        try:
            account = AccountMaster(
                name=account_data['name'],
                code=account_data['code'],
                account_group_id=account_data.get('account_group_id'),
                opening_balance=account_data.get('opening_balance', 0),
                current_balance=account_data.get('current_balance', 0),
                is_active=account_data.get('is_active', True),
                tenant_id=current_user['tenant_id'],
                created_by=current_user['username']
            )
            session.add(account)
            session.flush()
            account_id = account.id
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Account created successfully",
                data={"id": account_id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.put("/accounts/{account_id}", response_model=BaseResponse)
async def update_account(account_id: int, account_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import AccountMaster
    
    with db_manager.get_session() as session:
        try:
            account = session.query(AccountMaster).filter(
                AccountMaster.id == account_id,
                AccountMaster.tenant_id == current_user['tenant_id']
            ).first()
            
            if not account:
                raise HTTPException(status_code=404, detail="Account not found")
            
            if 'name' in account_data:
                account.name = account_data['name']
            if 'code' in account_data:
                account.code = account_data['code']
            if 'account_group_id' in account_data:
                account.account_group_id = account_data['account_group_id']
            if 'opening_balance' in account_data:
                account.opening_balance = account_data['opening_balance']
            if 'current_balance' in account_data:
                account.current_balance = account_data['current_balance']
            if 'is_active' in account_data:
                account.is_active = account_data['is_active']
            
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Account updated successfully",
                data={"id": account_id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.delete("/accounts/{account_id}", response_model=BaseResponse)
async def delete_account(account_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import AccountMaster
    
    with db_manager.get_session() as session:
        try:
            account = session.query(AccountMaster).filter(
                AccountMaster.id == account_id,
                AccountMaster.tenant_id == current_user['tenant_id']
            ).first()
            
            if not account:
                raise HTTPException(status_code=404, detail="Account not found")
            
            session.delete(account)
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Account deleted successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.get("/accounts/{account_id}", response_model=BaseResponse)
async def get_account(account_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import AccountMaster
    
    with db_manager.get_session() as session:
        account = session.query(AccountMaster).filter(
            AccountMaster.id == account_id,
            AccountMaster.tenant_id == current_user['tenant_id']
        ).first()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        account_data = {
            "id": account.id,
            "name": account.name,
            "code": account.code,
            "current_balance": float(account.current_balance) if account.current_balance else 0,
            "is_active": account.is_active
        }
    
    return BaseResponse(
        success=True,
        message="Account retrieved successfully",
        data=account_data
    )

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
                # Ensure debit and credit amounts are properly converted
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
            except Exception as e:
                # Skip entries with missing relationships
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
    
    with db_manager.get_session() as session:
        query = session.query(
            func.sum(Ledger.debit_amount).label('total_debit'),
            func.sum(Ledger.credit_amount).label('total_credit')
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

@router.get("/journal-entries", response_model=PaginatedResponse)
async def get_journal_entries(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Journal, Voucher
    
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
    
    with db_manager.get_session() as session:
        try:
            # Validate fiscal year
            ValidationService.validate_fiscal_year(
                session, 
                datetime.fromisoformat(entry_data['date']), 
                current_user['tenant_id']
            )
            # Get or create Journal voucher type
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
            
            # Create voucher
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
            
            # Create journal
            journal = Journal(
                voucher_id=voucher.id,
                journal_date=datetime.fromisoformat(entry_data['date']),
                total_debit=entry_data['total_amount'],
                total_credit=entry_data['total_amount'],
                tenant_id=current_user['tenant_id']
            )
            session.add(journal)
            session.flush()
            
            # Create journal details and ledger entries
            for line in entry_data['lines']:
                if line['account_id'] and (line['debit'] or line['credit']):
                    # Journal detail
                    journal_detail = JournalDetail(
                        journal_id=journal.id,
                        account_id=line['account_id'],
                        debit_amount=line['debit'],
                        credit_amount=line['credit'],
                        narration=line.get('description', ''),
                        tenant_id=current_user['tenant_id']
                    )
                    session.add(journal_detail)
                    
                    # Use validation service for correct balance calculation
                    current_balance = float(ValidationService.calculate_ledger_balance(
                        session, line['account_id'], datetime.fromisoformat(entry_data['date']), current_user['tenant_id']
                    ))
                    new_balance = current_balance + float(line['debit'] or 0) - float(line['credit'] or 0)
                    
                    # Ledger entry with calculated balance
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
            
            # Update account balances with locking
            session.flush()
            
            from modules.account_module.models.entities import AccountMaster
            for line in entry_data['lines']:
                if line['account_id'] and (line['debit'] or line['credit']):
                    # Lock account for update
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
            
            # Log audit trail
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

# Voucher Type endpoints
@router.get("/voucher-types", response_model=PaginatedResponse)
async def get_voucher_types(current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import VoucherType
    
    with db_manager.get_session() as session:
        voucher_types = session.query(VoucherType).filter(
            VoucherType.tenant_id == current_user['tenant_id'],
            VoucherType.is_active == True
        ).all()
        
        voucher_type_data = [{
            "id": vt.id,
            "name": vt.name,
            "code": vt.code,
            "prefix": vt.prefix
        } for vt in voucher_types]
    
    return PaginatedResponse(
        success=True,
        message="Voucher types retrieved successfully",
        data=voucher_type_data,
        total=len(voucher_type_data),
        page=1,
        per_page=len(voucher_type_data),
        total_pages=1
    )

# Voucher endpoints
@router.get("/vouchers", response_model=PaginatedResponse)
async def get_vouchers(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Voucher, VoucherType
    
    with db_manager.get_session() as session:
        query = session.query(Voucher).join(VoucherType).filter(
            Voucher.tenant_id == current_user['tenant_id'],
            Voucher.is_deleted == False
        )
        
        if pagination.search:
            query = query.filter(or_(
                Voucher.voucher_number.ilike(f"%{pagination.search}%"),
                Voucher.narration.ilike(f"%{pagination.search}%")
            ))
        
        query = query.order_by(Voucher.voucher_date.desc(), Voucher.id.desc())
        
        total = query.count()
        vouchers = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        voucher_data = [{
            "id": voucher.id,
            "voucher_number": voucher.voucher_number,
            "voucher_type": voucher.voucher_type.name if voucher.voucher_type else "",
            "date": voucher.voucher_date.isoformat() if voucher.voucher_date else None,
            "amount": float(voucher.total_amount) if voucher.total_amount else 0,
            "description": voucher.narration or "",
            "created_by": voucher.created_by or "",
            "status": "Posted" if voucher.is_posted else "Draft"
        } for voucher in vouchers]
    
    return PaginatedResponse(
        success=True,
        message="Vouchers retrieved successfully",
        data=voucher_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.get("/vouchers/{voucher_id}", response_model=BaseResponse)
async def get_voucher(voucher_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Voucher, VoucherType, Ledger
    
    with db_manager.get_session() as session:
        voucher = session.query(Voucher).filter(
            Voucher.id == voucher_id,
            Voucher.tenant_id == current_user['tenant_id']
        ).first()
        
        if not voucher:
            raise HTTPException(status_code=404, detail="Voucher not found")
        
        # Get ledger entries as line items
        ledger_entries = session.query(Ledger).filter(
            Ledger.voucher_id == voucher_id,
            Ledger.tenant_id == current_user['tenant_id']
        ).all()
        
        lines = [{
            "account_id": entry.account_id,
            "debit": float(entry.debit_amount or 0),
            "credit": float(entry.credit_amount or 0),
            "description": entry.narration or ""
        } for entry in ledger_entries]
        
        voucher_data = {
            "id": voucher.id,
            "voucher_number": voucher.voucher_number,
            "voucher_type": voucher.voucher_type.name if voucher.voucher_type else "",
            "date": voucher.voucher_date.isoformat() if voucher.voucher_date else None,
            "description": voucher.narration or "",
            "amount": float(voucher.total_amount) if voucher.total_amount else 0,
            "status": "Posted" if voucher.is_posted else "Draft",
            "lines": lines
        }
    
    return BaseResponse(
        success=True,
        message="Voucher retrieved successfully",
        data=voucher_data
    )

@router.post("/vouchers", response_model=BaseResponse)
async def create_voucher(voucher_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Voucher, VoucherType, Ledger, AccountMaster
    from modules.account_module.services.validation_service import ValidationService
    
    with db_manager.get_session() as session:
        try:
            # Validate fiscal year (prevent posting to closed periods)
            from modules.account_module.services.validation_service import ValidationService
            ValidationService.validate_fiscal_year(
                session, 
                datetime.fromisoformat(voucher_data['date']), 
                current_user['tenant_id']
            )
            
            # Validate voucher lines
            ValidationService.validate_voucher_lines(voucher_data['lines'])
            # Get voucher type
            voucher_type = session.query(VoucherType).filter(
                VoucherType.name == voucher_data['voucher_type'],
                VoucherType.tenant_id == current_user['tenant_id']
            ).first()
            
            if not voucher_type:
                voucher_type = session.query(VoucherType).filter(
                    VoucherType.code == 'JV',
                    VoucherType.tenant_id == current_user['tenant_id']
                ).first()
            
            if not voucher_type:
                raise HTTPException(status_code=400, detail="Voucher type not found")
            
            # Create voucher
            voucher = Voucher(
                voucher_number=voucher_data['voucher_number'],
                voucher_type_id=voucher_type.id,
                voucher_date=datetime.fromisoformat(voucher_data['date']),
                narration=voucher_data.get('description', ''),
                total_amount=voucher_data['total_amount'],
                is_posted=voucher_data.get('is_posted', False),
                tenant_id=current_user['tenant_id'],
                created_by=current_user['username']
            )
            session.add(voucher)
            session.flush()
            
            # Create ledger entries with row-level locking
            for line in voucher_data['lines']:
                if line['account_id'] and (line['debit'] or line['credit']):
                    # Lock the account row to prevent concurrent updates
                    account = session.query(AccountMaster).with_for_update().filter(
                        AccountMaster.id == line['account_id']
                    ).first()
                    
                    if not account:
                        raise HTTPException(status_code=404, detail=f"Account {line['account_id']} not found")
                    
                    # Use validation service for correct balance calculation
                    from modules.account_module.services.validation_service import ValidationService
                    current_balance = float(ValidationService.calculate_ledger_balance(
                        session, line['account_id'], datetime.fromisoformat(voucher_data['date']), current_user['tenant_id']
                    ))
                    new_balance = current_balance + float(line['debit'] or 0) - float(line['credit'] or 0)
                    
                    ledger_entry = Ledger(
                        account_id=line['account_id'],
                        voucher_id=voucher.id,
                        transaction_date=datetime.fromisoformat(voucher_data['date']),
                        debit_amount=line['debit'],
                        credit_amount=line['credit'],
                        balance=new_balance,
                        narration=line.get('description', ''),
                        tenant_id=current_user['tenant_id']
                    )
                    session.add(ledger_entry)
                    
                    # Update account balance immediately
                    account.current_balance = new_balance
            
            session.flush()
            
            # Log audit trail
            AuditService.log_action(
                session, 'VOUCHER', voucher.id, 'CREATE',
                new_value={'voucher_number': voucher.voucher_number, 'amount': float(voucher.total_amount)}
            )
            
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Voucher created successfully",
                data={"id": voucher.id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.put("/vouchers/{voucher_id}", response_model=BaseResponse)
async def update_voucher(voucher_id: int, voucher_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Voucher
    
    with db_manager.get_session() as session:
        try:
            voucher = session.query(Voucher).filter(
                Voucher.id == voucher_id,
                Voucher.tenant_id == current_user['tenant_id']
            ).first()
            
            if not voucher:
                raise HTTPException(status_code=404, detail="Voucher not found")
            
            if 'voucher_number' in voucher_data:
                voucher.voucher_number = voucher_data['voucher_number']
            if 'date' in voucher_data:
                voucher.voucher_date = datetime.fromisoformat(voucher_data['date'])
            if 'amount' in voucher_data:
                voucher.total_amount = voucher_data['amount']
            if 'description' in voucher_data:
                voucher.narration = voucher_data['description']
            
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Voucher updated successfully",
                data={"id": voucher_id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.delete("/vouchers/{voucher_id}", response_model=BaseResponse)
async def delete_voucher(voucher_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Voucher, Ledger, Journal, JournalDetail
    
    with db_manager.get_session() as session:
        try:
            voucher = session.query(Voucher).filter(
                Voucher.id == voucher_id,
                Voucher.tenant_id == current_user['tenant_id']
            ).first()
            
            if not voucher:
                raise HTTPException(status_code=404, detail="Voucher not found")
            
            if voucher.is_posted:
                raise HTTPException(status_code=400, detail="Cannot delete posted voucher. Please unpost it first.")
            
            voucher.is_deleted = True
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Voucher deleted successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.post("/vouchers/{voucher_id}/post", response_model=BaseResponse)
async def post_voucher(voucher_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Voucher
    
    with db_manager.get_session() as session:
        try:
            voucher = session.query(Voucher).filter(
                Voucher.id == voucher_id,
                Voucher.tenant_id == current_user['tenant_id']
            ).first()
            
            if not voucher:
                raise HTTPException(status_code=404, detail="Voucher not found")
            
            voucher.is_posted = True
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Voucher posted successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.post("/vouchers/{voucher_id}/unpost", response_model=BaseResponse)
async def unpost_voucher(voucher_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Voucher
    
    with db_manager.get_session() as session:
        try:
            voucher = session.query(Voucher).filter(
                Voucher.id == voucher_id,
                Voucher.tenant_id == current_user['tenant_id']
            ).first()
            
            if not voucher:
                raise HTTPException(status_code=404, detail="Voucher not found")
            
            voucher.is_posted = False
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Voucher unposted successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.post("/vouchers/{voucher_id}/reverse", response_model=BaseResponse)
async def reverse_voucher(voucher_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Voucher, VoucherType, Ledger, AccountMaster
    
    with db_manager.get_session() as session:
        try:
            # Get original voucher
            original_voucher = session.query(Voucher).filter(
                Voucher.id == voucher_id,
                Voucher.tenant_id == current_user['tenant_id']
            ).first()
            
            if not original_voucher:
                raise HTTPException(status_code=404, detail="Voucher not found")
            
            if not original_voucher.is_posted:
                raise HTTPException(status_code=400, detail="Only posted vouchers can be reversed")
            
            # Get original ledger entries
            original_entries = session.query(Ledger).filter(
                Ledger.voucher_id == voucher_id,
                Ledger.tenant_id == current_user['tenant_id']
            ).all()
            
            if not original_entries:
                raise HTTPException(status_code=400, detail="No ledger entries found for this voucher")
            
            # Generate new voucher number
            from datetime import datetime
            now = datetime.now()
            dd = str(now.day).zfill(2)
            mm = str(now.month).zfill(2)
            yyyy = now.year
            hh = str(now.hour).zfill(2)
            min_str = str(now.minute).zfill(2)
            ss = str(now.second).zfill(2)
            fff = str(now.microsecond // 1000).zfill(3)
            tenant_id = current_user['tenant_id']
            reverse_voucher_number = f"V-{tenant_id}{dd}{mm}{yyyy}{hh}{min_str}{ss}{fff}"
            
            # Create reversing voucher
            reverse_voucher = Voucher(
                voucher_number=reverse_voucher_number,
                voucher_type_id=original_voucher.voucher_type_id,
                voucher_date=datetime.now(),
                narration=f"Reversal of {original_voucher.voucher_number}: {original_voucher.narration or ''}",
                total_amount=original_voucher.total_amount,
                is_posted=True,
                tenant_id=current_user['tenant_id'],
                created_by=current_user['username']
            )
            session.add(reverse_voucher)
            session.flush()
            
            # Create reversing ledger entries (swap debit and credit)
            for entry in original_entries:
                # Calculate running balance
                previous_balance = session.query(
                    func.coalesce(func.sum(Ledger.debit_amount), 0) - func.coalesce(func.sum(Ledger.credit_amount), 0)
                ).filter(
                    Ledger.account_id == entry.account_id,
                    Ledger.transaction_date < datetime.now(),
                    Ledger.tenant_id == current_user['tenant_id']
                ).scalar() or 0
                
                same_date_balance = session.query(
                    func.coalesce(func.sum(Ledger.debit_amount), 0) - func.coalesce(func.sum(Ledger.credit_amount), 0)
                ).filter(
                    Ledger.account_id == entry.account_id,
                    Ledger.transaction_date == datetime.now(),
                    Ledger.tenant_id == current_user['tenant_id']
                ).scalar() or 0
                
                current_balance = float(previous_balance) + float(same_date_balance)
                # Reverse: swap debit and credit
                new_balance = current_balance + float(entry.credit_amount or 0) - float(entry.debit_amount or 0)
                
                reverse_entry = Ledger(
                    account_id=entry.account_id,
                    voucher_id=reverse_voucher.id,
                    transaction_date=datetime.now(),
                    debit_amount=entry.credit_amount,  # Swap
                    credit_amount=entry.debit_amount,  # Swap
                    balance=new_balance,
                    narration=f"Reversal: {entry.narration or ''}",
                    tenant_id=current_user['tenant_id']
                )
                session.add(reverse_entry)
            
            # Update account balances
            session.flush()
            for entry in original_entries:
                account = session.query(AccountMaster).filter(
                    AccountMaster.id == entry.account_id
                ).first()
                if account:
                    total_balance = session.query(
                        func.coalesce(func.sum(Ledger.debit_amount), 0) - func.coalesce(func.sum(Ledger.credit_amount), 0)
                    ).filter(
                        Ledger.account_id == entry.account_id,
                        Ledger.tenant_id == current_user['tenant_id']
                    ).scalar() or 0
                    account.current_balance = float(total_balance)
            
            session.commit()
            
            return BaseResponse(
                success=True,
                message=f"Voucher reversed successfully. Reversing voucher: {reverse_voucher_number}",
                data={"reverse_voucher_id": reverse_voucher.id, "reverse_voucher_number": reverse_voucher_number}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

# Payment endpoints
@router.get("/payments", response_model=PaginatedResponse)
async def get_payments(
    pagination: PaginationParams = Depends(),
    payment_mode: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Payment
    
    with db_manager.get_session() as session:
        query = session.query(Payment).filter(
            Payment.tenant_id == current_user['tenant_id']
        )
        
        if payment_mode:
            query = query.filter(Payment.payment_mode == payment_mode)
        
        if pagination.search:
            query = query.filter(or_(
                Payment.payment_type.ilike(f"%{pagination.search}%"),
                Payment.remarks.ilike(f"%{pagination.search}%"),
                Payment.payment_number.ilike(f"%{pagination.search}%")
            ))
        
        query = query.order_by(Payment.payment_date.desc(), Payment.id.desc())
        
        total = query.count()
        payments = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        payment_data = [{
            "id": payment.id,
            "payment_number": payment.payment_number,
            "payment_mode": payment.payment_mode,
            "payment_type": payment.payment_type,
            "account_id": payment.account_id,
            "amount": float(payment.amount) if payment.amount else 0,
            "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
            "reference_type": payment.reference_type or "",
            "reference_number": payment.reference_number or "",
            "remarks": payment.remarks or "",
            "status": "Completed"
        } for payment in payments]
    
    return PaginatedResponse(
        success=True,
        message="Payments retrieved successfully",
        data=payment_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/payments", response_model=BaseResponse)
async def create_payment(payment_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Payment
    
    with db_manager.get_session() as session:
        try:
            payment = Payment(
                payment_number=payment_data['payment_number'],
                payment_date=datetime.fromisoformat(payment_data['payment_date']),
                payment_type=payment_data['payment_type'],
                payment_mode=payment_data['payment_mode'],
                reference_type=payment_data.get('reference_type', 'GENERAL'),
                reference_id=payment_data.get('reference_id', 0),
                reference_number=payment_data.get('reference_number', ''),
                amount=payment_data['amount'],
                account_id=payment_data.get('account_id'),
                remarks=payment_data.get('remarks'),
                tenant_id=current_user['tenant_id'],
                created_by=current_user['username']
            )
            session.add(payment)
            session.flush()
            payment_id = payment.id
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Payment created successfully",
                data={"id": payment_id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.post("/record-payment", response_model=BaseResponse)
async def record_payment(payment_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    try:
        # Convert payment_date string to datetime if needed
        if 'payment_date' in payment_data and isinstance(payment_data['payment_date'], str):
            payment_data['payment_date'] = datetime.fromisoformat(payment_data['payment_date'].replace('Z', ''))
        
        payment_service = PaymentService()
        payment = payment_service.record_payment(payment_data)
        return BaseResponse(
            success=True,
            message="Payment recorded successfully",
            data={"id": payment.id, "payment_number": payment.payment_number}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/record-receipt", response_model=BaseResponse)
async def record_receipt(receipt_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    try:
        # Convert payment_date string to datetime if needed
        if 'payment_date' in receipt_data and isinstance(receipt_data['payment_date'], str):
            receipt_data['payment_date'] = datetime.fromisoformat(receipt_data['payment_date'].replace('Z', ''))
        
        payment_service = PaymentService()
        receipt = payment_service.record_receipt(receipt_data)
        return BaseResponse(
            success=True,
            message="Receipt recorded successfully",
            data={"id": receipt.id, "payment_number": receipt.payment_number}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/payments/{payment_id}", response_model=BaseResponse)
async def update_payment(payment_id: int, payment_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Payment
    
    with db_manager.get_session() as session:
        try:
            payment = session.query(Payment).filter(
                Payment.id == payment_id,
                Payment.tenant_id == current_user['tenant_id']
            ).first()
            
            if not payment:
                raise HTTPException(status_code=404, detail="Payment not found")
            
            if 'payment_date' in payment_data:
                payment.payment_date = datetime.fromisoformat(payment_data['payment_date'])
            if 'payment_type' in payment_data:
                payment.payment_type = payment_data['payment_type']
            if 'payment_mode' in payment_data:
                payment.payment_mode = payment_data['payment_mode']
            if 'amount' in payment_data:
                payment.amount = payment_data['amount']
            if 'account_id' in payment_data:
                payment.account_id = payment_data['account_id']
            if 'remarks' in payment_data:
                payment.remarks = payment_data['remarks']
            if 'reference_type' in payment_data:
                payment.reference_type = payment_data['reference_type']
            if 'reference_number' in payment_data:
                payment.reference_number = payment_data['reference_number']
            
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Payment updated successfully",
                data={"id": payment_id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.delete("/payments/{payment_id}", response_model=BaseResponse)
async def delete_payment(payment_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Payment
    
    with db_manager.get_session() as session:
        try:
            payment = session.query(Payment).filter(
                Payment.id == payment_id,
                Payment.tenant_id == current_user['tenant_id']
            ).first()
            
            if not payment:
                raise HTTPException(status_code=404, detail="Payment not found")
            
            session.delete(payment)
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Payment deleted successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

# Account Groups endpoints
@router.get("/account-groups", response_model=PaginatedResponse)
async def get_account_groups(current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import AccountGroup
    
    with db_manager.get_session() as session:
        groups = session.query(AccountGroup).filter(
            AccountGroup.tenant_id == current_user['tenant_id']
        ).order_by(AccountGroup.code).all()
        
        group_data = [{
            "id": group.id,
            "name": group.name,
            "code": group.code,
            "parent_id": group.parent_id,
            "account_type": group.account_type,
            "is_active": group.is_active
        } for group in groups]
    
    return PaginatedResponse(
        success=True,
        message="Account groups retrieved successfully",
        data=group_data,
        total=len(group_data),
        page=1,
        per_page=len(group_data),
        total_pages=1
    )

@router.post("/account-groups", response_model=BaseResponse)
async def create_account_group(group_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import AccountGroup
    
    with db_manager.get_session() as session:
        try:
            group = AccountGroup(
                name=group_data['name'],
                code=group_data['code'],
                parent_id=group_data.get('parent_id') if group_data.get('parent_id') else None,
                account_type=group_data['account_type'],
                is_active=group_data.get('is_active', True),
                tenant_id=current_user['tenant_id']
            )
            session.add(group)
            session.flush()
            group_id = group.id
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Account group created successfully",
                data={"id": group_id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.put("/account-groups/{group_id}", response_model=BaseResponse)
async def update_account_group(group_id: int, group_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import AccountGroup
    
    with db_manager.get_session() as session:
        try:
            group = session.query(AccountGroup).filter(
                AccountGroup.id == group_id,
                AccountGroup.tenant_id == current_user['tenant_id']
            ).first()
            
            if not group:
                raise HTTPException(status_code=404, detail="Account group not found")
            
            if 'name' in group_data:
                group.name = group_data['name']
            if 'code' in group_data:
                group.code = group_data['code']
            if 'parent_id' in group_data:
                group.parent_id = group_data['parent_id'] if group_data['parent_id'] else None
            if 'account_type' in group_data:
                group.account_type = group_data['account_type']
            if 'is_active' in group_data:
                group.is_active = group_data['is_active']
            
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Account group updated successfully",
                data={"id": group_id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.delete("/account-groups/{group_id}", response_model=BaseResponse)
async def delete_account_group(group_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import AccountGroup
    
    with db_manager.get_session() as session:
        try:
            group = session.query(AccountGroup).filter(
                AccountGroup.id == group_id,
                AccountGroup.tenant_id == current_user['tenant_id']
            ).first()
            
            if not group:
                raise HTTPException(status_code=404, detail="Account group not found")
            
            session.delete(group)
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Account group deleted successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

# Reports endpoints
@router.get("/trial-balance", response_model=BaseResponse)
async def get_trial_balance(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import AccountMaster, AccountGroup, Ledger
    from sqlalchemy import func
    
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
    from sqlalchemy import func
    
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
            else:  # EXPENSE
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
    from sqlalchemy import func
    
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
    from sqlalchemy import func
    
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
            else:  # EQUITY
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

# Export/Import endpoints
@router.get("/chart-of-accounts/export-template")
async def export_chart_of_accounts_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "code", "account_type", "parent_id", "current_balance", "is_active"])
    writer.writerow(["Cash", "1001", "Asset", "", "0.00", "true"])
    writer.writerow(["Bank", "1002", "Asset", "", "0.00", "true"])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=chart_of_accounts_template.csv"}
    )

@router.post("/chart-of-accounts/import", response_model=BaseResponse)
async def import_chart_of_accounts(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    account_service = AccountService()
    imported_count = 0
    
    for row in csv_data:
        try:
            account_data = {
                "name": row["name"],
                "code": row["code"],
                "account_type": row["account_type"],
                "current_balance": float(row["current_balance"]) if row["current_balance"] else 0,
                "is_active": row["is_active"].lower() == "true"
            }
            if row["parent_id"]:
                account_data["parent_id"] = int(row["parent_id"])
            
            account_service.create(account_data)
            imported_count += 1
        except Exception:
            continue
    
    return BaseResponse(
        success=True,
        message=f"Imported {imported_count} accounts successfully"
    )

@router.post("/ledger/recalculate-balances", response_model=BaseResponse)
async def recalculate_ledger_balances(current_user: dict = Depends(get_current_user)):
    """Recalculate all ledger balances - useful for fixing data inconsistencies"""
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Ledger, AccountMaster
    from sqlalchemy import func
    
    with db_manager.get_session() as session:
        try:
            # Get all accounts for the current tenant
            accounts = session.query(AccountMaster).filter(
                AccountMaster.tenant_id == current_user['tenant_id']
            ).all()
            
            updated_accounts = 0
            updated_entries = 0
            
            for account in accounts:
                # Get all ledger entries for this account ordered by date and id
                ledger_entries = session.query(Ledger).filter(
                    Ledger.account_id == account.id,
                    Ledger.tenant_id == current_user['tenant_id']
                ).order_by(Ledger.transaction_date.asc(), Ledger.id.asc()).all()
                
                running_balance = 0.0
                
                for entry in ledger_entries:
                    # Calculate running balance
                    debit = float(entry.debit_amount or 0)
                    credit = float(entry.credit_amount or 0)
                    running_balance += debit - credit
                    
                    # Update the balance field if it's different
                    if entry.balance != running_balance:
                        entry.balance = running_balance
                        updated_entries += 1
                
                # Update account current balance if it's different
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

# Tax Management endpoints
@router.get("/taxes", response_model=PaginatedResponse)
async def get_taxes(current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import TaxMaster
    
    with db_manager.get_session() as session:
        taxes = session.query(TaxMaster).filter(
            TaxMaster.tenant_id == current_user['tenant_id']
        ).all()
        
        tax_data = [{
            "id": tax.id,
            "name": tax.name,
            "tax_type": tax.tax_type,
            "rate": float(tax.rate),
            "is_active": tax.is_active
        } for tax in taxes]
    
    return PaginatedResponse(
        success=True,
        message="Taxes retrieved successfully",
        data=tax_data,
        total=len(tax_data),
        page=1,
        per_page=len(tax_data),
        total_pages=1
    )

@router.post("/taxes", response_model=BaseResponse)
async def create_tax(tax_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import TaxMaster
    
    with db_manager.get_session() as session:
        try:
            tax = TaxMaster(
                name=tax_data['name'],
                tax_type=tax_data['tax_type'],
                rate=tax_data['rate'],
                is_active=tax_data.get('is_active', True),
                tenant_id=current_user['tenant_id']
            )
            session.add(tax)
            session.flush()
            tax_id = tax.id
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Tax created successfully",
                data={"id": tax_id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.put("/taxes/{tax_id}", response_model=BaseResponse)
async def update_tax(tax_id: int, tax_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import TaxMaster
    
    with db_manager.get_session() as session:
        try:
            tax = session.query(TaxMaster).filter(
                TaxMaster.id == tax_id,
                TaxMaster.tenant_id == current_user['tenant_id']
            ).first()
            
            if not tax:
                raise HTTPException(status_code=404, detail="Tax not found")
            
            if 'name' in tax_data:
                tax.name = tax_data['name']
            if 'tax_type' in tax_data:
                tax.tax_type = tax_data['tax_type']
            if 'rate' in tax_data:
                tax.rate = tax_data['rate']
            if 'is_active' in tax_data:
                tax.is_active = tax_data['is_active']
            
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Tax updated successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.delete("/taxes/{tax_id}", response_model=BaseResponse)
async def delete_tax(tax_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import TaxMaster
    
    with db_manager.get_session() as session:
        try:
            tax = session.query(TaxMaster).filter(
                TaxMaster.id == tax_id,
                TaxMaster.tenant_id == current_user['tenant_id']
            ).first()
            
            if not tax:
                raise HTTPException(status_code=404, detail="Tax not found")
            
            session.delete(tax)
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Tax deleted successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.post("/taxes/import", response_model=BaseResponse)
async def import_taxes(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import TaxMaster
    
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    imported_count = 0
    with db_manager.get_session() as session:
        try:
            for row in csv_data:
                tax = TaxMaster(
                    name=row['name'],
                    tax_type=row['tax_type'],
                    rate=float(row['rate']),
                    is_active=row.get('is_active', 'true').lower() == 'true',
                    tenant_id=current_user['tenant_id']
                )
                session.add(tax)
                imported_count += 1
            
            session.commit()
            return BaseResponse(
                success=True,
                message=f"Imported {imported_count} taxes successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.get("/taxes/export-template")
async def export_taxes_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['name', 'tax_type', 'rate', 'is_active'])
    writer.writerow(['CGST 9%', 'GST', '9', 'true'])
    writer.writerow(['SGST 9%', 'GST', '9', 'true'])
    writer.writerow(['IGST 18%', 'GST', '18', 'true'])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=taxes_template.csv"}
    )

# Currency Management endpoints
@router.get("/currencies", response_model=PaginatedResponse)
async def get_currencies(current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Currency
    
    with db_manager.get_session() as session:
        currencies = session.query(Currency).filter(Currency.is_active == True).all()
        
        currency_data = [{
            "id": curr.id,
            "code": curr.code,
            "name": curr.name,
            "symbol": curr.symbol,
            "is_base": curr.is_base
        } for curr in currencies]
    
    return PaginatedResponse(
        success=True,
        message="Currencies retrieved successfully",
        data=currency_data,
        total=len(currency_data),
        page=1,
        per_page=len(currency_data),
        total_pages=1
    )

@router.get("/exchange-rates", response_model=BaseResponse)
async def get_exchange_rate(
    from_currency: str = Query(...),
    to_currency: str = Query(...),
    date: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import ExchangeRate, Currency
    from datetime import datetime
    
    with db_manager.get_session() as session:
        effective_date = datetime.fromisoformat(date).date() if date else datetime.now().date()
        
        from_curr = session.query(Currency).filter(Currency.code == from_currency).first()
        to_curr = session.query(Currency).filter(Currency.code == to_currency).first()
        
        if not from_curr or not to_curr:
            raise HTTPException(status_code=404, detail="Currency not found")
        
        rate = session.query(ExchangeRate).filter(
            ExchangeRate.from_currency_id == from_curr.id,
            ExchangeRate.to_currency_id == to_curr.id,
            ExchangeRate.effective_date <= effective_date,
            ExchangeRate.tenant_id == current_user['tenant_id']
        ).order_by(ExchangeRate.effective_date.desc()).first()
        
        if not rate:
            return BaseResponse(
                success=True,
                message="No exchange rate found, using default",
                data={"rate": 1.0}
            )
        
        return BaseResponse(
            success=True,
            message="Exchange rate retrieved successfully",
            data={"rate": float(rate.rate)}
        )

@router.get("/exchange-rates/all", response_model=BaseResponse)
async def get_all_exchange_rates(current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import ExchangeRate, Currency
    
    with db_manager.get_session() as session:
        rates = session.query(ExchangeRate).filter(
            ExchangeRate.tenant_id == current_user['tenant_id']
        ).order_by(ExchangeRate.effective_date.desc()).all()
        
        rate_data = []
        for rate in rates:
            from_curr = session.query(Currency).filter(Currency.id == rate.from_currency_id).first()
            to_curr = session.query(Currency).filter(Currency.id == rate.to_currency_id).first()
            
            rate_data.append({
                "id": rate.id,
                "from_currency": from_curr.code if from_curr else "",
                "to_currency": to_curr.code if to_curr else "",
                "rate": float(rate.rate),
                "effective_date": rate.effective_date.isoformat()
            })
        
        return BaseResponse(
            success=True,
            message="Exchange rates retrieved successfully",
            data=rate_data
        )

@router.post("/exchange-rates", response_model=BaseResponse)
async def create_exchange_rate(rate_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import ExchangeRate, Currency
    from datetime import datetime
    
    with db_manager.get_session() as session:
        try:
            from_curr = session.query(Currency).filter(Currency.code == rate_data['from_currency']).first()
            to_curr = session.query(Currency).filter(Currency.code == rate_data['to_currency']).first()
            
            if not from_curr or not to_curr:
                raise HTTPException(status_code=404, detail="Currency not found")
            
            rate = ExchangeRate(
                from_currency_id=from_curr.id,
                to_currency_id=to_curr.id,
                rate=rate_data['rate'],
                effective_date=datetime.fromisoformat(rate_data['effective_date']).date(),
                tenant_id=current_user['tenant_id']
            )
            session.add(rate)
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Exchange rate created successfully",
                data={"id": rate.id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.delete("/exchange-rates/{rate_id}", response_model=BaseResponse)
async def delete_exchange_rate(rate_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import ExchangeRate
    
    with db_manager.get_session() as session:
        try:
            rate = session.query(ExchangeRate).filter(
                ExchangeRate.id == rate_id,
                ExchangeRate.tenant_id == current_user['tenant_id']
            ).first()
            
            if not rate:
                raise HTTPException(status_code=404, detail="Exchange rate not found")
            
            session.delete(rate)
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Exchange rate deleted successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.post("/exchange-rates/import", response_model=BaseResponse)
async def import_exchange_rates(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import ExchangeRate, Currency
    from datetime import datetime
    
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    imported_count = 0
    with db_manager.get_session() as session:
        try:
            for row in csv_data:
                from_curr = session.query(Currency).filter(Currency.code == row['from_currency']).first()
                to_curr = session.query(Currency).filter(Currency.code == row['to_currency']).first()
                
                if not from_curr or not to_curr:
                    continue
                
                rate = ExchangeRate(
                    from_currency_id=from_curr.id,
                    to_currency_id=to_curr.id,
                    rate=float(row['rate']),
                    effective_date=datetime.fromisoformat(row['effective_date']).date(),
                    tenant_id=current_user['tenant_id']
                )
                session.add(rate)
                imported_count += 1
            
            session.commit()
            return BaseResponse(
                success=True,
                message=f"Imported {imported_count} exchange rates successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.get("/exchange-rates/export-template")
async def export_exchange_rates_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['from_currency', 'to_currency', 'rate', 'effective_date'])
    writer.writerow(['USD', 'INR', '83.50', '2024-01-01'])
    writer.writerow(['EUR', 'INR', '91.20', '2024-01-01'])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=exchange_rates_template.csv"}
    )

# Bank Reconciliation endpoints
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
    
    with db_manager.get_session() as session:
        try:
            # Calculate book balance
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
        
        # Get unmatched ledger entries
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

# Recurring Vouchers endpoints
@router.get("/recurring-vouchers", response_model=PaginatedResponse)
async def get_recurring_vouchers(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from sqlalchemy import text
    
    with db_manager.get_session() as session:
        # Query recurring_vouchers table directly
        query = text("""
            SELECT id, name, voucher_type, frequency, start_date, end_date, description, is_active
            FROM recurring_vouchers
            WHERE tenant_id = :tenant_id
            ORDER BY created_at DESC
        """)
        
        result = session.execute(query, {"tenant_id": current_user['tenant_id']})
        rows = result.fetchall()
        
        voucher_data = [{
            "id": row[0],
            "name": row[1],
            "voucher_type": row[2],
            "frequency": row[3],
            "start_date": row[4].isoformat() if row[4] else None,
            "end_date": row[5].isoformat() if row[5] else None,
            "description": row[6] or "",
            "is_active": row[7]
        } for row in rows]
        
        return PaginatedResponse(
            success=True,
            message="Recurring vouchers retrieved successfully",
            data=voucher_data,
            total=len(voucher_data),
            page=pagination.page,
            per_page=pagination.per_page,
            total_pages=math.ceil(len(voucher_data) / pagination.per_page) if len(voucher_data) > 0 else 0
        )

@router.post("/recurring-vouchers", response_model=BaseResponse)
async def create_recurring_voucher(voucher_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from sqlalchemy import text
    
    with db_manager.get_session() as session:
        try:
            query = text("""
                INSERT INTO recurring_vouchers (name, voucher_type, frequency, start_date, end_date, description, is_active, tenant_id, created_by, created_at)
                VALUES (:name, :voucher_type, :frequency, :start_date, :end_date, :description, :is_active, :tenant_id, :created_by, NOW())
                RETURNING id
            """)
            
            result = session.execute(query, {
                "name": voucher_data['name'],
                "voucher_type": voucher_data['voucher_type'],
                "frequency": voucher_data['frequency'],
                "start_date": voucher_data['start_date'],
                "end_date": voucher_data.get('end_date') if voucher_data.get('end_date') else None,
                "description": voucher_data.get('description', ''),
                "is_active": voucher_data.get('is_active', True),
                "tenant_id": current_user['tenant_id'],
                "created_by": current_user['username']
            })
            
            voucher_id = result.fetchone()[0]
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Recurring voucher created successfully",
                data={"id": voucher_id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.put("/recurring-vouchers/{voucher_id}", response_model=BaseResponse)
async def update_recurring_voucher(voucher_id: int, voucher_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from sqlalchemy import text
    
    with db_manager.get_session() as session:
        try:
            query = text("""
                UPDATE recurring_vouchers
                SET name = :name, voucher_type = :voucher_type, frequency = :frequency,
                    start_date = :start_date, end_date = :end_date, description = :description,
                    is_active = :is_active, updated_at = NOW(), updated_by = :updated_by
                WHERE id = :id AND tenant_id = :tenant_id
            """)
            
            session.execute(query, {
                "id": voucher_id,
                "name": voucher_data['name'],
                "voucher_type": voucher_data['voucher_type'],
                "frequency": voucher_data['frequency'],
                "start_date": voucher_data['start_date'],
                "end_date": voucher_data.get('end_date') if voucher_data.get('end_date') else None,
                "description": voucher_data.get('description', ''),
                "is_active": voucher_data.get('is_active', True),
                "updated_by": current_user['username'],
                "tenant_id": current_user['tenant_id']
            })
            
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Recurring voucher updated successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.delete("/recurring-vouchers/{voucher_id}", response_model=BaseResponse)
async def delete_recurring_voucher(voucher_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from sqlalchemy import text
    
    with db_manager.get_session() as session:
        try:
            query = text("""
                DELETE FROM recurring_vouchers
                WHERE id = :id AND tenant_id = :tenant_id
            """)
            
            session.execute(query, {
                "id": voucher_id,
                "tenant_id": current_user['tenant_id']
            })
            
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Recurring voucher deleted successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

# Voucher Series endpoints
@router.get("/voucher-series", response_model=PaginatedResponse)
async def get_voucher_series(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import VoucherType
    
    with db_manager.get_session() as session:
        query = session.query(VoucherType).filter(
            VoucherType.tenant_id == current_user['tenant_id']
        )
        
        total = query.count()
        voucher_types = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        data = [{
            "id": vt.id,
            "name": vt.name,
            "code": vt.code,
            "prefix": vt.prefix,
            "is_active": vt.is_active
        } for vt in voucher_types]
    
    return PaginatedResponse(
        success=True,
        message="Voucher series retrieved successfully",
        data=data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page) if total > 0 else 0
    )

@router.put("/voucher-series/{series_id}", response_model=BaseResponse)
async def update_voucher_series(series_id: int, series_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import VoucherType
    
    with db_manager.get_session() as session:
        voucher_type = session.query(VoucherType).filter(
            VoucherType.id == series_id,
            VoucherType.tenant_id == current_user['tenant_id']
        ).first()
        
        if not voucher_type:
            raise HTTPException(status_code=404, detail="Voucher type not found")
        
        if 'code' in series_data:
            voucher_type.code = series_data['code']
        if 'prefix' in series_data:
            voucher_type.prefix = series_data['prefix']
        if 'is_active' in series_data:
            voucher_type.is_active = series_data['is_active']
        
        session.commit()
    
    return BaseResponse(
        success=True,
        message="Voucher series updated successfully"
    )

# Cost Center endpoints
@router.get("/cost-centers", response_model=PaginatedResponse)
async def get_cost_centers(current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import CostCenter
    
    with db_manager.get_session() as session:
        cost_centers = session.query(CostCenter).filter(
            CostCenter.tenant_id == current_user['tenant_id']
        ).all()
        
        cc_data = [{
            "id": cc.id,
            "name": cc.name,
            "code": cc.code,
            "parent_id": cc.parent_id,
            "is_active": cc.is_active
        } for cc in cost_centers]
    
    return PaginatedResponse(
        success=True,
        message="Cost centers retrieved successfully",
        data=cc_data,
        total=len(cc_data),
        page=1,
        per_page=len(cc_data),
        total_pages=1
    )

@router.post("/cost-centers", response_model=BaseResponse)
async def create_cost_center(cc_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import CostCenter
    
    with db_manager.get_session() as session:
        try:
            cc = CostCenter(
                name=cc_data['name'],
                code=cc_data['code'],
                parent_id=cc_data.get('parent_id'),
                is_active=cc_data.get('is_active', True),
                tenant_id=current_user['tenant_id']
            )
            session.add(cc)
            session.flush()
            cc_id = cc.id
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Cost center created successfully",
                data={"id": cc_id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.put("/cost-centers/{cc_id}", response_model=BaseResponse)
async def update_cost_center(cc_id: int, cc_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import CostCenter
    
    with db_manager.get_session() as session:
        try:
            cc = session.query(CostCenter).filter(
                CostCenter.id == cc_id,
                CostCenter.tenant_id == current_user['tenant_id']
            ).first()
            
            if not cc:
                raise HTTPException(status_code=404, detail="Cost center not found")
            
            if 'name' in cc_data:
                cc.name = cc_data['name']
            if 'code' in cc_data:
                cc.code = cc_data['code']
            if 'parent_id' in cc_data:
                cc.parent_id = cc_data['parent_id']
            if 'is_active' in cc_data:
                cc.is_active = cc_data['is_active']
            
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Cost center updated successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.delete("/cost-centers/{cc_id}", response_model=BaseResponse)
async def delete_cost_center(cc_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import CostCenter
    
    with db_manager.get_session() as session:
        try:
            cc = session.query(CostCenter).filter(
                CostCenter.id == cc_id,
                CostCenter.tenant_id == current_user['tenant_id']
            ).first()
            
            if not cc:
                raise HTTPException(status_code=404, detail="Cost center not found")
            
            session.delete(cc)
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Cost center deleted successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.post("/cost-centers/import", response_model=BaseResponse)
async def import_cost_centers(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import CostCenter
    
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    imported_count = 0
    with db_manager.get_session() as session:
        try:
            for row in csv_data:
                parent_id = None
                if row.get("parent_cost_center") and row["parent_cost_center"].strip():
                    parent = session.query(CostCenter).filter(
                        CostCenter.name == row["parent_cost_center"].strip(),
                        CostCenter.tenant_id == current_user['tenant_id']
                    ).first()
                    if parent:
                        parent_id = parent.id
                
                cc = CostCenter(
                    code=row["code"],
                    name=row["name"],
                    parent_id=parent_id,
                    is_active=row.get("is_active", "true").lower() == "true",
                    tenant_id=current_user['tenant_id']
                )
                session.add(cc)
                imported_count += 1
            
            session.commit()
            return BaseResponse(
                success=True,
                message=f"Imported {imported_count} cost centers successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.get("/cost-centers/export-template")
async def export_cost_centers_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["code", "name", "parent_cost_center", "is_active"])
    writer.writerow(["CC001", "Sales Department", "", "true"])
    writer.writerow(["CC002", "Marketing Department", "", "true"])
    writer.writerow(["CC003", "Sales Team A", "Sales Department", "true"])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=cost_centers_template.csv"}
    )

# Budget endpoints
@router.get("/budgets", response_model=PaginatedResponse)
async def get_budgets(current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Budget
    
    with db_manager.get_session() as session:
        budgets = session.query(Budget).filter(
            Budget.tenant_id == current_user['tenant_id']
        ).all()
        
        budget_data = [{
            "id": b.id,
            "name": b.name,
            "fiscal_year_id": b.fiscal_year_id,
            "account_id": b.account_id,
            "cost_center_id": b.cost_center_id,
            "budget_amount": float(b.budget_amount),
            "actual_amount": float(b.actual_amount),
            "variance": float(b.variance),
            "status": b.status
        } for b in budgets]
    
    return PaginatedResponse(
        success=True,
        message="Budgets retrieved successfully",
        data=budget_data,
        total=len(budget_data),
        page=1,
        per_page=len(budget_data),
        total_pages=1
    )

@router.post("/budgets", response_model=BaseResponse)
async def create_budget(budget_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Budget
    
    with db_manager.get_session() as session:
        try:
            budget = Budget(
                name=budget_data['name'],
                fiscal_year_id=budget_data['fiscal_year_id'],
                account_id=budget_data['account_id'],
                cost_center_id=budget_data.get('cost_center_id'),
                budget_amount=budget_data['budget_amount'],
                status=budget_data.get('status', 'DRAFT'),
                tenant_id=current_user['tenant_id'],
                created_by=current_user['username']
            )
            session.add(budget)
            session.flush()
            budget_id = budget.id
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Budget created successfully",
                data={"id": budget_id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.put("/budgets/{budget_id}", response_model=BaseResponse)
async def update_budget(budget_id: int, budget_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Budget
    
    with db_manager.get_session() as session:
        try:
            budget = session.query(Budget).filter(
                Budget.id == budget_id,
                Budget.tenant_id == current_user['tenant_id']
            ).first()
            
            if not budget:
                raise HTTPException(status_code=404, detail="Budget not found")
            
            if 'name' in budget_data:
                budget.name = budget_data['name']
            if 'budget_amount' in budget_data:
                budget.budget_amount = budget_data['budget_amount']
            if 'status' in budget_data:
                budget.status = budget_data['status']
            
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Budget updated successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.delete("/budgets/{budget_id}", response_model=BaseResponse)
async def delete_budget(budget_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Budget
    
    with db_manager.get_session() as session:
        try:
            budget = session.query(Budget).filter(
                Budget.id == budget_id,
                Budget.tenant_id == current_user['tenant_id']
            ).first()
            
            if not budget:
                raise HTTPException(status_code=404, detail="Budget not found")
            
            session.delete(budget)
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Budget deleted successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.post("/budgets/import", response_model=BaseResponse)
async def import_budgets(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Budget, FiscalYear, AccountMaster, CostCenter
    
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    imported_count = 0
    with db_manager.get_session() as session:
        try:
            for row in csv_data:
                fiscal_year = session.query(FiscalYear).filter(
                    FiscalYear.name == row['fiscal_year'],
                    FiscalYear.tenant_id == current_user['tenant_id']
                ).first()
                
                account = session.query(AccountMaster).filter(
                    AccountMaster.name == row['account'],
                    AccountMaster.tenant_id == current_user['tenant_id']
                ).first()
                
                if not fiscal_year or not account:
                    continue
                
                cost_center_id = None
                if row.get('cost_center') and row['cost_center'].strip():
                    cost_center = session.query(CostCenter).filter(
                        CostCenter.name == row['cost_center'].strip(),
                        CostCenter.tenant_id == current_user['tenant_id']
                    ).first()
                    if cost_center:
                        cost_center_id = cost_center.id
                
                budget = Budget(
                    name=row['name'],
                    fiscal_year_id=fiscal_year.id,
                    account_id=account.id,
                    cost_center_id=cost_center_id,
                    budget_amount=float(row['budget_amount']),
                    status=row.get('status', 'DRAFT'),
                    tenant_id=current_user['tenant_id'],
                    created_by=current_user['username']
                )
                session.add(budget)
                imported_count += 1
            
            session.commit()
            return BaseResponse(
                success=True,
                message=f"Imported {imported_count} budgets successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@router.get("/budgets/export-template")
async def export_budgets_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['name', 'fiscal_year', 'account', 'cost_center', 'budget_amount', 'status'])
    writer.writerow(['Marketing Budget 2024', 'FY 2024-25', 'Marketing Expenses', 'Marketing Department', '100000', 'DRAFT'])
    writer.writerow(['Sales Budget 2024', 'FY 2024-25', 'Sales Expenses', '', '150000', 'APPROVED'])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=budgets_template.csv"}
    )

# Fiscal Year endpoints
@router.get("/fiscal-years", response_model=PaginatedResponse)
async def get_fiscal_years(current_user: dict = Depends(get_current_user)):
    from modules.account_module.services.fiscal_year_service import FiscalYearService
    
    try:
        fiscal_year_service = FiscalYearService()
        fiscal_years = fiscal_year_service.get_all()
        
        fiscal_year_data = [{
            "id": fy.id,
            "name": fy.name,
            "start_date": fy.start_date.isoformat(),
            "end_date": fy.end_date.isoformat(),
            "is_active": fy.is_active,
            "is_closed": fy.is_closed
        } for fy in fiscal_years]
        
        return PaginatedResponse(
            success=True,
            message="Fiscal years retrieved successfully",
            data=fiscal_year_data,
            total=len(fiscal_year_data),
            page=1,
            per_page=len(fiscal_year_data),
            total_pages=1
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/fiscal-years", response_model=BaseResponse)
async def create_fiscal_year(fiscal_year_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from modules.account_module.services.fiscal_year_service import FiscalYearService
    
    try:
        fiscal_year_service = FiscalYearService()
        fiscal_year = fiscal_year_service.create(fiscal_year_data)
        
        return BaseResponse(
            success=True,
            message="Fiscal year created successfully",
            data={"id": fiscal_year.id}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/fiscal-years/{fiscal_year_id}", response_model=BaseResponse)
async def update_fiscal_year(fiscal_year_id: int, fiscal_year_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from modules.account_module.services.fiscal_year_service import FiscalYearService
    
    try:
        fiscal_year_service = FiscalYearService()
        fiscal_year = fiscal_year_service.update(fiscal_year_id, fiscal_year_data)
        
        return BaseResponse(
            success=True,
            message="Fiscal year updated successfully",
            data={"id": fiscal_year.id}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/fiscal-years/{fiscal_year_id}", response_model=BaseResponse)
async def delete_fiscal_year(fiscal_year_id: int, current_user: dict = Depends(get_current_user)):
    from modules.account_module.services.fiscal_year_service import FiscalYearService
    
    try:
        fiscal_year_service = FiscalYearService()
        fiscal_year_service.soft_delete(fiscal_year_id)
        
        return BaseResponse(
            success=True,
            message="Fiscal year deleted successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/fiscal-years/{fiscal_year_id}/close", response_model=BaseResponse)
async def close_fiscal_year(fiscal_year_id: int, current_user: dict = Depends(get_current_user)):
    from modules.account_module.services.fiscal_year_service import FiscalYearService
    
    try:
        fiscal_year_service = FiscalYearService()
        fiscal_year = fiscal_year_service.close_fiscal_year(fiscal_year_id)
        
        return BaseResponse(
            success=True,
            message="Fiscal year closed successfully",
            data={"id": fiscal_year.id}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Report Export endpoints
@router.get("/reports/trial-balance/export")
async def export_trial_balance(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    format: str = Query("pdf", regex="^(pdf|excel)$"),
    current_user: dict = Depends(get_current_user)
):
    from modules.account_module.services.report_export_service import ReportExportService
    
    try:
        export_service = ReportExportService()
        file_data, filename, media_type = export_service.export_trial_balance(
            from_date=from_date,
            to_date=to_date,
            format=format
        )
        
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/reports/profit-loss/export")
async def export_profit_loss(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    format: str = Query("pdf", regex="^(pdf|excel)$"),
    current_user: dict = Depends(get_current_user)
):
    from modules.account_module.services.report_export_service import ReportExportService
    
    try:
        export_service = ReportExportService()
        file_data, filename, media_type = export_service.export_profit_loss(
            from_date=from_date,
            to_date=to_date,
            format=format
        )
        
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/reports/balance-sheet/export")
async def export_balance_sheet(
    as_of_date: Optional[str] = Query(None),
    format: str = Query("pdf", regex="^(pdf|excel)$"),
    current_user: dict = Depends(get_current_user)
):
    from modules.account_module.services.report_export_service import ReportExportService
    
    try:
        export_service = ReportExportService()
        file_data, filename, media_type = export_service.export_balance_sheet(
            as_of_date=as_of_date,
            format=format
        )
        
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# AR/AP Aging Reports
@router.get("/reports/ar-aging", response_model=BaseResponse)
async def get_ar_aging(
    as_of_date: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get Accounts Receivable Aging Report"""
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Ledger, AccountMaster, Voucher
    from sqlalchemy import and_, case
    from datetime import datetime, timedelta
    
    with db_manager.get_session() as session:
        as_of = datetime.fromisoformat(as_of_date).date() if as_of_date else datetime.now().date()
        
        # Get AR account
        ar_account = session.query(AccountMaster).filter(
            AccountMaster.code == 'AR001',
            AccountMaster.tenant_id == current_user['tenant_id']
        ).first()
        
        if not ar_account:
            raise HTTPException(status_code=404, detail="AR account not found")
        
        # Get unpaid invoices
        invoices = session.query(
            Voucher.id,
            Voucher.voucher_number,
            Voucher.voucher_date,
            Voucher.total_amount,
            Voucher.reference_number
        ).join(Ledger).filter(
            and_(
                Ledger.account_id == ar_account.id,
                Ledger.debit_amount > 0,
                Voucher.voucher_date <= as_of,
                Voucher.tenant_id == current_user['tenant_id']
            )
        ).all()
        
        aging_data = []
        for inv in invoices:
            days_outstanding = (as_of - inv.voucher_date.date()).days
            
            # Calculate paid amount
            paid = session.query(func.coalesce(func.sum(Ledger.credit_amount), 0)).filter(
                Ledger.voucher_id == inv.id,
                Ledger.account_id == ar_account.id
            ).scalar() or 0
            
            balance = float(inv.total_amount) - float(paid)
            
            if balance > 0.01:  # Only unpaid invoices
                aging_data.append({
                    'invoice_number': inv.voucher_number,
                    'invoice_date': inv.voucher_date.isoformat(),
                    'reference': inv.reference_number or '',
                    'total_amount': float(inv.total_amount),
                    'balance': balance,
                    'days_outstanding': days_outstanding,
                    'current': balance if days_outstanding <= 30 else 0,
                    '31_60': balance if 31 <= days_outstanding <= 60 else 0,
                    '61_90': balance if 61 <= days_outstanding <= 90 else 0,
                    'over_90': balance if days_outstanding > 90 else 0
                })
        
        # Calculate totals
        totals = {
            'total_balance': sum(item['balance'] for item in aging_data),
            'current': sum(item['current'] for item in aging_data),
            '31_60': sum(item['31_60'] for item in aging_data),
            '61_90': sum(item['61_90'] for item in aging_data),
            'over_90': sum(item['over_90'] for item in aging_data)
        }
        
        return BaseResponse(
            success=True,
            message="AR Aging report retrieved successfully",
            data={'invoices': aging_data, 'totals': totals}
        )

@router.get("/reports/ap-aging", response_model=BaseResponse)
async def get_ap_aging(
    as_of_date: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get Accounts Payable Aging Report"""
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Ledger, AccountMaster, Voucher
    from sqlalchemy import and_
    from datetime import datetime
    
    with db_manager.get_session() as session:
        as_of = datetime.fromisoformat(as_of_date).date() if as_of_date else datetime.now().date()
        
        # Get AP account
        ap_account = session.query(AccountMaster).filter(
            AccountMaster.code == 'AP001',
            AccountMaster.tenant_id == current_user['tenant_id']
        ).first()
        
        if not ap_account:
            raise HTTPException(status_code=404, detail="AP account not found")
        
        # Get unpaid bills
        bills = session.query(
            Voucher.id,
            Voucher.voucher_number,
            Voucher.voucher_date,
            Voucher.total_amount,
            Voucher.reference_number
        ).join(Ledger).filter(
            and_(
                Ledger.account_id == ap_account.id,
                Ledger.credit_amount > 0,
                Voucher.voucher_date <= as_of,
                Voucher.tenant_id == current_user['tenant_id']
            )
        ).all()
        
        aging_data = []
        for bill in bills:
            days_outstanding = (as_of - bill.voucher_date.date()).days
            
            # Calculate paid amount
            paid = session.query(func.coalesce(func.sum(Ledger.debit_amount), 0)).filter(
                Ledger.voucher_id == bill.id,
                Ledger.account_id == ap_account.id
            ).scalar() or 0
            
            balance = float(bill.total_amount) - float(paid)
            
            if balance > 0.01:  # Only unpaid bills
                aging_data.append({
                    'bill_number': bill.voucher_number,
                    'bill_date': bill.voucher_date.isoformat(),
                    'reference': bill.reference_number or '',
                    'total_amount': float(bill.total_amount),
                    'balance': balance,
                    'days_outstanding': days_outstanding,
                    'current': balance if days_outstanding <= 30 else 0,
                    '31_60': balance if 31 <= days_outstanding <= 60 else 0,
                    '61_90': balance if 61 <= days_outstanding <= 90 else 0,
                    'over_90': balance if days_outstanding > 90 else 0
                })
        
        # Calculate totals
        totals = {
            'total_balance': sum(item['balance'] for item in aging_data),
            'current': sum(item['current'] for item in aging_data),
            '31_60': sum(item['31_60'] for item in aging_data),
            '61_90': sum(item['61_90'] for item in aging_data),
            'over_90': sum(item['over_90'] for item in aging_data)
        }
        
        return BaseResponse(
            success=True,
            message="AP Aging report retrieved successfully",
            data={'bills': aging_data, 'totals': totals}
        )

# Audit Trail endpoint
@router.get("/audit-trail", response_model=PaginatedResponse)
async def get_audit_trail(
    pagination: PaginationParams = Depends(),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get audit trail for accounting transactions"""
    from core.database.connection import db_manager
    from modules.account_module.models.audit_trail import AuditTrail
    
    with db_manager.get_session() as session:
        query = session.query(AuditTrail).filter(
            AuditTrail.tenant_id == current_user['tenant_id']
        )
        
        if entity_type:
            query = query.filter(AuditTrail.entity_type == entity_type)
        
        if entity_id:
            query = query.filter(AuditTrail.entity_id == entity_id)
        
        if pagination.search:
            query = query.filter(or_(
                AuditTrail.username.ilike(f"%{pagination.search}%"),
                AuditTrail.remarks.ilike(f"%{pagination.search}%")
            ))
        
        total = query.count()
        entries = query.order_by(AuditTrail.created_at.desc()).offset(pagination.offset).limit(pagination.per_page).all()
        
        audit_data = [{
            'id': entry.id,
            'entity_type': entry.entity_type,
            'entity_id': entry.entity_id,
            'action': entry.action,
            'username': entry.username,
            'created_at': entry.created_at.isoformat(),
            'remarks': entry.remarks,
            'old_value': entry.old_value,
            'new_value': entry.new_value
        } for entry in entries]
        
        return PaginatedResponse(
            success=True,
            message="Audit trail retrieved successfully",
            data=audit_data,
            total=total,
            page=pagination.page,
            per_page=pagination.per_page,
            total_pages=math.ceil(total / pagination.per_page)
        )

# GST Calculation endpoint
@router.post("/calculate-gst", response_model=BaseResponse)
async def calculate_gst(
    gst_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Calculate GST amounts"""
    from modules.account_module.services.gst_service import GSTService
    
    try:
        result = GSTService.calculate_gst(
            subtotal=gst_data['subtotal'],
            gst_rate=gst_data['gst_rate'],
            is_interstate=gst_data.get('is_interstate', False)
        )
        
        return BaseResponse(
            success=True,
            message="GST calculated successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))