from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
import io
import csv
from datetime import datetime

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.schemas.health_schema.prescription_schemas import PrescriptionCreate, PrescriptionUpdate
from sqlalchemy import or_
import math
from api.middleware.auth_middleware import get_current_user
from modules.health_module.services.prescription_service import PrescriptionService
from modules.health_module.services.patient_service import PatientService
from modules.health_module.services.doctor_service import DoctorService
from modules.health_module.services.appointment_service import AppointmentService
from modules.health_module.services.medical_record_service import MedicalRecordService
from modules.admin_module.models.agency import Agency

router = APIRouter()
# Prescription endpoints
@router.get("/prescriptions", response_model=PaginatedResponse)
async def get_prescriptions(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    try:
        prescription_service = PrescriptionService()
        result = prescription_service.get_all(
            tenant_id=current_user.get('tenant_id'),
            search=pagination.search,
            offset=pagination.offset,
            limit=pagination.per_page
        )
        
        return PaginatedResponse(
            success=True,
            message="Prescriptions retrieved successfully",
            data=result['prescriptions'],
            total=result['total'],
            page=pagination.page,
            per_page=pagination.per_page,
            total_pages=math.ceil(result['total'] / pagination.per_page)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving prescriptions: {str(e)}")

@router.post("/prescriptions", response_model=BaseResponse)
async def create_prescription(prescription_data: PrescriptionCreate, current_user: dict = Depends(get_current_user)):
    try:
        prescription_service = PrescriptionService()
        prescription_dict = prescription_data.model_dump(exclude={'items', 'test_items'})
        prescription_dict['tenant_id'] = current_user.get('tenant_id')
        prescription_dict['created_by'] = current_user.get('username', 'system')
        
        items_data = [item.model_dump() for item in prescription_data.items]
        test_items_data = [test_item.model_dump() for test_item in prescription_data.test_items]
        
        for item in items_data:
            item['created_by'] = current_user.get('username')
        
        for test_item in test_items_data:
            test_item['created_by'] = current_user.get('username')
        
        result = prescription_service.create(prescription_dict, items_data, test_items_data)
        
        return BaseResponse(
            success=True,
            message="Prescription created successfully",
            data=result
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating prescription: {str(e)}")

@router.put("/prescriptions/{prescription_id}", response_model=BaseResponse)
async def update_prescription(prescription_id: int, prescription_data: PrescriptionUpdate, current_user: dict = Depends(get_current_user)):
    try:
        prescription_service = PrescriptionService()
        prescription_dict = prescription_data.model_dump(exclude={'items', 'test_items'}, exclude_unset=True)
        prescription_dict['updated_by'] = current_user.get('username', 'system')
        
        items_data = None
        test_items_data = None
        
        if prescription_data.items is not None:
            items_data = [item.model_dump() for item in prescription_data.items]
            for item in items_data:
                item['updated_by'] = current_user.get('username')
        
        if prescription_data.test_items is not None:
            test_items_data = [test_item.model_dump() for test_item in prescription_data.test_items]
            for test_item in test_items_data:
                test_item['updated_by'] = current_user.get('username')
        
        result = prescription_service.update(prescription_id, prescription_dict, items_data, test_items_data)
        if not result:
            raise HTTPException(status_code=404, detail="Prescription not found")
        return BaseResponse(
            success=True,
            message="Prescription updated successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating prescription: {str(e)}")

@router.delete("/prescriptions/{prescription_id}", response_model=BaseResponse)
async def delete_prescription(prescription_id: int, current_user: dict = Depends(get_current_user)):
    try:
        prescription_service = PrescriptionService()
        success = prescription_service.delete(prescription_id, current_user.get('tenant_id'))
        if not success:
            raise HTTPException(status_code=404, detail="Prescription not found")
        return BaseResponse(
            success=True,
            message="Prescription deleted successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting prescription: {str(e)}")

@router.get("/prescriptions/{prescription_id}", response_model=BaseResponse)
async def get_prescription(prescription_id: int, current_user: dict = Depends(get_current_user)):
    try:
        prescription_service = PrescriptionService()
        prescription_data = prescription_service.get_by_id(current_user.get('tenant_id'),prescription_id)
        
        if not prescription_data:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        return BaseResponse(
            success=True,
            message="Prescription retrieved successfully",
            data=prescription_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving prescription: {str(e)}")
