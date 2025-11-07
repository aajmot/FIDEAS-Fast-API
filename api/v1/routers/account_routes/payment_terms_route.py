from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse
from modules.account_module.models.payment_term_schemas import (
    PaymentTermRequest,
    PaymentTermResponse,
    PaymentTermListResponse
)
from modules.account_module.services.payment_term_service import PaymentTermService

router = APIRouter()
payment_term_service = PaymentTermService()


@router.get("/payment-terms", response_model=PaymentTermListResponse)
async def get_payment_terms(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all payment terms with pagination and optional filters
    """
    try:
        result = payment_term_service.get_all(
            page=page,
            page_size=page_size,
            search=search,
            is_active=is_active
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payment-terms/{payment_term_id}", response_model=PaymentTermResponse)
async def get_payment_term_by_id(
    payment_term_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific payment term by ID
    """
    try:
        result = payment_term_service.get_by_id(payment_term_id)
        if not result:
            raise HTTPException(status_code=404, detail="Payment term not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/payment-terms", response_model=PaymentTermResponse, status_code=201)
async def create_payment_term(
    payment_term: PaymentTermRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new payment term
    """
    try:
        result = payment_term_service.create(payment_term.dict())
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/payment-terms/{payment_term_id}", response_model=PaymentTermResponse)
async def update_payment_term(
    payment_term_id: int,
    payment_term: PaymentTermRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update an existing payment term
    """
    try:
        result = payment_term_service.update(payment_term_id, payment_term.dict())
        if not result:
            raise HTTPException(status_code=404, detail="Payment term not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/payment-terms/{payment_term_id}", status_code=204)
async def delete_payment_term(
    payment_term_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Soft delete a payment term
    """
    try:
        success = payment_term_service.delete(payment_term_id)
        if not success:
            raise HTTPException(status_code=404, detail="Payment term not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
