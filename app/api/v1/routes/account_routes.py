from fastapi import APIRouter
from app.api.v1.controllers.account.account_controller import router as account_router
from app.api.v1.controllers.account.voucher_controller import router as voucher_router
from app.api.v1.controllers.account.journal_controller import router as journal_router
from app.api.v1.controllers.account.gst_controller import router as gst_router

router = APIRouter()

# Include all account controllers
router.include_router(account_router, tags=["Account - Accounts"])
router.include_router(voucher_router, tags=["Account - Vouchers"])
router.include_router(journal_router, tags=["Account - Journals"])
router.include_router(gst_router, tags=["Account - GST"])