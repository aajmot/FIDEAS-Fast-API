from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from typing import Dict, Any
from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user
import io, csv, math

router = APIRouter()


@router.get("/cost-centers", response_model=PaginatedResponse)
async def get_cost_centers(current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import CostCenter

    with db_manager.get_session() as session:
        cost_centers = session.query(CostCenter).filter(
            CostCenter.tenant_id == current_user['tenant_id']
        ).all()
        
        cc_data = [{
            "id": cc.id,
            "name": cc.name,
            "code": cc.code,
            "parent_id": cc.parent_id,
            "is_active": cc.is_active
        } for cc in cost_centers]
    
    return PaginatedResponse(
        success=True,
        message="Cost centers retrieved successfully",
        data=cc_data,
        total=len(cc_data),
        page=1,
        per_page=len(cc_data),
        total_pages=1
    )


@router.post("/cost-centers", response_model=BaseResponse)
async def create_cost_center(cc_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import CostCenter

    with db_manager.get_session() as session:
        try:
            cc = CostCenter(
                name=cc_data['name'],
                code=cc_data['code'],
                parent_id=cc_data.get('parent_id'),
                is_active=cc_data.get('is_active', True),
                tenant_id=current_user['tenant_id']
            )
            session.add(cc)
            session.flush()
            cc_id = cc.id
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Cost center created successfully",
                data={"id": cc_id}
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))


@router.put("/cost-centers/{cc_id}", response_model=BaseResponse)
async def update_cost_center(cc_id: int, cc_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import CostCenter

    with db_manager.get_session() as session:
        try:
            cc = session.query(CostCenter).filter(
                CostCenter.id == cc_id,
                CostCenter.tenant_id == current_user['tenant_id']
            ).first()
            
            if not cc:
                raise HTTPException(status_code=404, detail="Cost center not found")
            
            if 'name' in cc_data:
                cc.name = cc_data['name']
            if 'code' in cc_data:
                cc.code = cc_data['code']
            if 'parent_id' in cc_data:
                cc.parent_id = cc_data['parent_id']
            if 'is_active' in cc_data:
                cc.is_active = cc_data['is_active']
            
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Cost center updated successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))


@router.delete("/cost-centers/{cc_id}", response_model=BaseResponse)
async def delete_cost_center(cc_id: int, current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.account_module.models.entities import CostCenter

    with db_manager.get_session() as session:
        try:
            cc = session.query(CostCenter).filter(
                CostCenter.id == cc_id,
                CostCenter.tenant_id == current_user['tenant_id']
            ).first()
            
            if not cc:
                raise HTTPException(status_code=404, detail="Cost center not found")
            
            session.delete(cc)
            session.commit()
            
            return BaseResponse(
                success=True,
                message="Cost center deleted successfully"
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e))


@router.post("/cost-centers/import", response_model=BaseResponse)
async def import_cost_centers(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    content = await file.read()
    csv_data = csv.DictReader(io.StringIO(content.decode()))

    imported_count = 0
    # Use a service or simple creation loop
    from modules.account_module.services.account_service import AccountService
    svc = AccountService()
    for row in csv_data:
        try:
            svc.create({
                "name": row.get('name'),
                "code": row.get('code'),
                "account_type": row.get('account_type'),
                "tenant_id": current_user['tenant_id']
            })
            imported_count += 1
        except Exception:
            continue

    return BaseResponse(success=True, message=f"Imported {imported_count} cost centers")


@router.get("/cost-centers/export-template")
async def export_cost_centers_template(current_user: dict = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['name', 'code', 'parent_id', 'is_active'])
    writer.writerow(['Main', 'CC-001', '', 'true'])
    output.seek(0)
    return output.getvalue()
