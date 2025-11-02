from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user
from modules.admin_module.services.order_commission_service import OrderCommissionService

router = APIRouter()

@router.get("/ordercommissions", response_model=PaginatedResponse)
async def get_order_commissions(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.order_commission import OrderCommission
    
    with db_manager.get_session() as session:
        query = session.query(OrderCommission).filter(
            OrderCommission.tenant_id == current_user["tenant_id"],
            OrderCommission.is_deleted == False
        )
        
        total = query.count()
        commissions = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        commission_data = []
        for comm in commissions:
            commission_data.append({
                "id": comm.id,
                "commission_number": comm.order_commission_number,
                "order_type": comm.order_type,
                "order_id": comm.order_id,
                "order_number": comm.order_number,
                "agency_id": comm.agency_id,
                "agency_name": comm.agency_name,
                "agency_phone": comm.agency_phone,
                "total_amount": float(comm.total_amount) if comm.total_amount else 0,
                "disc_percentage": float(comm.disc_percentage) if comm.disc_percentage else 0,
                "disc_amount": float(comm.disc_amount) if comm.disc_amount else 0,
                "roundoff": float(comm.roundoff) if comm.roundoff else 0,
                "final_amount": float(comm.final_amount) if comm.final_amount else 0,
                "created_at": comm.created_at.isoformat() if comm.created_at else None,
                "created_by": comm.created_by,
                "updated_at": comm.updated_at.isoformat() if comm.updated_at else None,
                "updated_by": comm.updated_by
            })
    
    return PaginatedResponse(
        success=True,
        message="Order commissions retrieved successfully",
        data=commission_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/ordercommissions", response_model=BaseResponse)
async def create_order_commission(
    commission_data: Dict[str, Any], 
    current_user: dict = Depends(get_current_user)
):
    # Validate order_type
    order_type = commission_data.get('order_type')
    if not order_type or order_type not in ['Products', 'Tests']:
        raise HTTPException(status_code=400, detail="order_type must be 'Products' or 'Tests'")
    
    service = OrderCommissionService()
    commission_data["tenant_id"] = current_user["tenant_id"]
    commission_data["created_by"] = current_user["username"]
    
    # Extract items data if provided
    items_data = commission_data.pop('items', None)
    if items_data:
        for item in items_data:
            item["created_by"] = current_user["username"]
    
    commission = service.create(commission_data, items_data)
    
    return BaseResponse(
        success=True,
        message="Order commission created successfully",
        data={"id": commission.id}
    )

@router.get("/ordercommissions/{commission_id}", response_model=BaseResponse)
async def get_order_commission(commission_id: int, current_user: dict = Depends(get_current_user)):
    service = OrderCommissionService()
    commission = service.get_by_id(commission_id, current_user["tenant_id"])
    
    if not commission:
        raise HTTPException(status_code=404, detail="Order commission not found")
    
    # Get items
    items = service.get_items_by_commission_id(commission_id, current_user["tenant_id"])
    items_data = []
    for item in items:
        items_data.append({
            "id": item.id,
            "item_type": item.item_type,
            "item_id": item.item_id,
            "item_name": item.item_name,
            "item_rate": float(item.item_rate) if item.item_rate else 0,
            "commission_percentage": float(item.commission_percentage) if item.commission_percentage else 0,
            "commission_value": float(item.commission_value) if item.commission_value else 0,
            "gst_percentage": float(item.gst_percentage) if item.gst_percentage else 0,
            "gst_amount": float(item.gst_amount) if item.gst_amount else 0,
            "cess_percentage": float(item.cess_percentage) if item.cess_percentage else 0,
            "cess_amount": float(item.cess_amount) if item.cess_amount else 0,
            "total_amount": float(item.total_amount) if item.total_amount else 0,
            "discount_percentage": float(item.discount_percentage) if item.discount_percentage else 0,
            "discount_amount": float(item.discount_amount) if item.discount_amount else 0,
            "roundoff": float(item.roundoff) if item.roundoff else 0,
            "final_amount": float(item.final_amount) if item.final_amount else 0
        })
    
    return BaseResponse(
        success=True,
        message="Order commission retrieved successfully",
        data={
            "id": commission.id,
            "commission_number": commission.order_commission_number,
            "order_type": commission.order_type,
            "order_id": commission.order_id,
            "order_number": commission.order_number,
            "agency_id": commission.agency_id,
            "agency_name": commission.agency_name,
            "agency_phone": commission.agency_phone,
            "notes": commission.notes,
            "total_amount": float(commission.total_amount) if commission.total_amount else 0,
            "disc_percentage": float(commission.disc_percentage) if commission.disc_percentage else 0,
            "disc_amount": float(commission.disc_amount) if commission.disc_amount else 0,
            "roundoff": float(commission.roundoff) if commission.roundoff else 0,
            "final_amount": float(commission.final_amount) if commission.final_amount else 0,
            "created_at": commission.created_at.isoformat() if commission.created_at else None,
            "created_by": commission.created_by,
            "updated_at": commission.updated_at.isoformat() if commission.updated_at else None,
            "updated_by": commission.updated_by,
            "items": items_data
        }
    )

@router.put("/ordercommissions/{commission_id}", response_model=BaseResponse)
async def update_order_commission(
    commission_id: int, 
    commission_data: Dict[str, Any], 
    current_user: dict = Depends(get_current_user)
):
    # Validate order_type
    order_type = commission_data.get('order_type')
    if order_type and order_type not in ['Products', 'Tests']:
        raise HTTPException(status_code=400, detail="order_type must be 'Products' or 'Tests'")
    
    service = OrderCommissionService()
    commission_data["updated_by"] = current_user["username"]
    
    # Extract items data if provided
    items_data = commission_data.pop('items', None)
    if items_data:
        for item in items_data:
            item["updated_by"] = current_user["username"]
    
    commission = service.update(commission_id, commission_data, items_data)
    
    if not commission:
        raise HTTPException(status_code=404, detail="Order commission not found")
    
    return BaseResponse(success=True, message="Order commission updated successfully")

@router.delete("/ordercommissions/{commission_id}", response_model=BaseResponse)
async def delete_order_commission(commission_id: int, current_user: dict = Depends(get_current_user)):
    service = OrderCommissionService()
    success = service.delete(commission_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Order commission not found")
    
    return BaseResponse(success=True, message="Order commission deleted successfully")