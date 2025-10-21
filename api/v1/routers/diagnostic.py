from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from sqlalchemy import or_
import math

from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from api.middleware.auth_middleware import get_current_user
from modules.diagnostic_module.services.test_panel_service import TestPanelService
from modules.diagnostic_module.services.test_result_service import TestResultService

router = APIRouter()

@router.get("/testpanels", response_model=PaginatedResponse)
async def get_test_panels(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    from core.database.connection import db_manager
    from modules.diagnostic_module.models.entities import TestPanel
    from modules.care_module.models.entities import TestCategory
    
    with db_manager.get_session() as session:
        query = session.query(TestPanel).filter(
            TestPanel.tenant_id == current_user["tenant_id"],
            TestPanel.is_deleted == False
        )
        
        if pagination.search:
            query = query.filter(or_(
                TestPanel.name.ilike(f"%{pagination.search}%"),
                TestPanel.description.ilike(f"%{pagination.search}%")
            ))
        
        total = query.count()
        panels = query.offset(pagination.offset).limit(pagination.per_page).all()
        
        panel_data = []
        for panel in panels:
            category = session.query(TestCategory).filter(TestCategory.id == panel.category_id).first() if panel.category_id else None
            panel_data.append({
                "id": panel.id,
                "name": panel.name,
                "description": panel.description,
                "category_id": panel.category_id,
                "category_name": category.name if category else None,
                "cost": float(panel.cost) if panel.cost else None,
                "gst": float(panel.gst) if panel.gst else None,
                "cess": float(panel.cess) if panel.cess else None,
                "expired_on": panel.expired_on.isoformat() if panel.expired_on else None,
                "is_active": panel.is_active,
                "created_at": panel.created_at.isoformat() if panel.created_at else None,
                "created_by": panel.created_by,
                "updated_at": panel.updated_at.isoformat() if panel.updated_at else None,
                "updated_by": panel.updated_by
            })
    
    return PaginatedResponse(
        success=True,
        message="Test panels retrieved successfully",
        data=panel_data,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=math.ceil(total / pagination.per_page)
    )

@router.post("/testpanels", response_model=BaseResponse)
async def create_test_panel(panel_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    service = TestPanelService()
    panel_data["tenant_id"] = current_user["tenant_id"]
    panel_data["created_by"] = current_user["username"]
    panel = service.create(panel_data)
    
    return BaseResponse(
        success=True,
        message="Test panel created successfully",
        data={"id": panel.id}
    )

@router.get("/testpanels/{panel_id}", response_model=BaseResponse)
async def get_test_panel(panel_id: int, current_user: dict = Depends(get_current_user)):
    service = TestPanelService()
    panel = service.get_by_id(panel_id, current_user["tenant_id"])
    
    if not panel:
        raise HTTPException(status_code=404, detail="Test panel not found")
    
    items = service.get_items(panel_id, current_user["tenant_id"])
    
    return BaseResponse(
        success=True,
        message="Test panel retrieved successfully",
        data={
            "id": panel.id,
            "name": panel.name,
            "description": panel.description,
            "category_id": panel.category_id,
            "cost": float(panel.cost) if panel.cost else None,
            "gst": float(panel.gst) if panel.gst else None,
            "cess": float(panel.cess) if panel.cess else None,
            "expired_on": panel.expired_on.isoformat() if panel.expired_on else None,
            "is_active": panel.is_active,
            "created_at": panel.created_at.isoformat() if panel.created_at else None,
            "created_by": panel.created_by,
            "updated_at": panel.updated_at.isoformat() if panel.updated_at else None,
            "updated_by": panel.updated_by,
            "items": [{
                "id": item.id,
                "test_id": item.test_id,
                "test_name": item.test_name
            } for item in items]
        }
    )

@router.put("/testpanels/{panel_id}", response_model=BaseResponse)
async def update_test_panel(panel_id: int, panel_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    service = TestPanelService()
    panel_data["updated_by"] = current_user["username"]
    
    for field in ['cost', 'gst', 'cess']:
        if field in panel_data and panel_data[field] == '':
            panel_data[field] = None
    
    if 'category_id' in panel_data and panel_data['category_id'] == '':
        panel_data['category_id'] = None
    
    panel = service.update(panel_id, panel_data)
    
    if not panel:
        raise HTTPException(status_code=404, detail="Test panel not found")
    
    return BaseResponse(success=True, message="Test panel updated successfully")

@router.delete("/testpanels/{panel_id}", response_model=BaseResponse)
async def delete_test_panel(panel_id: int, current_user: dict = Depends(get_current_user)):
    service = TestPanelService()
    success = service.delete(panel_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Test panel not found")
    
    return BaseResponse(success=True, message="Test panel deleted successfully")

@router.get("/testpanels/{panel_id}/items", response_model=BaseResponse)
async def get_test_panel_items(panel_id: int, current_user: dict = Depends(get_current_user)):
    service = TestPanelService()
    items = service.get_items(panel_id, current_user["tenant_id"])
    
    return BaseResponse(
        success=True,
        message="Test panel items retrieved successfully",
        data=[{
            "id": item.id,
            "test_id": item.test_id,
            "test_name": item.test_name,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "created_by": item.created_by,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            "updated_by": item.updated_by
        } for item in items]
    )

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

@router.get("/testresults/{result_id}", response_model=BaseResponse)
async def get_test_result(result_id: int, current_user: dict = Depends(get_current_user)):
    service = TestResultService()
    result = service.get_by_id(result_id, current_user["tenant_id"])
    
    if not result:
        raise HTTPException(status_code=404, detail="Test result not found")
    
    details = service.get_details(result_id, current_user["tenant_id"])
    files = service.get_files(result_id, current_user["tenant_id"])
    
    return BaseResponse(
        success=True,
        message="Test result retrieved successfully",
        data={
            "id": result.id,
            "result_number": result.result_number,
            "test_order_id": result.test_order_id,
            "result_date": result.result_date.isoformat() if result.result_date else None,
            "overall_report": result.overall_report,
            "performed_by": result.performed_by,
            "result_type": result.result_type,
            "notes": result.notes,
            "doctor_id": result.doctor_id,
            "license_number": result.license_number,
            "created_at": result.created_at.isoformat() if result.created_at else None,
            "created_by": result.created_by,
            "updated_at": result.updated_at.isoformat() if result.updated_at else None,
            "updated_by": result.updated_by,
            "details": [{
                "id": detail.id,
                "parameter_id": detail.parameter_id,
                "parameter_name": detail.parameter_name,
                "unit": detail.unit,
                "parameter_value": detail.parameter_value,
                "reference_value": detail.reference_value,
                "verdict": detail.verdict,
                "notes": detail.notes
            } for detail in details],
            "files": [{
                "id": file.id,
                "file_name": file.file_name,
                "file_path": file.file_path,
                "file_format": file.file_format,
                "file_size": file.file_size,
                "acquisition_date": file.acquisition_date.isoformat() if file.acquisition_date else None,
                "description": file.description,
                "storage_system": file.storage_system
            } for file in files]
        }
    )

@router.put("/testresults/{result_id}", response_model=BaseResponse)
async def update_test_result(result_id: int, result_data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    service = TestResultService()
    result_data["updated_by"] = current_user["username"]
    
    result = service.update(result_id, result_data)
    
    if not result:
        raise HTTPException(status_code=404, detail="Test result not found")
    
    return BaseResponse(success=True, message="Test result updated successfully")

@router.delete("/testresults/{result_id}", response_model=BaseResponse)
async def delete_test_result(result_id: int, current_user: dict = Depends(get_current_user)):
    service = TestResultService()
    success = service.delete(result_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Test result not found")
    
    return BaseResponse(success=True, message="Test result deleted successfully")

@router.get("/testresults/order/{order_id}", response_model=BaseResponse)
async def get_test_results_by_order(order_id: int, current_user: dict = Depends(get_current_user)):
    service = TestResultService()
    results = service.get_by_order_id(order_id, current_user["tenant_id"])
    
    return BaseResponse(
        success=True,
        message="Test results retrieved successfully",
        data=[{
            "id": result.id,
            "result_number": result.result_number,
            "test_order_id": result.test_order_id,
            "result_date": result.result_date.isoformat() if result.result_date else None,
            "overall_report": result.overall_report,
            "performed_by": result.performed_by,
            "result_type": result.result_type,
            "notes": result.notes,
            "created_at": result.created_at.isoformat() if result.created_at else None
        } for result in results]
    )
