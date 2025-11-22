from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user
from modules.account_module.services.audit_service import AuditService
from sqlalchemy import or_
from sqlalchemy import func

router = APIRouter()

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
            "amount": float(voucher.base_total_amount) if voucher.base_total_amount else 0,
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
            "amount": float(voucher.base_total_amount) if voucher.base_total_amount else 0,
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
            ValidationService.validate_financial_year(
                session, 
                datetime.fromisoformat(voucher_data['date']), 
                current_user['tenant_id']
            )
            
            ValidationService.validate_voucher_lines(voucher_data['lines'])
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
            
            voucher = Voucher(
                voucher_number=voucher_data['voucher_number'],
                voucher_type_id=voucher_type.id,
                voucher_date=datetime.fromisoformat(voucher_data['date']),
                narration=voucher_data.get('description', ''),
                base_total_amount=voucher_data['total_amount'],
                is_posted=voucher_data.get('is_posted', False),
                tenant_id=current_user['tenant_id'],
                created_by=current_user['username']
            )
            session.add(voucher)
            session.flush()
            
            for line in voucher_data['lines']:
                if line['account_id'] and (line['debit'] or line['credit']):
                    account = session.query(AccountMaster).with_for_update().filter(
                        AccountMaster.id == line['account_id']
                    ).first()
                    
                    if not account:
                        raise HTTPException(status_code=404, detail=f"Account {line['account_id']} not found")
                    
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
                    account.current_balance = new_balance
            
            session.flush()
            
            AuditService.log_action(
                session, 'VOUCHER', voucher.id, 'CREATE',
                new_value={'voucher_number': voucher.voucher_number, 'amount': float(voucher.base_total_amount)}
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

# Additional voucher endpoints (update/delete/post/unpost/reverse) follow the same logic
# For brevity they are included below (copied from original file)

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
                voucher.base_total_amount = voucher_data['amount']
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
    from modules.account_module.models.entities import Voucher

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
                base_total_amount=original_voucher.base_total_amount,
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


