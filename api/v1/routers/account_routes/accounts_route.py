from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional
import io
import csv
from datetime import datetime
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user
from sqlalchemy import or_
from modules.account_module.services.account_service import AccountService
from modules.account_module.services.audit_service import AuditService

router = APIRouter()

# Account endpoints (moved from api/v1/routers/account.py)
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
