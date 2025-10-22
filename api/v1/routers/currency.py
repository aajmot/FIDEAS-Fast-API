from fastapi import APIRouter, Depends
from typing import List, Dict
from pydantic import BaseModel
from api.middleware.auth_middleware import get_current_user
from modules.account_module.services.currency_service import CurrencyService

router = APIRouter(prefix="/currency", tags=["Multi-Currency"])

class ExchangeRateUpdate(BaseModel):
    currency_id: int
    rate: float

class ConvertRequest(BaseModel):
    amount: float
    from_currency_id: int
    to_currency_id: int

@router.get("/list")
def get_currencies(current_user: dict = Depends(get_current_user)):
    return CurrencyService.get_currencies(current_user['tenant_id'])

@router.post("/convert")
def convert_amount(req: ConvertRequest, current_user: dict = Depends(get_current_user)):
    converted = CurrencyService.convert_amount(
        req.amount, req.from_currency_id, req.to_currency_id, current_user['tenant_id']
    )
    return {"converted_amount": converted}

@router.put("/exchange-rate")
def update_rate(update: ExchangeRateUpdate, current_user: dict = Depends(get_current_user)):
    CurrencyService.update_exchange_rate(update.currency_id, update.rate, current_user['tenant_id'])
    return {"status": "updated"}

@router.get("/forex-gain-loss/{voucher_id}")
def get_forex_gain_loss(voucher_id: int, current_user: dict = Depends(get_current_user)):
    gain_loss = CurrencyService.calculate_forex_gain_loss(voucher_id, current_user['tenant_id'])
    return {"forex_gain_loss": gain_loss}
