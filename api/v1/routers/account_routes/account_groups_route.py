from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import math
from api.schemas.common import PaginatedResponse, BaseResponse
from api.middleware.auth_middleware import get_current_user

router = APIRouter()


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
