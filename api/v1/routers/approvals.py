from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from api.middleware.auth_middleware import get_current_user
from api.schemas.common import BaseResponse, PaginatedResponse, PaginationParams
from core.database.connection import db_manager
from sqlalchemy import text
import math

router = APIRouter()

@router.get("/workflows", response_model=PaginatedResponse)
async def get_workflows(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        query = "SELECT * FROM approval_workflows WHERE tenant_id = :tenant_id"
        params = {"tenant_id": current_user['tenant_id']}
        
        total = session.execute(text(query.replace("*", "COUNT(*)")), params).scalar()
        query += f" ORDER BY name LIMIT :limit OFFSET :offset"
        params.update({"limit": pagination.per_page, "offset": pagination.offset})
        
        result = session.execute(text(query), params)
        workflows = [dict(row._mapping) for row in result]
        
        # Get levels for each workflow
        for workflow in workflows:
            levels_result = session.execute(text("""
                SELECT al.*, r.name as approver_name
                FROM approval_levels al
                LEFT JOIN roles r ON al.approver_role_id = r.id
                WHERE al.workflow_id = :workflow_id
                ORDER BY al.level_number
            """), {"workflow_id": workflow['id']})
            workflow['levels'] = [{
                'level_number': row.level_number,
                'approver_type': 'role' if row.approver_role_id else 'user',
                'approver_role_id': row.approver_role_id,
                'approver_user_id': row.approver_user_id,
                'approver_name': row.approver_name
            } for row in levels_result]
    
    return PaginatedResponse(success=True, message="Workflows retrieved", data=workflows,
                           total=total, page=pagination.page, per_page=pagination.per_page,
                           total_pages=math.ceil(total / pagination.per_page))

@router.post("/workflows", response_model=BaseResponse)
async def create_workflow(data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        try:
            result = session.execute(text("""
                INSERT INTO approval_workflows (name, entity_type, min_amount, max_amount, tenant_id, created_by)
                VALUES (:name, :entity_type, :min_amount, :max_amount, :tenant_id, :created_by)
                RETURNING id
            """), {**data, "tenant_id": current_user['tenant_id'], "created_by": current_user['username']})
            workflow_id = result.scalar()
            
            # Add levels
            for level in data.get('levels', []):
                session.execute(text("""
                    INSERT INTO approval_levels (workflow_id, level_number, approver_role_id, 
                        approver_user_id, is_mandatory, tenant_id)
                    VALUES (:workflow_id, :level_number, :approver_role_id, :approver_user_id,
                        :is_mandatory, :tenant_id)
                """), {**level, "workflow_id": workflow_id, "tenant_id": current_user['tenant_id']})
            
            session.commit()
            return BaseResponse(success=True, message="Workflow created", data={"id": workflow_id})
        except Exception as e:
            session.rollback()
            raise HTTPException(400, str(e))

@router.get("/pending", response_model=PaginatedResponse)
async def get_pending_approvals(pagination: PaginationParams = Depends(), current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        # Get approvals where current user is approver
        query = """
            SELECT ar.*, aw.name as workflow_name
            FROM approval_requests ar
            JOIN approval_workflows aw ON ar.workflow_id = aw.id
            JOIN approval_levels al ON aw.id = al.workflow_id AND ar.current_level = al.level_number
            WHERE ar.tenant_id = :tenant_id AND ar.status = 'PENDING'
            AND (al.approver_user_id = :user_id OR al.approver_role_id IN (
                SELECT role_id FROM user_roles WHERE user_id = :user_id
            ))
        """
        params = {"tenant_id": current_user['tenant_id'], "user_id": current_user['user_id']}
        
        total = session.execute(text(query.replace("ar.*, aw.name as workflow_name", "COUNT(*)")), params).scalar()
        query += f" ORDER BY ar.requested_at DESC LIMIT :limit OFFSET :offset"
        params.update({"limit": pagination.per_page, "offset": pagination.offset})
        
        result = session.execute(text(query), params)
        data = [dict(row._mapping) for row in result]
    
    return PaginatedResponse(success=True, message="Pending approvals retrieved", data=data,
                           total=total, page=pagination.page, per_page=pagination.per_page,
                           total_pages=math.ceil(total / pagination.per_page))

@router.post("/{request_id}/approve", response_model=BaseResponse)
async def approve_request(request_id: int, data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        try:
            # Get request
            request = session.execute(text("""
                SELECT * FROM approval_requests WHERE id = :id AND tenant_id = :tenant_id
            """), {"id": request_id, "tenant_id": current_user['tenant_id']}).fetchone()
            
            if not request:
                raise HTTPException(404, "Request not found")
            
            # Add to history
            session.execute(text("""
                INSERT INTO approval_history (request_id, level_number, approver_id, action, comments, tenant_id)
                VALUES (:request_id, :level_number, :approver_id, 'APPROVED', :comments, :tenant_id)
            """), {
                "request_id": request_id,
                "level_number": request.current_level,
                "approver_id": current_user['user_id'],
                "comments": data.get('comments'),
                "tenant_id": current_user['tenant_id']
            })
            
            # Check if more levels
            next_level = session.execute(text("""
                SELECT * FROM approval_levels 
                WHERE workflow_id = :workflow_id AND level_number > :current_level
                ORDER BY level_number LIMIT 1
            """), {"workflow_id": request.workflow_id, "current_level": request.current_level}).fetchone()
            
            if next_level:
                # Move to next level
                session.execute(text("""
                    UPDATE approval_requests SET current_level = :level WHERE id = :id
                """), {"level": next_level.level_number, "id": request_id})
            else:
                # Complete approval
                session.execute(text("""
                    UPDATE approval_requests SET status = 'APPROVED', completed_at = NOW() WHERE id = :id
                """), {"id": request_id})
                
                # Update entity status
                if request.entity_type == 'PURCHASE_ORDER':
                    session.execute(text("UPDATE purchase_orders SET approval_status = 'APPROVED' WHERE id = :id"),
                                  {"id": request.entity_id})
                elif request.entity_type == 'VOUCHER':
                    session.execute(text("UPDATE vouchers SET approval_status = 'APPROVED' WHERE id = :id"),
                                  {"id": request.entity_id})
            
            session.commit()
            return BaseResponse(success=True, message="Request approved")
        except Exception as e:
            session.rollback()
            raise HTTPException(400, str(e))

@router.post("/{request_id}/reject", response_model=BaseResponse)
async def reject_request(request_id: int, data: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    with db_manager.get_session() as session:
        try:
            request = session.execute(text("""
                SELECT * FROM approval_requests WHERE id = :id AND tenant_id = :tenant_id
            """), {"id": request_id, "tenant_id": current_user['tenant_id']}).fetchone()
            
            if not request:
                raise HTTPException(404, "Request not found")
            
            session.execute(text("""
                INSERT INTO approval_history (request_id, level_number, approver_id, action, comments, tenant_id)
                VALUES (:request_id, :level_number, :approver_id, 'REJECTED', :comments, :tenant_id)
            """), {
                "request_id": request_id,
                "level_number": request.current_level,
                "approver_id": current_user['user_id'],
                "comments": data.get('comments'),
                "tenant_id": current_user['tenant_id']
            })
            
            session.execute(text("""
                UPDATE approval_requests SET status = 'REJECTED', completed_at = NOW() WHERE id = :id
            """), {"id": request_id})
            
            # Update entity status
            if request.entity_type == 'PURCHASE_ORDER':
                session.execute(text("UPDATE purchase_orders SET approval_status = 'REJECTED' WHERE id = :id"),
                              {"id": request.entity_id})
            elif request.entity_type == 'VOUCHER':
                session.execute(text("UPDATE vouchers SET approval_status = 'REJECTED' WHERE id = :id"),
                              {"id": request.entity_id})
            
            session.commit()
            return BaseResponse(success=True, message="Request rejected")
        except Exception as e:
            session.rollback()
            raise HTTPException(400, str(e))
