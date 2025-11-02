from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import math
from api.schemas.common import PaginatedResponse, BaseResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user

router = APIRouter()


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
        try:
            series = session.query(VoucherType).filter(
                VoucherType.id == series_id,
                VoucherType.tenant_id == current_user['tenant_id']
            ).first()

            if not series:
                raise HTTPException(status_code=404, detail="Voucher series not found")

            if 'name' in series_data:
                series.name = series_data['name']
            if 'code' in series_data:
                series.code = series_data['code']
            if 'prefix' in series_data:
                series.prefix = series_data['prefix']
            if 'is_active' in series_data:
                series.is_active = series_data['is_active']

            session.commit()

            return BaseResponse(
                success=True,
                message="Voucher series updated successfully",
                data={"id": series_id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))
