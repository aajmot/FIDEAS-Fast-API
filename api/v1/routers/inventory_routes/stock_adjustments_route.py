from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from modules.inventory_module.models.stock_adjustment_schemas import StockAdjustmentRequest, StockAdjustmentResponse
from api.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.get("/stock-adjustments", response_model=PaginatedResponse)
async def get_stock_adjustments(
    pagination: PaginationParams = Depends(),
    current_user: dict = Depends(get_current_user)
):
    """
    Get paginated list of stock adjustments with line items.
    
    Returns all stock adjustments for the current tenant with their line items.
    Results are ordered by adjustment_date (descending).
    """
    from modules.inventory_module.services.stock_adjustment_service import StockAdjustmentService

    adjustment_service = StockAdjustmentService()
    adjustments = adjustment_service.get_all(page=pagination.page, page_size=pagination.per_page)
    total = adjustment_service.get_total_count()

    adjustment_data = [{
        "id": adj.id,
        "adjustment_number": adj.adjustment_number,
        "warehouse_id": adj.warehouse_id,
        "warehouse_name": adj.warehouse_name,
        "adjustment_date": adj.adjustment_date.isoformat() if adj.adjustment_date else None,
        "adjustment_type": adj.adjustment_type,
        "reason": adj.reason,
        "total_items": adj.total_items,
        "net_quantity_change": float(adj.net_quantity_change) if adj.net_quantity_change else 0,
        "total_cost_impact": float(adj.total_cost_impact) if adj.total_cost_impact else 0,
        "currency_id": adj.currency_id,
        "exchange_rate": float(adj.exchange_rate) if adj.exchange_rate else 1,
        "voucher_id": adj.voucher_id,
        "is_active": adj.is_active,
        "is_deleted": adj.is_deleted,
        "created_at": adj.created_at.isoformat() if adj.created_at else None,
        "created_by": adj.created_by,
        "updated_at": adj.updated_at.isoformat() if adj.updated_at else None,
        "updated_by": adj.updated_by,
        "items": [{
            "id": item['id'],
            "line_no": item['line_no'],
            "product_id": item['product_id'],
            "product_name": item['product_name'],
            "batch_number": item['batch_number'],
            "adjustment_qty": float(item['adjustment_qty']) if item['adjustment_qty'] else 0,
            "uom": item['uom'],
            "stock_before": float(item['stock_before']) if item['stock_before'] else 0,
            "stock_after": float(item['stock_after']) if item['stock_after'] else 0,
            "unit_cost_base": float(item['unit_cost_base']) if item['unit_cost_base'] else 0,
            "cost_impact": float(item['cost_impact']) if item['cost_impact'] else 0,
            "currency_id": item['currency_id'],
            "unit_cost_foreign": float(item['unit_cost_foreign']) if item['unit_cost_foreign'] else None,
            "cost_impact_foreign": float(item['cost_impact_foreign']) if item['cost_impact_foreign'] else None,
            "exchange_rate": float(item['exchange_rate']) if item['exchange_rate'] else 1,
            "reason": item['reason']
        } for item in adj.items]
    } for adj in adjustments]

    return PaginatedResponse(
        success=True,
        message="Stock adjustments retrieved successfully",
        data=adjustment_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )


