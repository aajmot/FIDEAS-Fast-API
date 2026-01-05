from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from api.schemas.common import BaseResponse
from api.middleware.auth_middleware import get_current_user
from modules.account_module.services.payment_service import PaymentService
from modules.account_module.models.payment_enums import PaymentType, PartyType, PaymentStatus, PaymentMode
from modules.account_module.models.payment_schemas import (
    PaymentRequest,
    PaymentResponse,
    PaymentListResponse,
    ReconcilePaymentRequest,
    PaymentAllocationResponse
)

router = APIRouter()
payment_service = PaymentService()


class PaymentMetadataUpdate(BaseModel):
    """Schema for updating payment metadata only"""
    remarks: Optional[str] = Field(None, description="Remarks")
    tags: Optional[list[str]] = Field(None, description="Tags")
    reference_number: Optional[str] = Field(None, max_length=50, description="Reference number")


class PaymentReversalRequest(BaseModel):
    """Schema for reversing a payment"""
    reversal_date: Optional[datetime] = Field(None, description="Reversal date")
    reversal_remarks: str = Field(..., description="Reason for reversal")


class AdvancePaymentRequest(BaseModel):
    """Minimal schema for advance payment"""
    payment_number: str = Field(..., max_length=50, description="Payment number")
    party_id: int = Field(..., description="Party ID")
    party_type: PartyType = Field(..., description="Party type")
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    payment_mode: PaymentMode = Field(PaymentMode.CASH, description="Payment mode")
    instrument_number: Optional[str] = Field(None, description="Cheque/DD number")
    instrument_date: Optional[date] = Field(None, description="Instrument date")
    bank_name: Optional[str] = Field(None, description="Bank name")
    branch_name: Optional[str] = Field(None, description="Branch name")
    ifsc_code: Optional[str] = Field(None, description="IFSC code")
    transaction_reference: Optional[str] = Field(None, description="Transaction reference")
    remarks: Optional[str] = Field(None, description="Remarks")


class InvoicePaymentRequest(BaseModel):
    """Minimal schema for payment against invoice"""
    payment_number: str = Field(..., max_length=50, description="Payment number")
    invoice_id: int = Field(..., description="Invoice ID")
    invoice_type: str = Field(..., description="SALES or PURCHASE")
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    payment_mode: PaymentMode = Field(PaymentMode.CASH, description="Payment mode")
    instrument_number: Optional[str] = Field(None, description="Cheque/DD number")
    instrument_date: Optional[date] = Field(None, description="Instrument date")
    bank_name: Optional[str] = Field(None, description="Bank name")
    branch_name: Optional[str] = Field(None, description="Branch name")
    ifsc_code: Optional[str] = Field(None, description="IFSC code")
    transaction_reference: Optional[str] = Field(None, description="Transaction reference")
    remarks: Optional[str] = Field(None, description="Remarks")


class GatewayPaymentUpdateRequest(BaseModel):
    """Schema for updating payment with gateway response"""
    transaction_reference: str = Field(..., description="UPI/Gateway transaction reference")
    gateway_transaction_id: Optional[str] = Field(None, description="Gateway transaction ID")
    gateway_status: str = Field(..., description="Gateway status (SUCCESS/FAILED)")
    gateway_fee_base: Optional[Decimal] = Field(0, description="Gateway fee")
    gateway_response: Optional[str] = Field(None, description="Gateway response JSON")
    
    @validator('gateway_status')
    def validate_status(cls, v):
        if v not in ['SUCCESS', 'FAILED']:
            raise ValueError('gateway_status must be SUCCESS or FAILED')
        return v


