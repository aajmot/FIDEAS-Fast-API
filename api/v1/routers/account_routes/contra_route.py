from fastapi import APIRouter, HTTPException, Depends
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from modules.account_module.services.contra_service import ContraService
from modules.account_module.models.contra_schemas import ContraVoucherCreate

router = APIRouter()
contra_service = ContraService()


@router.post("/contra", response_model=BaseResponse)
async def create_contra(contra_data: ContraVoucherCreate, current_user: dict = Depends(get_current_user)):
    """Create contra voucher for cash/bank transfers"""
    try:
        result = contra_service.create_contra_voucher(
            contra_data.dict(), 
            current_user['tenant_id'], 
            current_user['username']
        )
        
        return BaseResponse(
            success=True,
            message=result["message"],
            data={"id": result["id"], "voucher_number": result["voucher_number"]}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/contra", response_model=PaginatedResponse)
async def get_contra_vouchers(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    """Get contra vouchers by voucher type"""
    try:
        result = contra_service.get_vouchers_by_type(
            voucher_type="Contra",
            page=pagination.page,
            per_page=pagination.per_page,
            tenant_id=current_user['tenant_id']
        )
        
        return PaginatedResponse(
            success=True,
            message="Contra vouchers retrieved successfully",
            data=result["vouchers"],
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"],
            total_pages=result["total_pages"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/contra/{voucher_id}", response_model=BaseResponse)
async def get_contra_voucher_by_id(voucher_id: int, current_user: dict = Depends(get_current_user)):
    """Get a specific contra voucher by ID"""
    try:
        result = contra_service.get_contra_voucher_by_id(voucher_id, current_user['tenant_id'])
        
        return BaseResponse(
            success=True,
            message="Contra voucher retrieved successfully",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
