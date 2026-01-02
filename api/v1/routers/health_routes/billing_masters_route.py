from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
import io
import csv
from datetime import datetime

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from sqlalchemy import or_
import math
from api.middleware.auth_middleware import get_current_user
from modules.health_module.services.patient_service import PatientService
from modules.health_module.services.doctor_service import DoctorService
from modules.health_module.services.appointment_service import AppointmentService
from modules.health_module.services.medical_record_service import MedicalRecordService
from modules.admin_module.models.agency import Agency

router = APIRouter()

# Billing Master endpoints
@router.get("/billing-masters", response_model=PaginatedResponse)
async def get_billing_masters(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.health_module.models.clinic_entities import ClinicBillingMaster
    
    with db_manager.get_session() as session:
        query = session.query(ClinicBillingMaster).filter(
            ClinicBillingMaster.is_deleted == False,
            ClinicBillingMaster.tenant_id == current_user.get('tenant_id')
        )
        
        if pagination.search:
            search_term = f"%{pagination.search}%"
            query = query.filter(or_(
                ClinicBillingMaster.description.ilike(search_term),
                ClinicBillingMaster.note.ilike(search_term)
            ))
        
        total = query.count()
        billing_masters = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        billing_master_data = [{
            "id": bm.id,
            "description": bm.description,
            "note": bm.note,
            "amount": float(bm.amount),
            "hsn_code": bm.hsn_code,
            "gst_percentage": float(bm.gst_percentage) if bm.gst_percentage else 0.0,
            "is_active": bm.is_active,
            "created_at": bm.created_at.isoformat() if bm.created_at else None,
            "updated_at": bm.updated_at.isoformat() if bm.updated_at else None
        } for bm in billing_masters]
    
    return PaginatedResponse(
        success=True,
        message="Billing masters retrieved successfully",
        data=billing_master_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/billing-masters", response_model=BaseResponse)
async def create_billing_master(billing_master_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from modules.health_module.services.billing_master_service import BillingMasterService
    
    billing_master_service = BillingMasterService()
    # Always use tenant_id from logged-in user, never from request
    billing_master_data['tenant_id'] = current_user.get('tenant_id')
    billing_master_data['created_by'] = current_user.get('username')
    billing_master = billing_master_service.create(billing_master_data)
    return BaseResponse(
        success=True,
        message="Billing master created successfully",
        data={"id": billing_master['id']}
    )

@router.get("/billing-masters/export-template")
async def export_billing_masters_template(current_user: dict = Depends(get_current_user)):
    from modules.health_module.services.billing_master_service import BillingMasterService
    
    billing_master_service = BillingMasterService()
    template_content = billing_master_service.export_template()
    
    return StreamingResponse(
        io.BytesIO(template_content.encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=billing_masters_template.csv"}
    )

@router.post("/billing-masters/import", response_model=BaseResponse)
async def import_billing_masters(request_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from modules.health_module.services.billing_master_service import BillingMasterService
    
    csv_content = request_data.get('csv_content', '')
    
    if not csv_content:
        raise HTTPException(status_code=400, detail="CSV content is required")
    
    billing_master_service = BillingMasterService()
    result = billing_master_service.import_billing_masters(csv_content, current_user.get('tenant_id', 1))
    
    return BaseResponse(
        success=True,
        message=f"Imported {result['imported']} billing masters successfully",
        data=result
    )

@router.get("/billing-masters/{billing_master_id}", response_model=BaseResponse)
async def get_billing_master(billing_master_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.health_module.models.clinic_entities import ClinicBillingMaster
    
    with db_manager.get_session() as session:
        billing_master = session.query(ClinicBillingMaster).filter(
            ClinicBillingMaster.id == billing_master_id,
            ClinicBillingMaster.is_deleted == False
        ).first()
        if not billing_master:
            raise HTTPException(status_code=404, detail="Billing master not found")
        
        billing_master_data = {
            "id": billing_master.id,
            "description": billing_master.description,
            "note": billing_master.note,
            "amount": float(billing_master.amount),
            "hsn_code": billing_master.hsn_code,
            "gst_percentage": float(billing_master.gst_percentage) if billing_master.gst_percentage else 0.0,
            "is_active": billing_master.is_active,
            "created_at": billing_master.created_at.isoformat() if billing_master.created_at else None,
            "updated_at": billing_master.updated_at.isoformat() if billing_master.updated_at else None
        }
    
    return BaseResponse(
        success=True,
        message="Billing master retrieved successfully",
        data=billing_master_data
    )

@router.put("/billing-masters/{billing_master_id}", response_model=BaseResponse)
async def update_billing_master(billing_master_id: int, billing_master_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from modules.health_module.services.billing_master_service import BillingMasterService
    
    billing_master_service = BillingMasterService()
    billing_master = billing_master_service.update(billing_master_id, billing_master_data)
    if not billing_master:
        raise HTTPException(status_code=404, detail="Billing master not found")
    return BaseResponse(
        success=True,
        message="Billing master updated successfully",
        data={"id": billing_master['id']}
    )

@router.delete("/billing-masters/{billing_master_id}", response_model=BaseResponse)
async def delete_billing_master(billing_master_id: int, current_user: dict = Depends(get_current_user)):
    from modules.health_module.services.billing_master_service import BillingMasterService
    
    billing_master_service = BillingMasterService()
    success = billing_master_service.delete(billing_master_id)
    if not success:
        raise HTTPException(status_code=404, detail="Billing master not found")
    return BaseResponse(
        success=True,
        message="Billing master deleted successfully"
    )

