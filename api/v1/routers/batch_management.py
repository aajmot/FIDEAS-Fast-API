from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from pydantic import BaseModel
from api.middleware.auth_middleware import get_current_user
from modules.inventory_module.services.batch_service import BatchService

router = APIRouter(prefix="/batch", tags=["Batch Management"])

class BatchCreate(BaseModel):
    product_id: int
    batch_no: str
    mfg_date: str
    exp_date: str
    quantity: float
    mrp: float

@router.post("/create")
def create_batch(batch: BatchCreate, current_user: dict = Depends(get_current_user)):
    batch_id = BatchService.create_batch(
        batch.product_id, batch.batch_no, batch.mfg_date, batch.exp_date,
        batch.quantity, batch.mrp, current_user['tenant_id']
    )
    return {"batch_id": batch_id}

@router.get("/near-expiry")
def get_near_expiry(days: int = 30, current_user: dict = Depends(get_current_user)):
    return BatchService.get_near_expiry_batches(days, current_user['tenant_id'])

@router.get("/product/{product_id}")
def get_product_batches(product_id: int, current_user: dict = Depends(get_current_user)):
    return BatchService.get_batch_stock(product_id, current_user['tenant_id'])
