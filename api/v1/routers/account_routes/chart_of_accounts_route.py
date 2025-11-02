from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from typing import Dict, Any
from api.schemas.common import BaseResponse
from api.middleware.auth_middleware import get_current_user
import io, csv

router = APIRouter()


@router.get("/chart-of-accounts/export-template")
async def export_chart_of_accounts_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "code", "account_type", "parent_id", "current_balance", "is_active"])
    writer.writerow(["Cash", "1001", "Asset", "", "0.00", "true"])
    writer.writerow(["Bank", "1002", "Asset", "", "0.00", "true"])
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=chart_of_accounts_template.csv"}
    )


@router.post("/chart-of-accounts/import", response_model=BaseResponse)
async def import_chart_of_accounts(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))
    
    from modules.account_module.services.account_service import AccountService
    svc = AccountService()
    imported_count = 0
    for row in csv_data:
        try:
            account_data = {
                "name": row.get("name"),
                "code": row.get("code"),
                "account_type": row.get("account_type"),
                "current_balance": float(row.get("current_balance") or 0),
                "is_active": row.get("is_active", "true").lower() == "true",
                "tenant_id": current_user['tenant_id']
            }
            if row.get("parent_id"):
                account_data["parent_id"] = int(row.get("parent_id"))
            svc.create(account_data)
            imported_count += 1
        except Exception:
            continue
    
    return BaseResponse(success=True, message=f"Imported {imported_count} accounts successfully")
