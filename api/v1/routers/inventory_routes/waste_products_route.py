from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from modules.inventory_module.models.product_waste_schemas import ProductWasteRequest, ProductWasteResponse
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
        "warehouse_id": waste.warehouse_id,
        "warehouse_name": waste.warehouse_name,
        "waste_date": waste.waste_date.isoformat() if waste.waste_date else None,
        "reason": waste.reason,
        "total_quantity": float(waste.total_quantity) if waste.total_quantity else 0,
        "total_cost_base": float(waste.total_cost_base) if waste.total_cost_base else 0,
        "total_cost_foreign": float(waste.total_cost_foreign) if waste.total_cost_foreign else None,
        "currency_id": waste.currency_id,
        "exchange_rate": float(waste.exchange_rate) if waste.exchange_rate else 1,
        "voucher_id": waste.voucher_id,
        "is_active": waste.is_active,
        "is_deleted": waste.is_deleted,
        "created_at": waste.created_at.isoformat() if waste.created_at else None,
        "created_by": waste.created_by,
        "updated_at": waste.updated_at.isoformat() if waste.updated_at else None,
        "updated_by": waste.updated_by,
        "items": [{
            "id": item['id'],
            "line_no": item['line_no'],
            "product_id": item['product_id'],
            "product_name": item['product_name'],
            "batch_number": item['batch_number'],
            "quantity": float(item['quantity']) if item['quantity'] else 0,
            "unit_cost_base": float(item['unit_cost_base']) if item['unit_cost_base'] else 0,
            "total_cost_base": float(item['total_cost_base']) if item['total_cost_base'] else 0,
            "currency_id": item['currency_id'],
            "unit_cost_foreign": float(item['unit_cost_foreign']) if item['unit_cost_foreign'] else None,
            "total_cost_foreign": float(item['total_cost_foreign']) if item['total_cost_foreign'] else None,
            "exchange_rate": float(item['exchange_rate']) if item['exchange_rate'] else 1,
            "reason": item['reason']
        } for item in waste.items]
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
async def create_product_waste(waste_data: ProductWasteRequest, current_user: dict = Depends(get_current_user)):
    """
    Create a new product waste record with multiple line items.
    
    Header Required fields:
    - waste_number: Unique reference number
    - waste_date: Date of waste occurrence
    - reason: General reason for waste
    - items: Array of waste line items (at least 1 required)
    
    Header Optional fields:
    - warehouse_id: Warehouse where waste occurred
    - currency_id: Currency ID (defaults to tenant's base currency if not provided)
    - voucher_id: Link to accounting voucher
    - is_active: Active status (default: True)
    
    Item Required fields (per line item):
    - line_no: Sequential line number
    - product_id: Product being wasted
    - quantity: Quantity wasted (must be > 0)
    - unit_cost_base: Unit cost in base currency
    
    Item Optional fields:
    - batch_number: Batch number if applicable
    - unit_cost_foreign: Unit cost in foreign currency
    - reason: Item-specific reason (overrides header reason)
    
    Note: 
    - Total quantities and costs are automatically calculated from line items
    - exchange_rate is automatically set to 1.0 for base currency
    - currency_id defaults to tenant's base currency if not provided
    """
    from modules.inventory_module.services.product_waste_service import ProductWasteService

    product_waste_service = ProductWasteService()
    # Convert Pydantic model to dict for service layer
    waste_dict = waste_data.model_dump()
    waste_id = product_waste_service.create(waste_dict)
    return BaseResponse(
        success=True,
        message="Product waste recorded successfully",
        data={"id": waste_id}
    )


@router.delete("/waste-products/{waste_id}", response_model=BaseResponse)
async def delete_product_waste(waste_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.inventory_module.models.product_waste_entity import ProductWaste
    from core.shared.utils.session_manager import session_manager

    with db_manager.get_session() as session:
        waste = session.query(ProductWaste).filter(
            ProductWaste.id == waste_id,
            ProductWaste.tenant_id == current_user['tenant_id']
        ).first()
        if not waste:
            raise HTTPException(status_code=404, detail="Product waste not found")

        # Soft delete header and all items (cascade)
        waste.is_deleted = True
        waste.updated_by = session_manager.get_current_username()
        
        # Also soft delete all items
        for item in waste.items:
            item.is_deleted = True
            item.updated_by = session_manager.get_current_username()
        
        session.commit()

    return BaseResponse(success=True, message="Product waste deleted successfully")
