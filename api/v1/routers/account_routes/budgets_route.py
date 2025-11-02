from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user
import math

router = APIRouter()


@router.get("/budgets", response_model=PaginatedResponse)
async def get_budgets(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Budget

    with db_manager.get_session() as session:
        query = session.query(Budget).filter(Budget.tenant_id == current_user['tenant_id'])
        total = query.count()
        budgets = query.offset(pagination.offset).limit(pagination.per_page).all()
        data = [{"id": b.id, "name": b.name, "amount": float(b.amount)} for b in budgets]
        return PaginatedResponse(success=True, message="Budgets retrieved", data=data, total=total, page=pagination.page, per_page=pagination.per_page, total_pages=math.ceil(total/pagination.per_page) if total else 0)


@router.post("/budgets", response_model=BaseResponse)
async def create_budget(budget_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Budget

    with db_manager.get_session() as session:
        try:
            b = Budget(name=budget_data['name'], amount=budget_data['amount'], tenant_id=current_user['tenant_id'])
            session.add(b)
            session.flush()
            bid = b.id
            session.commit()
            return BaseResponse(success=True, message="Budget created", data={"id": bid})
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))


@router.put("/budgets/{budget_id}", response_model=BaseResponse)
async def update_budget(budget_id: int, budget_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Budget

    with db_manager.get_session() as session:
        try:
            b = session.query(Budget).filter(Budget.id == budget_id, Budget.tenant_id == current_user['tenant_id']).first()
            if not b:
                raise HTTPException(status_code=404, detail="Budget not found")
            if 'name' in budget_data:
                b.name = budget_data['name']
            if 'amount' in budget_data:
                b.amount = budget_data['amount']
            session.commit()
            return BaseResponse(success=True, message="Budget updated")
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))


@router.delete("/budgets/{budget_id}", response_model=BaseResponse)
async def delete_budget(budget_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import Budget

    with db_manager.get_session() as session:
        try:
            b = session.query(Budget).filter(Budget.id == budget_id, Budget.tenant_id == current_user['tenant_id']).first()
            if not b:
                raise HTTPException(status_code=404, detail="Budget not found")
            session.delete(b)
            session.commit()
            return BaseResponse(success=True, message="Budget deleted")
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))
