from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import math
from sqlalchemy import or_

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.schemas.health_schema.lab_technician_schemas import (
    LabTechnicianCreate, 
    LabTechnicianUpdate, 
    LabTechnicianResponse
)
from api.middleware.auth_middleware import get_current_user
from modules.health_module.services.lab_technician_service import LabTechnicianService
from modules.health_module.models.lab_technician_entity import LabTechnician
from core.database.connection import db_manager

router = APIRouter()

@router.get("/lab-technicians", response_model=PaginatedResponse)
async def get_lab_technicians(
    pagination: PaginationParams = Depends(),
    name: Optional[str] = Query(None),
    phone: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    employment_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    with db_manager.get_session() as session:
        query = session.query(LabTechnician).filter(
            LabTechnician.tenant_id == current_user['tenant_id'],
            LabTechnician.is_deleted == False
        )
        
        if name:
            query = query.filter(LabTechnician.technician_name.ilike(f"%{name}%"))
        if phone:
            query = query.filter(LabTechnician.phone.ilike(f"%{phone}%"))
        if email:
            query = query.filter(LabTechnician.email.ilike(f"%{email}%"))
        if status:
            query = query.filter(LabTechnician.status == status)
        if employment_type:
            query = query.filter(LabTechnician.employment_type == employment_type)
        
        if pagination.search:
            search_term = f"%{pagination.search}%"
            query = query.filter(or_(
                LabTechnician.technician_code.ilike(search_term),
                LabTechnician.technician_name.ilike(search_term),
                LabTechnician.phone.ilike(search_term),
                LabTechnician.email.ilike(search_term),
                LabTechnician.specialization.ilike(search_term)
            ))
        
        total = query.count()
        technicians = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        technician_data = [{
            "id": t.id,
            "technician_code": t.technician_code,
            "technician_name": t.technician_name,
            "phone": t.phone,
            "email": t.email,
            "qualification": t.qualification,
            "specialization": t.specialization,
            "license_number": t.license_number,
            "license_expiry": t.license_expiry.isoformat() if t.license_expiry else None,
            "employment_type": t.employment_type,
            "status": t.status,
            "remarks": t.remarks,
            "created_at": t.created_at.isoformat() if t.created_at else None
        } for t in technicians]
    
    return PaginatedResponse(
        success=True,
        message="Lab technicians retrieved successfully",
        data=technician_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page) if total > 0 else 0
    )

@router.post("/lab-technicians", response_model=BaseResponse)
async def create_lab_technician(
    technician: LabTechnicianCreate,
    current_user: dict = Depends(get_current_user)
):
    service = LabTechnicianService()
    technician_data = technician.model_dump(exclude_unset=True)
    created = service.create(
        technician_data,
        tenant_id=current_user['tenant_id'],
        created_by=current_user.get('username', 'system')
    )
    return BaseResponse(
        success=True,
        message="Lab technician created successfully",
        data={"id": created.id, "technician_code": created.technician_code}
    )

@router.get("/lab-technicians/{technician_id}", response_model=BaseResponse)
async def get_lab_technician(
    technician_id: int,
    current_user: dict = Depends(get_current_user)
):
    service = LabTechnicianService()
    technician = service.get_by_id(technician_id, current_user['tenant_id'])
    if not technician:
        raise HTTPException(status_code=404, detail="Lab technician not found")
    
    technician_data = {
        "id": technician.id,
        "technician_code": technician.technician_code,
        "technician_name": technician.technician_name,
        "phone": technician.phone,
        "email": technician.email,
        "qualification": technician.qualification,
        "specialization": technician.specialization,
        "license_number": technician.license_number,
        "license_expiry": technician.license_expiry.isoformat() if technician.license_expiry else None,
        "employment_type": technician.employment_type,
        "status": technician.status,
        "remarks": technician.remarks,
        "created_at": technician.created_at.isoformat() if technician.created_at else None
    }
    
    return BaseResponse(
        success=True,
        message="Lab technician retrieved successfully",
        data=technician_data
    )

@router.put("/lab-technicians/{technician_id}", response_model=BaseResponse)
async def update_lab_technician(
    technician_id: int,
    technician: LabTechnicianUpdate,
    current_user: dict = Depends(get_current_user)
):
    service = LabTechnicianService()
    technician_data = technician.model_dump(exclude_unset=True)
    updated = service.update(
        technician_id,
        technician_data,
        tenant_id=current_user['tenant_id'],
        updated_by=current_user.get('username', 'system')
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Lab technician not found")
    
    return BaseResponse(
        success=True,
        message="Lab technician updated successfully",
        data={"id": updated.id}
    )

@router.delete("/lab-technicians/{technician_id}", response_model=BaseResponse)
async def delete_lab_technician(
    technician_id: int,
    current_user: dict = Depends(get_current_user)
):
    service = LabTechnicianService()
    success = service.delete(
        technician_id,
        tenant_id=current_user['tenant_id'],
        deleted_by=current_user.get('username', 'system')
    )
    if not success:
        raise HTTPException(status_code=404, detail="Lab technician not found")
    
    return BaseResponse(
        success=True,
        message="Lab technician deleted successfully"
    )
