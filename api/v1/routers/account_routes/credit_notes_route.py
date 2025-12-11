from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from modules.account_module.models.credit_note_schemas import (
    CreditNoteRequest, CreditNoteResponse, CreditNoteListResponse
)
from modules.account_module.services.credit_note_service import CreditNoteService
from modules.account_module.services.credit_note_validation_service import CreditNoteValidationService
import math
from datetime import date

router = APIRouter()


@router.post("/credit-notes", response_model=BaseResponse)
async def create_credit_note(note_data: CreditNoteRequest, current_user: dict = Depends(get_current_user)):
    """Create credit note for sales returns with automatic accounting entries"""
    try:
        note_id = CreditNoteService.create_credit_note(
            note_data.dict(), 
            current_user['tenant_id'], 
            current_user['username']
        )
        
        # Validate voucher creation if status is POSTED
        validation_data = {"id": note_id}
        if note_data.status == 'POSTED':
            validation_result = CreditNoteValidationService.validate_voucher_creation(
                note_id, current_user['tenant_id']
            )
            validation_data.update({
                "voucher_created": validation_result['voucher_exists'],
                "accounting_balanced": validation_result.get('accounting_validation', {}).get('balanced', False)
            })
        
        return BaseResponse(
            success=True,
            message="Credit note created successfully",
            data=validation_data
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/credit-notes", response_model=PaginatedResponse)
async def get_credit_notes(
    pagination: PaginationParams = Depends(),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    date_from: Optional[date] = Query(None, description="Filter from date"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    current_user: dict = Depends(get_current_user)
):
    """Get paginated list of credit notes with filters"""
    try:
        filters = {}
        if customer_id:
            filters['customer_id'] = customer_id
        if status:
            filters['status'] = status
        if date_from:
            filters['date_from'] = date_from
        if date_to:
            filters['date_to'] = date_to
        
        result = CreditNoteService.get_credit_notes_list(
            current_user['tenant_id'],
            pagination.page,
            pagination.per_page,
            filters
        )
        
        return PaginatedResponse(
            success=True,
            message="Credit notes retrieved successfully",
            **result
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/credit-notes/{note_id}", response_model=BaseResponse)
async def get_credit_note(note_id: int, current_user: dict = Depends(get_current_user)):
    """Get credit note by ID with items"""
    try:
        note = CreditNoteService.get_credit_note_by_id(note_id, current_user['tenant_id'])
        
        if not note:
            raise HTTPException(status_code=404, detail="Credit note not found")
        
        return BaseResponse(
            success=True,
            message="Credit note retrieved successfully",
            data=note
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/credit-notes/{note_id}/status", response_model=BaseResponse)
async def update_credit_note_status(
    note_id: int,
    status_data: Dict[str, str],
    current_user: dict = Depends(get_current_user)
):
    """Update credit note status"""
    try:
        status = status_data.get('status')
        if not status:
            raise HTTPException(status_code=400, detail="Status is required")
        
        valid_statuses = {'DRAFT', 'POSTED', 'APPLIED', 'CANCELLED'}
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        success = CreditNoteService.update_credit_note_status(
            note_id, status, current_user['tenant_id'], current_user['username']
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Credit note not found")
        
        # Validate voucher creation if status is POSTED
        validation_data = None
        if status == 'POSTED':
            validation_result = CreditNoteValidationService.validate_voucher_creation(
                note_id, current_user['tenant_id']
            )
            validation_data = {
                "voucher_created": validation_result['voucher_exists'],
                "accounting_balanced": validation_result.get('accounting_validation', {}).get('balanced', False)
            }
        
        return BaseResponse(
            success=True,
            message=f"Credit note status updated to {status}",
            data=validation_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/credit-notes/{note_id}/validate-voucher", response_model=BaseResponse)
async def validate_credit_note_voucher(note_id: int, current_user: dict = Depends(get_current_user)):
    """Validate voucher entries for credit note"""
    try:
        validation_result = CreditNoteValidationService.validate_voucher_creation(
            note_id, current_user['tenant_id']
        )
        
        if not validation_result['valid']:
            return BaseResponse(
                success=False,
                message=validation_result.get('error', 'Validation failed'),
                data=validation_result
            )
        
        # Get account configurations for reference
        account_configs = CreditNoteValidationService.get_account_configurations(
            current_user['tenant_id']
        )
        validation_result['account_configurations'] = account_configs
        
        return BaseResponse(
            success=True,
            message="Credit note voucher validation completed",
            data=validation_result
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
