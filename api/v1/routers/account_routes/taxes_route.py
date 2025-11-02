from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Dict, Any
import io
import csv
import math
from api.schemas.common import PaginatedResponse, BaseResponse
from api.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.get("/taxes", response_model=PaginatedResponse)
async def get_taxes(current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import TaxMaster

    with db_manager.get_session() as session:
        taxes = session.query(TaxMaster).filter(
            TaxMaster.tenant_id == current_user['tenant_id']
        ).all()

        tax_data = [{
            "id": tax.id,
            "name": tax.name,
            "tax_type": tax.tax_type,
            "rate": float(tax.rate),
            "is_active": tax.is_active
        } for tax in taxes]

    return PaginatedResponse(
        success=True,
        message="Taxes retrieved successfully",
        data=tax_data,
        total=len(tax_data),
        page=1,
        per_page=len(tax_data),
        total_pages=1
    )


@router.post("/taxes", response_model=BaseResponse)
async def create_tax(tax_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import TaxMaster

    with db_manager.get_session() as session:
        try:
            tax = TaxMaster(
                name=tax_data['name'],
                tax_type=tax_data['tax_type'],
                rate=tax_data['rate'],
                is_active=tax_data.get('is_active', True),
                tenant_id=current_user['tenant_id']
            )
            session.add(tax)
            session.flush()
            tax_id = tax.id
            session.commit()

            return BaseResponse(
                success=True,
                message="Tax created successfully",
                data={"id": tax_id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))


@router.put("/taxes/{tax_id}", response_model=BaseResponse)
async def update_tax(tax_id: int, tax_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import TaxMaster

    with db_manager.get_session() as session:
        try:
            tax = session.query(TaxMaster).filter(
                TaxMaster.id == tax_id,
                TaxMaster.tenant_id == current_user['tenant_id']
            ).first()

            if not tax:
                raise HTTPException(status_code=404, detail="Tax not found")

            if 'name' in tax_data:
                tax.name = tax_data['name']
            if 'tax_type' in tax_data:
                tax.tax_type = tax_data['tax_type']
            if 'rate' in tax_data:
                tax.rate = tax_data['rate']
            if 'is_active' in tax_data:
                tax.is_active = tax_data['is_active']

            session.commit()

            return BaseResponse(
                success=True,
                message="Tax updated successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))


@router.delete("/taxes/{tax_id}", response_model=BaseResponse)
async def delete_tax(tax_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import TaxMaster

    with db_manager.get_session() as session:
        try:
            tax = session.query(TaxMaster).filter(
                TaxMaster.id == tax_id,
                TaxMaster.tenant_id == current_user['tenant_id']
            ).first()

            if not tax:
                raise HTTPException(status_code=404, detail="Tax not found")

            session.delete(tax)
            session.commit()

            return BaseResponse(
                success=True,
                message="Tax deleted successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))


@router.post("/taxes/import", response_model=BaseResponse)
async def import_taxes(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import TaxMaster

    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))

    imported_count = 0
    with db_manager.get_session() as session:
        try:
            for row in csv_data:
                tax = TaxMaster(
                    name=row['name'],
                    tax_type=row['tax_type'],
                    rate=float(row['rate']),
                    is_active=row.get('is_active', 'true').lower() == 'true',
                    tenant_id=current_user['tenant_id']
                )
                session.add(tax)
                imported_count += 1

            session.commit()
            return BaseResponse(
                success=True,
                message=f"Imported {imported_count} taxes successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))


@router.get("/taxes/export-template")
async def export_taxes_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['name', 'tax_type', 'rate', 'is_active'])
    writer.writerow(['CGST 9%', 'GST', '9', 'true'])
    writer.writerow(['SGST 9%', 'GST', '9', 'true'])
    writer.writerow(['IGST 18%', 'GST', '18', 'true'])

    output.seek(0)
    from fastapi.responses import StreamingResponse
    import io as _io
    return StreamingResponse(
        _io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=taxes_template.csv"}
    )
