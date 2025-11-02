from fastapi import APIRouter, Depends, UploadFile, File
from typing import List, Dict
from pydantic import BaseModel
from api.middleware.auth_middleware import get_current_user
from modules.account_module.services.reconciliation_service import ReconciliationService

router = APIRouter()

class ManualReconcile(BaseModel):
    statement_id: int
    voucher_id: int

@router.post("/import/{account_id}")
async def import_statement(account_id: int, file: UploadFile = File(...), 
                          current_user: dict = Depends(get_current_user)):
    content = await file.read()
    csv_content = content.decode('utf-8')
    imported = ReconciliationService.import_bank_statement(
        csv_content, account_id, current_user['tenant_id']
    )
    return {"imported_count": len(imported), "statements": imported}

@router.post("/auto-match/{account_id}")
def auto_match(account_id: int, current_user: dict = Depends(get_current_user)):
    matches = ReconciliationService.auto_match_transactions(account_id, current_user['tenant_id'])
    return {"matched_count": len(matches), "matches": matches}

@router.post("/manual-reconcile")
def manual_reconcile(req: ManualReconcile, current_user: dict = Depends(get_current_user)):
    ReconciliationService.manual_reconcile(req.statement_id, req.voucher_id, current_user['tenant_id'])
    return {"status": "reconciled"}

@router.get("/unreconciled/{account_id}")
def get_unreconciled(account_id: int, current_user: dict = Depends(get_current_user)):
    return ReconciliationService.get_unreconciled(account_id, current_user['tenant_id'])