@router.get("/stock-adjustments/{adjustment_id}", response_model=BaseResponse)
async def get_stock_adjustment(
    adjustment_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific stock adjustment by ID with all line items.
    """
    from modules.inventory_module.services.stock_adjustment_service import StockAdjustmentService

    adjustment_service = StockAdjustmentService()
    adjustment = adjustment_service.get_by_id(adjustment_id)
    
    if not adjustment:
        raise HTTPException(status_code=404, detail="Stock adjustment not found")

    adjustment_data = {
        "id": adjustment.id,
        "adjustment_number": adjustment.adjustment_number,
        "warehouse_id": adjustment.warehouse_id,
        "warehouse_name": adjustment.warehouse_name,
        "adjustment_date": adjustment.adjustment_date.isoformat() if adjustment.adjustment_date else None,
        "adjustment_type": adjustment.adjustment_type,
        "reason": adjustment.reason,
        "total_items": adjustment.total_items,
        "net_quantity_change": float(adjustment.net_quantity_change) if adjustment.net_quantity_change else 0,
        "total_cost_impact": float(adjustment.total_cost_impact) if adjustment.total_cost_impact else 0,
        "currency_id": adjustment.currency_id,
        "exchange_rate": float(adjustment.exchange_rate) if adjustment.exchange_rate else 1,
        "voucher_id": adjustment.voucher_id,
        "is_active": adjustment.is_active,
        "is_deleted": adjustment.is_deleted,
        "created_at": adjustment.created_at.isoformat() if adjustment.created_at else None,
        "created_by": adjustment.created_by,
        "updated_at": adjustment.updated_at.isoformat() if adjustment.updated_at else None,
        "updated_by": adjustment.updated_by,
        "items": [{
            "id": item['id'],
            "line_no": item['line_no'],
            "product_id": item['product_id'],
            "product_name": item['product_name'],
            "batch_number": item['batch_number'],
            "adjustment_qty": float(item['adjustment_qty']) if item['adjustment_qty'] else 0,
            "uom": item['uom'],
            "stock_before": float(item['stock_before']) if item['stock_before'] else 0,
            "stock_after": float(item['stock_after']) if item['stock_after'] else 0,
            "unit_cost_base": float(item['unit_cost_base']) if item['unit_cost_base'] else 0,
            "cost_impact": float(item['cost_impact']) if item['cost_impact'] else 0,
            "currency_id": item['currency_id'],
            "unit_cost_foreign": float(item['unit_cost_foreign']) if item['unit_cost_foreign'] else None,
            "cost_impact_foreign": float(item['cost_impact_foreign']) if item['cost_impact_foreign'] else None,
            "exchange_rate": float(item['exchange_rate']) if item['exchange_rate'] else 1,
            "reason": item['reason']
        } for item in adjustment.items]
    }

    return BaseResponse(
        success=True,
        message="Stock adjustment retrieved successfully",
        data=adjustment_data
    )


@router.post("/stock-adjustments", response_model=BaseResponse)
async def create_stock_adjustment(
    adjustment_data: StockAdjustmentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new stock adjustment with multiple line items.
    
    Header Required fields:
    - adjustment_number: Unique reference number
    - warehouse_id: Warehouse where adjustment is made
    - adjustment_date: Date of adjustment
    - adjustment_type: Type (PHYSICAL, DAMAGED, THEFT, OTHER)
    - reason: General reason for adjustment
    - items: Array of adjustment line items (at least 1 required)
    
    Header Optional fields:
    - currency_id: Currency ID (defaults to tenant's base currency)
    - voucher_id: Link to accounting voucher
    - is_active: Active status (default: True)
    
    Item Required fields (per line item):
    - line_no: Sequential line number
    - product_id: Product being adjusted
    - adjustment_qty: Quantity adjustment (+ve for increase, -ve for decrease)
    - uom: Unit of measurement (default: NOS)
    - unit_cost_base: Unit cost in base currency
    
    Item Optional fields:
    - batch_number: Batch number if applicable
    - stock_before: Current stock (auto-fetched if not provided)
    - unit_cost_foreign: Unit cost in foreign currency
    - reason: Item-specific reason (overrides header reason)
    
    Note: 
    - Calculated fields (stock_after, cost_impact, totals) are computed in service layer
    - Positive adjustment_qty increases stock, negative decreases
    - Stock transactions are automatically recorded
    """
    from modules.inventory_module.services.stock_adjustment_service import StockAdjustmentService

    adjustment_service = StockAdjustmentService()
    # Convert Pydantic model to dict for service layer
    adjustment_dict = adjustment_data.model_dump()
    adjustment_id = adjustment_service.create(adjustment_dict)
    
    return BaseResponse(
        success=True,
        message="Stock adjustment created successfully",
        data={"id": adjustment_id}
    )


@router.delete("/stock-adjustments/{adjustment_id}", response_model=BaseResponse)
async def delete_stock_adjustment(
    adjustment_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Soft delete a stock adjustment and all its line items.
    
    Note: This performs a soft delete (sets is_deleted=True) rather than 
    removing records from the database to maintain audit trail.
    """
    from core.database.connection import db_manager
    from modules.inventory_module.models.stock_adjustment_entity import StockAdjustment
    from core.shared.utils.session_manager import session_manager

    with db_manager.get_session() as session:
        adjustment = session.query(StockAdjustment).filter(
            StockAdjustment.id == adjustment_id,
            StockAdjustment.tenant_id == current_user['tenant_id']
        ).first()
        
        if not adjustment:
            raise HTTPException(status_code=404, detail="Stock adjustment not found")

        # Soft delete header and all items
        adjustment.is_deleted = True
        adjustment.updated_by = session_manager.get_current_username()
        
        # Also soft delete all items
        for item in adjustment.items:
            item.is_deleted = True
            item.updated_by = session_manager.get_current_username()
        
        session.commit()

    return BaseResponse(
        success=True,
        message="Stock adjustment deleted successfully"
    )
