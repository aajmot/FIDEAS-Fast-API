from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from datetime import datetime, date
from api.schemas.common import BaseResponse
from api.middleware.auth_middleware import get_current_user
from modules.account_module.services.payment_service import PaymentService
from modules.account_module.models.payment_schemas import (
    PaymentRequest,
    PaymentResponse,
    PaymentListResponse,
    ReconcilePaymentRequest
)

router = APIRouter()
payment_service = PaymentService()

# ==================== NEW PAYMENT ENDPOINTS ====================

@router.get("/payments", response_model=PaymentListResponse)
async def get_payments(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=500, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by payment number, reference, remarks"),
    payment_type: Optional[str] = Query(None, description="Filter by payment type"),
    party_type: Optional[str] = Query(None, description="Filter by party type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    date_from: Optional[date] = Query(None, description="Filter from date"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    is_reconciled: Optional[bool] = Query(None, description="Filter by reconciliation status"),
    current_user: dict = Depends(get_current_user)
):
    """Get all payments with pagination and filters"""
    result = payment_service.get_all_payments(
        page=page,
        page_size=page_size,
        search=search,
        payment_type=payment_type,
        party_type=party_type,
        status=status,
        date_from=date_from,
        date_to=date_to,
        is_reconciled=is_reconciled
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


@router.post("/payments", response_model=PaymentResponse)
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

@router.put("/payments/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: int,
    payment: PaymentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing payment"""
    try:
        result = payment_service.update_payment(payment_id, payment.dict())
        if not result:
            raise HTTPException(status_code=404, detail="Payment not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating payment: {str(e)}")


@router.delete("/payments/{payment_id}", response_model=BaseResponse)
async def delete_payment(
    payment_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Soft delete a payment"""
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
        result = payment_service.reconcile_payment(
            payment_id,
            reconcile_data.reconciled_at
        )
        if not result:
            raise HTTPException(status_code=404, detail="Payment not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reconciling payment: {str(e)}")
