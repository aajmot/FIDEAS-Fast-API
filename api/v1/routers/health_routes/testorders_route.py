from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from sqlalchemy import or_
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user
from modules.diagnostic_module.services.test_panel_service import TestPanelService
from modules.diagnostic_module.services.test_result_service import TestResultService

router = APIRouter()

# Test Order endpoints
@router.get("/testorders", response_model=PaginatedResponse)
async def get_test_orders(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.diagnostic_module.models.entities import TestOrder
    
    with db_manager.get_session() as session:
        query = session.query(TestOrder).filter(
            TestOrder.tenant_id == current_user["tenant_id"],
            TestOrder.is_deleted == False
        )
        
        if pagination.search:
            query = query.filter(or_(
                TestOrder.test_order_number.ilike(f"%{pagination.search}%"),
                TestOrder.patient_name.ilike(f"%{pagination.search}%"),
                TestOrder.doctor_name.ilike(f"%{pagination.search}%")
            ))
        
        total = query.count()
        orders = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        order_data = [{
            "id": order.id,
            "test_order_number": order.test_order_number,
            "patient_name": order.patient_name,
            "doctor_name": order.doctor_name,
            "agency_id": order.agency_id,
            "order_date": order.order_date.isoformat() if order.order_date else None,
            "status": order.status,
            "urgency": order.urgency,
            "final_amount": float(order.final_amount) if order.final_amount else None,
            "created_at": order.created_at.isoformat() if order.created_at else None
        } for order in orders]
    
    return PaginatedResponse(
        success=True,
        message="Test orders retrieved successfully",
        data=order_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/testorders", response_model=BaseResponse)
async def create_test_order(order_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from modules.diagnostic_module.services.test_order_service import TestOrderService
    from modules.account_module.services.transaction_posting_service import TransactionPostingService
    from core.database.connection import db_manager
    
    service = TestOrderService()
    order_data["tenant_id"] = current_user["tenant_id"]
    order_data["created_by"] = current_user["username"]
    order = service.create(order_data)
    
    # Post to accounting
    try:
        with db_manager.get_session() as session:
            posting_data = {
                'reference_type': 'DIAGNOSTIC_ORDER',
                'reference_id': order.id,
                'reference_number': order.test_order_number,
                'total_amount': float(order.final_amount) if order.final_amount else 0,
                'transaction_date': order.order_date,
                'created_by': current_user['username']
            }
            TransactionPostingService.post_transaction(
                session, 'DIAGNOSTIC_SALES', posting_data, current_user['tenant_id']
            )
            session.commit()
    except Exception as e:
        print(f"Accounting posting failed for diagnostic order: {e}")
    
    return BaseResponse(
        success=True,
        message="Test order created successfully",
        data={"id": order.id}
    )

@router.get("/testorders/{order_id}", response_model=BaseResponse)
async def get_test_order(order_id: int, current_user: dict = Depends(get_current_user)):
    from modules.diagnostic_module.services.test_order_service import TestOrderService
    service = TestOrderService()
    order = service.get_by_id(order_id, current_user["tenant_id"])
    
    if not order:
        raise HTTPException(status_code=404, detail="Test order not found")
    
    items = service.get_items(order_id, current_user["tenant_id"])
    
    return BaseResponse(
        success=True,
        message="Test order retrieved successfully",
        data={
            "id": order.id,
            "test_order_number": order.test_order_number,
            "appointment_id": order.appointment_id,
            "patient_name": order.patient_name,
            "patient_phone": order.patient_phone,
            "doctor_name": order.doctor_name,
            "doctor_phone": order.doctor_phone,
            "doctor_license_number": order.doctor_license_number,
            "order_date": order.order_date.isoformat() if order.order_date else None,
            "status": order.status,
            "urgency": order.urgency,
            "notes": order.notes,
            "agency_id": order.agency_id,
            "total_amount": float(order.total_amount) if order.total_amount else None,
            "disc_percentage": float(order.disc_percentage) if order.disc_percentage else None,
            "disc_amount": float(order.disc_amount) if order.disc_amount else None,
            "roundoff": float(order.roundoff) if order.roundoff else None,
            "final_amount": float(order.final_amount) if order.final_amount else None,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "created_by": order.created_by,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None,
            "updated_by": order.updated_by,
            "items": [{
                "id": item.id,
                "test_id": item.test_id,
                "test_name": item.test_name,
                "panel_id": item.panel_id,
                "panel_name": item.panel_name,
                "rate": float(item.rate) if item.rate else None,
                "gst": float(item.gst) if item.gst else None,
                "cess": float(item.cess) if item.cess else None,
                "disc_percentage": float(item.disc_percentage) if item.disc_percentage else None,
                "disc_amount": float(item.disc_amount) if item.disc_amount else None,
                "total_amount": float(item.total_amount) if item.total_amount else None
            } for item in items]
        }
    )

@router.put("/testorders/{order_id}", response_model=BaseResponse)
async def update_test_order(order_id: int, order_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    from modules.diagnostic_module.services.test_order_service import TestOrderService
    service = TestOrderService()
    order_data["updated_by"] = current_user["username"]
    
    order = service.update(order_id, order_data)
    
    if not order:
        raise HTTPException(status_code=404, detail="Test order not found")
    
    return BaseResponse(success=True, message="Test order updated successfully")

@router.delete("/testorders/{order_id}", response_model=BaseResponse)
async def delete_test_order(order_id: int, current_user: dict = Depends(get_current_user)):
    from modules.diagnostic_module.services.test_order_service import TestOrderService
    service = TestOrderService()
    success = service.delete(order_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Test order not found")
    
    return BaseResponse(success=True, message="Test order deleted successfully")

# Test Result endpoints
@router.get("/testresults", response_model=PaginatedResponse)
async def get_test_results(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.diagnostic_module.models.entities import TestResult, TestOrder
    
    with db_manager.get_session() as session:
        query = session.query(TestResult).filter(
            TestResult.tenant_id == current_user["tenant_id"],
            TestResult.is_deleted == False
        )
        
        if pagination.search:
            query = query.filter(or_(
                TestResult.result_number.ilike(f"%{pagination.search}%"),
                TestResult.performed_by.ilike(f"%{pagination.search}%"),
                TestResult.notes.ilike(f"%{pagination.search}%")
            ))
        
        total = query.count()
        results = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        result_data = []
        for result in results:
            order = session.query(TestOrder).filter(TestOrder.id == result.test_order_id).first()
            result_data.append({
                "id": result.id,
                "result_number": result.result_number,
                "test_order_id": result.test_order_id,
                "order_number": order.test_order_number if order else None,
                "patient_name": order.patient_name if order else None,
                "doctor_name": order.doctor_name if order else None,
                "result_date": result.result_date.isoformat() if result.result_date else None,
                "performed_by": result.performed_by,
                "result_type": result.result_type,
                "created_at": result.created_at.isoformat() if result.created_at else None
            })
    
        return PaginatedResponse(
            success=True,
            message="Test results retrieved successfully",
            data=result_data,
            total=total,
            page=pagination.page,
            per_page=pagination.per_page,
            total_pages=math.ceil(total / pagination.per_page)
        )

@router.post("/testresults", response_model=BaseResponse)
async def create_test_result(result_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    service = TestResultService()
    result_data["tenant_id"] = current_user["tenant_id"]
    result_data["created_by"] = current_user["username"]
    result = service.create(result_data)
    
    return BaseResponse(
        success=True,
        message="Test result created successfully",
        data={"id": result.id}
    )
