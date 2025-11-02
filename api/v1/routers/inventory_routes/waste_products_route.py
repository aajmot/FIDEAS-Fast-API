from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.get("/waste-products", response_model=PaginatedResponse)
async def get_product_wastes(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from modules.inventory_module.services.product_waste_service import ProductWasteService

    product_waste_service = ProductWasteService()
    wastes = product_waste_service.get_all(page=pagination.page, page_size=pagination.per_page)
    total = product_waste_service.get_total_count()

    waste_data = [{
        "id": waste.id,
        "waste_number": waste.waste_number,
        "product_name": waste.product_name,
        "batch_number": waste.batch_number,
        "quantity": float(waste.quantity),
        "unit_cost": float(waste.unit_cost),
        "total_cost": float(waste.total_cost),
        "reason": waste.reason,
        "waste_date": waste.waste_date.isoformat() if waste.waste_date else None
    } for waste in wastes]

    return PaginatedResponse(
        success=True,
        message="Product wastes retrieved successfully",
        data=waste_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )


@router.post("/waste-products", response_model=BaseResponse)
async def create_product_waste(waste_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from modules.inventory_module.services.product_waste_service import ProductWasteService

    product_waste_service = ProductWasteService()
    waste_id = product_waste_service.create(waste_data)
    return BaseResponse(
        success=True,
        message="Product waste recorded successfully",
        data={"id": waste_id}
    )


@router.delete("/waste-products/{waste_id}", response_model=BaseResponse)
async def delete_product_waste(waste_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.inventory_module.models.entities import ProductWaste

    with db_manager.get_session() as session:
        waste = session.query(ProductWaste).filter(ProductWaste.id == waste_id).first()
        if not waste:
            raise HTTPException(status_code=404, detail="Product waste not found")

        session.delete(waste)
        session.commit()

    return BaseResponse(success=True, message="Product waste deleted successfully")
