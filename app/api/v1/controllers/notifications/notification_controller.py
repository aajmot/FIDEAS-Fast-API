from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.core.utils.api_response import BaseResponse

router = APIRouter()

class EmailRequest(BaseModel):
    to_email: str
    subject: str
    body: str

@router.post("/send-email", response_model=BaseResponse)
async def send_email(req: EmailRequest):
    # TODO: Implement email sending
    return BaseResponse(
        success=True,
        message="Email sent successfully",
        data={"status": "sent"}
    )

@router.post("/invoice-email/{voucher_id}", response_model=BaseResponse)
async def send_invoice(voucher_id: int):
    # TODO: Implement invoice email sending
    return BaseResponse(
        success=True,
        message="Invoice email sent successfully",
        data={"status": "sent"}
    )

@router.post("/payment-reminder/{party_id}", response_model=BaseResponse)
async def send_reminder(party_id: int):
    # TODO: Implement payment reminder sending
    return BaseResponse(
        success=True,
        message="Payment reminder sent successfully",
        data={"status": "sent"}
    )

@router.post("/low-stock-alert/{product_id}", response_model=BaseResponse)
async def send_stock_alert(product_id: int):
    # TODO: Implement low stock alert sending
    return BaseResponse(
        success=True,
        message="Stock alert sent successfully",
        data={"status": "sent"}
    )