@router.get("/payments", response_model=PaymentListResponse)
async def get_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    search: Optional[str] = Query(None),
    payment_type: Optional[PaymentType] = Query(None),
    party_type: Optional[PartyType] = Query(None),
    status: Optional[PaymentStatus] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    is_reconciled: Optional[bool] = Query(None),
    branch_id: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get all payments with pagination and filters"""
    result = payment_service.get_all_payments(
        page=page,
        page_size=page_size,
        search=search,
        payment_type=payment_type.value if payment_type else None,
        party_type=party_type.value if party_type else None,
        status=status.value if status else None,
        date_from=date_from,
        date_to=date_to,
        is_reconciled=is_reconciled,
        branch_id=branch_id
    )
    return result


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific payment by ID"""
    payment = payment_service.get_payment_by_id(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.post("/payments", response_model=PaymentResponse, status_code=201)
async def create_payment(
    payment: PaymentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new payment"""
    try:
        result = payment_service.create_payment(payment.dict())
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating payment: {str(e)}")


@router.put("/payments/{payment_id}/draft", response_model=PaymentResponse)
async def update_draft_payment(
    payment_id: int,
    payment: PaymentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update a DRAFT payment (full update allowed only for DRAFT status)"""
    try:
        existing = payment_service.get_payment_by_id(payment_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        if existing['status'] != PaymentStatus.DRAFT.value:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot fully update payment with status '{existing['status']}'. Only DRAFT payments can be fully updated."
            )
        
        result = payment_service.update_payment(payment_id, payment.dict())
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating payment: {str(e)}")


@router.patch("/payments/{payment_id}/metadata", response_model=PaymentResponse)
async def update_payment_metadata(
    payment_id: int,
    metadata: PaymentMetadataUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update payment metadata (remarks, tags, reference) - allowed for any status except RECONCILED"""
    try:
        existing = payment_service.get_payment_by_id(payment_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        if existing['is_reconciled']:
            raise HTTPException(
                status_code=400,
                detail="Cannot update reconciled payment metadata"
            )
        
        update_data = metadata.dict(exclude_none=True)
        result = payment_service.update_payment_metadata(payment_id, update_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating metadata: {str(e)}")


@router.post("/payments/{payment_id}/reverse", response_model=PaymentResponse)
async def reverse_payment(
    payment_id: int,
    reversal_request: PaymentReversalRequest,
    current_user: dict = Depends(get_current_user)
):
    """Reverse a posted payment (creates reversal entry)"""
    try:
        existing = payment_service.get_payment_by_id(payment_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        if existing['status'] not in [PaymentStatus.POSTED.value, PaymentStatus.RECONCILED.value]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot reverse payment with status '{existing['status']}'. Only POSTED or RECONCILED payments can be reversed."
            )
        
        if existing['is_refund']:
            raise HTTPException(status_code=400, detail="Cannot reverse a refund payment")
        
        result = payment_service.reverse_payment(
            payment_id,
            reversal_request.reversal_date,
            reversal_request.reversal_remarks
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reversing payment: {str(e)}")


@router.delete("/payments/{payment_id}", response_model=BaseResponse)
async def delete_payment(
    payment_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Soft delete a payment (only DRAFT or CANCELLED)"""
    try:
        result = payment_service.delete_payment(payment_id)
        if not result:
            raise HTTPException(status_code=404, detail="Payment not found")
        return BaseResponse(success=True, message="Payment deleted successfully", data={"id": payment_id})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting payment: {str(e)}")


@router.post("/payments/{payment_id}/reconcile", response_model=PaymentResponse)
async def reconcile_payment(
    payment_id: int,
    reconcile_data: ReconcilePaymentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Reconcile a payment"""
    try:
        result = payment_service.reconcile_payment(payment_id, reconcile_data.reconciled_at)
        if not result:
            raise HTTPException(status_code=404, detail="Payment not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reconciling payment: {str(e)}")


@router.get("/payments/{payment_id}/allocations", response_model=list[PaymentAllocationResponse])
async def get_payment_allocations(
    payment_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get all allocations for a specific payment"""
    try:
        allocations = payment_service.get_payment_allocations(payment_id)
        return allocations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching allocations: {str(e)}")


@router.get("/documents/{document_type}/{document_id}/payments", response_model=list[PaymentAllocationResponse])
async def get_document_payments(
    document_type: str,
    document_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get all payments allocated to a specific document"""
    try:
        allocations = payment_service.get_document_payments(document_type, document_id)
        return allocations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching document payments: {str(e)}")


@router.post("/payments/advance/customer", response_model=PaymentResponse, status_code=201)
async def create_advance_customer_payment(
    request: AdvancePaymentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create advance payment - UPI/ONLINE auto-set to DRAFT until gateway confirms"""
    try:
        result = payment_service.create_advance_payment(
            payment_number=request.payment_number,
            party_id=request.party_id,
            party_type=request.party_type.value,
            amount=request.amount,
            payment_mode=request.payment_mode.value,
            instrument_number=request.instrument_number,
            instrument_date=request.instrument_date,
            bank_name=request.bank_name,
            branch_name=request.branch_name,
            ifsc_code=request.ifsc_code,
            transaction_reference=request.transaction_reference,
            remarks=request.remarks
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating advance payment: {str(e)}")


@router.post("/payments/invoice", response_model=PaymentResponse, status_code=201)
async def create_invoice_payment(
    request: InvoicePaymentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create payment against invoice - auto DRAFT for UPI/online, POSTED for cash"""
    try:
        result = payment_service.create_invoice_payment_simple(
            payment_number=request.payment_number,
            invoice_id=request.invoice_id,
            invoice_type=request.invoice_type,
            amount=request.amount,
            payment_mode=request.payment_mode.value,
            instrument_number=request.instrument_number,
            instrument_date=request.instrument_date,
            bank_name=request.bank_name,
            branch_name=request.branch_name,
            ifsc_code=request.ifsc_code,
            transaction_reference=request.transaction_reference,
            remarks=request.remarks
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating invoice payment: {str(e)}")


@router.patch("/payments/{payment_id}/gateway-confirm", response_model=PaymentResponse)
async def confirm_gateway_payment(
    payment_id: int,
    gateway_data: GatewayPaymentUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update DRAFT payment with gateway response - POSTED on SUCCESS, stays DRAFT on FAILED"""
    try:
        result = payment_service.confirm_gateway_payment(
            payment_id=payment_id,
            transaction_reference=gateway_data.transaction_reference,
            gateway_transaction_id=gateway_data.gateway_transaction_id,
            gateway_status=gateway_data.gateway_status,
            gateway_fee_base=gateway_data.gateway_fee_base,
            gateway_response=gateway_data.gateway_response
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error confirming payment: {str(e)}")
