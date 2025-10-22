from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from sqlalchemy import or_
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user
from modules.admin_module.services.agency_commission_service import AgencyCommissionService

router = APIRouter()

@router.get("/agencycommissions", response_model=PaginatedResponse)
async def get_agency_commissions(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.admin_module.models.agency_commission import AgencyCommission
    from modules.admin_module.models.agency import Agency
    
    with db_manager.get_session() as session:
        query = session.query(AgencyCommission).filter(
            AgencyCommission.tenant_id == current_user["tenant_id"],
            AgencyCommission.is_deleted == False
        )
        
        total = query.count()
        commissions = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        commission_data = []
        for comm in commissions:
            agency = session.query(Agency).filter(Agency.id == comm.agency_id).first()
            commission_data.append({
                "id": comm.id,
                "agency_id": comm.agency_id,
                "agency_name": agency.name if agency else None,
                "product_type": comm.product_type,
                "product_id": comm.product_id,
                "product_name": comm.product_name,
                "product_rate": float(comm.product_rate) if comm.product_rate else None,
                "notes": comm.notes,
                "commission_type": comm.commission_type,
                "commission_value": float(comm.commission_value) if comm.commission_value else None,
                "effective_from": comm.effective_from.isoformat() if comm.effective_from else None,
                "effective_to": comm.effective_to.isoformat() if comm.effective_to else None,
                "created_at": comm.created_at.isoformat() if comm.created_at else None,
                "created_by": comm.created_by,
                "updated_at": comm.updated_at.isoformat() if comm.updated_at else None,
                "updated_by": comm.updated_by
            })
    
    return PaginatedResponse(
        success=True,
        message="Agency commissions retrieved successfully",
        data=commission_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/agencycommissions", response_model=BaseResponse)
async def create_agency_commission(commission_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    # Validate product_type
    product_type = commission_data.get('product_type')
    if not product_type or product_type not in ['Products', 'Tests']:
        raise HTTPException(status_code=400, detail="product_type must be 'Products' or 'Tests'")
    
    # Validate commission_type
    commission_type = commission_data.get('commission_type')
    if commission_type and commission_type not in ['', 'Inherit_default', 'Percentage', 'Fixed']:
        raise HTTPException(status_code=400, detail="commission_type must be null/empty, 'Inherit_default', 'Percentage', or 'Fixed'")
    
    # Convert empty strings to None for date and numeric fields
    for field in ['effective_from', 'effective_to', 'commission_value', 'product_rate']:
        if field in commission_data and commission_data[field] == '':
            commission_data[field] = None
    
    service = AgencyCommissionService()
    commission_data["tenant_id"] = current_user["tenant_id"]
    commission_data["created_by"] = current_user["username"]
    commission = service.create(commission_data)
    
    return BaseResponse(
        success=True,
        message="Agency commission created successfully",
        data={"id": commission.id}
    )

@router.get("/agencycommissions/{commission_id}", response_model=BaseResponse)
async def get_agency_commission(commission_id: int, current_user: dict = Depends(get_current_user)):
    service = AgencyCommissionService()
    commission = service.get_by_id(commission_id, current_user["tenant_id"])
    
    if not commission:
        raise HTTPException(status_code=404, detail="Agency commission not found")
    
    return BaseResponse(
        success=True,
        message="Agency commission retrieved successfully",
        data={
            "id": commission.id,
            "agency_id": commission.agency_id,
            "product_type": commission.product_type,
            "product_id": commission.product_id,
            "product_name": commission.product_name,
            "product_rate": float(commission.product_rate) if commission.product_rate else None,
            "notes": commission.notes,
            "commission_type": commission.commission_type,
            "commission_value": float(commission.commission_value) if commission.commission_value else None,
            "effective_from": commission.effective_from.isoformat() if commission.effective_from else None,
            "effective_to": commission.effective_to.isoformat() if commission.effective_to else None,
            "created_at": commission.created_at.isoformat() if commission.created_at else None,
            "created_by": commission.created_by,
            "updated_at": commission.updated_at.isoformat() if commission.updated_at else None,
            "updated_by": commission.updated_by
        }
    )

@router.put("/agencycommissions/{commission_id}", response_model=BaseResponse)
async def update_agency_commission(commission_id: int, commission_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    # Validate product_type
    product_type = commission_data.get('product_type')
    if product_type and product_type not in ['Products', 'Tests']:
        raise HTTPException(status_code=400, detail="product_type must be 'Products' or 'Tests'")
    
    # Validate commission_type
    commission_type = commission_data.get('commission_type')
    if commission_type and commission_type not in ['', 'Inherit_default', 'Percentage', 'Fixed']:
        raise HTTPException(status_code=400, detail="commission_type must be null/empty, 'Inherit_default', 'Percentage', or 'Fixed'")
    
    service = AgencyCommissionService()
    commission_data["updated_by"] = current_user["username"]
    
    # Convert empty strings to None for date and numeric fields
    for field in ['effective_from', 'effective_to', 'commission_value', 'product_rate']:
        if field in commission_data and commission_data[field] == '':
            commission_data[field] = None
    
    commission = service.update(commission_id, commission_data)
    
    if not commission:
        raise HTTPException(status_code=404, detail="Agency commission not found")
    
    return BaseResponse(success=True, message="Agency commission updated successfully")

@router.delete("/agencycommissions/{commission_id}", response_model=BaseResponse)
async def delete_agency_commission(commission_id: int, current_user: dict = Depends(get_current_user)):
    service = AgencyCommissionService()
    success = service.delete(commission_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Agency commission not found")
    
    return BaseResponse(success=True, message="Agency commission deleted successfully")
