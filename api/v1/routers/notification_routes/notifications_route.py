from fastapi import APIRouter, Depends
from pydantic import BaseModel
from api.middleware.auth_middleware import get_current_user
from core.shared.services.notification_service import NotificationService

router = APIRouter()

class EmailRequest(BaseModel):
    to_email: str
    subject: str
    body: str

@router.post("/send-email")
def send_email(req: EmailRequest, current_user: dict = Depends(get_current_user)):
    success = NotificationService.send_email(req.to_email, req.subject, req.body, current_user['tenant_id'])
    return {"status": "sent" if success else "failed"}

@router.post("/invoice-email/{voucher_id}")
def send_invoice(voucher_id: int, current_user: dict = Depends(get_current_user)):
    success = NotificationService.send_invoice_email(voucher_id, current_user['tenant_id'])
    return {"status": "sent" if success else "failed"}

@router.post("/payment-reminder/{party_id}")
def send_reminder(party_id: int, current_user: dict = Depends(get_current_user)):
    success = NotificationService.send_payment_reminder(party_id, current_user['tenant_id'])
    return {"status": "sent" if success else "failed"}

@router.post("/low-stock-alert/{product_id}")
def send_stock_alert(product_id: int, current_user: dict = Depends(get_current_user)):
    success = NotificationService.send_low_stock_alert(product_id, current_user['tenant_id'])
    return {"status": "sent" if success else "failed"}
