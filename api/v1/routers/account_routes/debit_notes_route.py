from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from modules.account_module.models.debit_note_schemas import (
    DebitNoteRequest, DebitNoteResponse, DebitNoteListResponse
)
from modules.account_module.services.debit_note_service import DebitNoteService
from modules.account_module.services.debit_note_validation_service import DebitNoteValidationService
import math
from datetime import date

router = APIRouter()


@router.post("/debit-notes", response_model=BaseResponse)
async def create_debit_note(note_data: DebitNoteRequest, current_user: dict = Depends(get_current_user)):
    """Create debit note for purchase adjustments with automatic accounting entries"""
    try:
        note_id = DebitNoteService.create_debit_note(
            note_data.dict(), 
            current_user['tenant_id'], 
            current_user['username']
        )
        
        # Validate voucher creation if status is POSTED
        validation_data = {"id": note_id}
        if note_data.status == 'POSTED':
            validation_result = DebitNoteValidationService.validate_voucher_creation(
                note_id, current_user['tenant_id']
            )
            validation_data.update({
                "voucher_created": validation_result['voucher_exists'],
                "accounting_balanced": validation_result.get('accounting_validation', {}).get('balanced', False)
            })
        
        return BaseResponse(
            success=True,
            message="Debit note created successfully",
            data=validation_data
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/debit-notes", response_model=PaginatedResponse)
async def get_debit_notes(
    pagination: PaginationParams = Depends(),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    date_from: Optional[date] = Query(None, description="Filter from date"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    current_user: dict = Depends(get_current_user)
):
    """Get paginated list of debit notes with filters"""
    try:
        filters = {}
        if supplier_id:
            filters['supplier_id'] = supplier_id
        if status:
            filters['status'] = status
        if date_from:
            filters['date_from'] = date_from
        if date_to:
            filters['date_to'] = date_to
        
        result = DebitNoteService.get_debit_notes_list(
            current_user['tenant_id'],
            pagination.page,
            pagination.per_page,
            filters
        )
        
        return PaginatedResponse(
            success=True,
            message="Debit notes retrieved successfully",
            **result
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/debit-notes/{note_id}", response_model=BaseResponse)
async def get_debit_note(note_id: int, current_user: dict = Depends(get_current_user)):
    """Get debit note by ID with items"""
    try:
        note = DebitNoteService.get_debit_note_by_id(note_id, current_user['tenant_id'])
        
        if not note:
            raise HTTPException(status_code=404, detail="Debit note not found")
        
        return BaseResponse(
            success=True,
            message="Debit note retrieved successfully",
            data=note
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/debit-notes/{note_id}/status", response_model=BaseResponse)
async def update_debit_note_status(
    note_id: int,
    status_data: Dict[str, str],
    current_user: dict = Depends(get_current_user)
):
    """Update debit note status"""
    try:
        status = status_data.get('status')
        if not status:
            raise HTTPException(status_code=400, detail="Status is required")
        
        valid_statuses = {'DRAFT', 'POSTED', 'PAID', 'PARTIALLY_PAID', 'CANCELLED'}
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        success = DebitNoteService.update_debit_note_status(
            note_id, status, current_user['tenant_id'], current_user['username']
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Debit note not found")
        
        # Validate voucher creation if status is POSTED
        validation_data = None
        if status == 'POSTED':
            validation_result = DebitNoteValidationService.validate_voucher_creation(
                note_id, current_user['tenant_id']
            )
            validation_data = {
                "voucher_created": validation_result['voucher_exists'],
                "accounting_balanced": validation_result.get('accounting_validation', {}).get('balanced', False)
            }
        
        return BaseResponse(
            success=True,
            message=f"Debit note status updated to {status}",
            data=validation_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/debit-notes/{note_id}/validate-voucher", response_model=BaseResponse)
async def validate_debit_note_voucher(note_id: int, current_user: dict = Depends(get_current_user)):
    """Validate voucher entries for debit note"""
    try:
        validation_result = DebitNoteValidationService.validate_voucher_creation(
            note_id, current_user['tenant_id']
        )
        
        if not validation_result['valid']:
            return BaseResponse(
                success=False,
                message=validation_result.get('error', 'Validation failed'),
                data=validation_result
            )
        
        # Get account configurations for reference
        account_configs = DebitNoteValidationService.get_account_configurations(
            current_user['tenant_id']
        )
        validation_result['account_configurations'] = account_configs
        
        return BaseResponse(
            success=True,
            message="Debit note voucher validation completed",
            data=validation_result
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
