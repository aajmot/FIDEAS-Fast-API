from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from core.database.connection import db_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware
from core.shared.utils.session_manager import session_manager
from modules.account_module.models.entities import CostCenter
from api.schemas.account_schema.cost_center_schemas import (
    CostCenterCreate, CostCenterUpdate, CostCenterResponse, 
    CostCenterListResponse, CostCenterImportRow
)
from datetime import datetime, date
from fastapi import HTTPException

class CostCenterService:
    
    @ExceptionMiddleware.handle_exceptions("CostCenterService")
    def get_all(self, tenant_id: int, page: int = 1, per_page: int = 50, 
                search: Optional[str] = None, is_active: Optional[bool] = None) -> Dict[str, Any]:
        """Get all cost centers with pagination and filtering"""
        with db_manager.get_session() as session:
            query = session.query(CostCenter).filter(CostCenter.tenant_id == tenant_id)
            
            # Apply filters
            if search:
                query = query.filter(or_(
                    CostCenter.name.ilike(f"%{search}%"),
                    CostCenter.code.ilike(f"%{search}%")
                ))
            
            if is_active is not None:
                query = query.filter(CostCenter.is_active == is_active)
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            offset = (page - 1) * per_page
            cost_centers = query.offset(offset).limit(per_page).all()
            
            return {
                "items": [CostCenterListResponse.from_orm(cc) for cc in cost_centers],
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
    
    @ExceptionMiddleware.handle_exceptions("CostCenterService")
    def get_by_id(self, cost_center_id: int, tenant_id: int) -> Optional[CostCenterResponse]:
        """Get cost center by ID"""
        with db_manager.get_session() as session:
            cost_center = session.query(CostCenter).filter(
                and_(CostCenter.id == cost_center_id, CostCenter.tenant_id == tenant_id)
            ).first()
            
            if not cost_center:
                return None
            
            return CostCenterResponse.from_orm(cost_center)
    
    @ExceptionMiddleware.handle_exceptions("CostCenterService")
    def create(self, cost_center_data: CostCenterCreate, tenant_id: int, created_by: Optional[int] = None) -> CostCenterResponse:
        """Create new cost center"""
        with db_manager.get_session() as session:
            # Validate parent exists if provided
            if cost_center_data.parent_id:
                parent = session.query(CostCenter).filter(
                    and_(CostCenter.id == cost_center_data.parent_id, CostCenter.tenant_id == tenant_id)
                ).first()
                if not parent:
                    raise HTTPException(status_code=400, detail="Parent cost center not found")
            
            # Check code uniqueness
            existing = session.query(CostCenter).filter(
                and_(CostCenter.code == cost_center_data.code, CostCenter.tenant_id == tenant_id)
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="Cost center code already exists")
            
            # Create cost center
            cost_center = CostCenter(
                tenant_id=tenant_id,
                legal_entity_id=cost_center_data.legal_entity_id,
                code=cost_center_data.code,
                name=cost_center_data.name,
                description=cost_center_data.description,
                parent_id=cost_center_data.parent_id,
                category=cost_center_data.category.value,
                manager_id=cost_center_data.manager_id,
                department_id=cost_center_data.department_id,
                valid_from=cost_center_data.valid_from,
                valid_until=cost_center_data.valid_until,
                is_active=cost_center_data.is_active,
                lock_posting=cost_center_data.lock_posting,
                currency_code=cost_center_data.currency_code,
                created_by=created_by
            )
            
            session.add(cost_center)
            session.flush()
            session.refresh(cost_center)
            session.commit()
            
            return CostCenterResponse.from_orm(cost_center)
    
    @ExceptionMiddleware.handle_exceptions("CostCenterService")
    def update(self, cost_center_id: int, cost_center_data: CostCenterUpdate, 
               tenant_id: int) -> Optional[CostCenterResponse]:
        """Update cost center"""
        with db_manager.get_session() as session:
            cost_center = session.query(CostCenter).filter(
                and_(CostCenter.id == cost_center_id, CostCenter.tenant_id == tenant_id)
            ).first()
            
            if not cost_center:
                return None
            
            # Validate parent if being updated
            if cost_center_data.parent_id is not None and cost_center_data.parent_id != cost_center.parent_id:
                if cost_center_data.parent_id == cost_center_id:
                    raise HTTPException(status_code=400, detail="Cost center cannot be its own parent")
                
                if cost_center_data.parent_id:
                    parent = session.query(CostCenter).filter(
                        and_(CostCenter.id == cost_center_data.parent_id, CostCenter.tenant_id == tenant_id)
                    ).first()
                    if not parent:
                        raise HTTPException(status_code=400, detail="Parent cost center not found")
            
            # Check code uniqueness if being updated
            if cost_center_data.code and cost_center_data.code != cost_center.code:
                existing = session.query(CostCenter).filter(
                    and_(CostCenter.code == cost_center_data.code, CostCenter.tenant_id == tenant_id)
                ).first()
                if existing:
                    raise HTTPException(status_code=400, detail="Cost center code already exists")
            
            # Update fields
            update_data = cost_center_data.dict(exclude_unset=True)
            if 'category' in update_data:
                update_data['category'] = update_data['category'].value
            
            for field, value in update_data.items():
                setattr(cost_center, field, value)
            
            cost_center.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(cost_center)
            
            return CostCenterResponse.from_orm(cost_center)
    
    @ExceptionMiddleware.handle_exceptions("CostCenterService")
    def delete(self, cost_center_id: int, tenant_id: int) -> bool:
        """Delete cost center"""
        with db_manager.get_session() as session:
            cost_center = session.query(CostCenter).filter(
                and_(CostCenter.id == cost_center_id, CostCenter.tenant_id == tenant_id)
            ).first()
            
            if not cost_center:
                return False
            
            # Check if has children
            children = session.query(CostCenter).filter(CostCenter.parent_id == cost_center_id).first()
            if children:
                raise HTTPException(status_code=400, detail="Cannot delete cost center with child cost centers")
            
            session.delete(cost_center)
            session.commit()
            return True
    
    @ExceptionMiddleware.handle_exceptions("CostCenterService")
    def get_hierarchy(self, tenant_id: int) -> List[Dict[str, Any]]:
        """Get cost center hierarchy"""
        with db_manager.get_session() as session:
            cost_centers = session.query(CostCenter).filter(
                and_(CostCenter.tenant_id == tenant_id, CostCenter.is_active == True)
            ).all()
            
            # Build hierarchy
            cc_dict = {cc.id: {
                "id": cc.id,
                "code": cc.code,
                "name": cc.name,
                "parent_id": cc.parent_id,
                "category": cc.category,
                "children": []
            } for cc in cost_centers}
            
            # Build tree structure
            root_nodes = []
            for cc in cc_dict.values():
                if cc["parent_id"] is None:
                    root_nodes.append(cc)
                else:
                    parent = cc_dict.get(cc["parent_id"])
                    if parent:
                        parent["children"].append(cc)
            
            return root_nodes
    
    @ExceptionMiddleware.handle_exceptions("CostCenterService")
    def import_cost_centers(self, import_data: List[CostCenterImportRow], 
                           tenant_id: int, created_by: Optional[int] = None) -> Dict[str, Any]:
        """Import cost centers from CSV data"""
        with db_manager.get_session() as session:
            imported_count = 0
            errors = []
            
            # First pass: create cost centers without parent relationships
            code_to_id = {}
            for i, row in enumerate(import_data):
                try:
                    # Check if already exists
                    existing = session.query(CostCenter).filter(
                        and_(CostCenter.code == row.code, CostCenter.tenant_id == tenant_id)
                    ).first()
                    
                    if existing:
                        errors.append(f"Row {i+1}: Cost center code '{row.code}' already exists")
                        continue
                    
                    cost_center = CostCenter(
                        tenant_id=tenant_id,
                        code=row.code,
                        name=row.name,
                        description=row.description,
                        category=row.category if row.category in ['PRODUCTION', 'MARKETING', 'ADMIN', 'NA'] else 'NA',
                        is_active=row.is_active.lower() == 'true' if row.is_active else True,
                        lock_posting=row.lock_posting.lower() == 'true' if row.lock_posting else False,
                        currency_code=row.currency_code,
                        created_by=created_by
                    )
                    
                    session.add(cost_center)
                    session.flush()
                    code_to_id[row.code] = cost_center.id
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {i+1}: {str(e)}")
            
            # Second pass: update parent relationships
            for i, row in enumerate(import_data):
                if row.parent_code and row.code in code_to_id:
                    try:
                        parent_id = code_to_id.get(row.parent_code)
                        if parent_id:
                            cost_center = session.query(CostCenter).filter(CostCenter.id == code_to_id[row.code]).first()
                            if cost_center:
                                cost_center.parent_id = parent_id
                        else:
                            errors.append(f"Row {i+1}: Parent code '{row.parent_code}' not found")
                    except Exception as e:
                        errors.append(f"Row {i+1}: Error setting parent - {str(e)}")
            
            session.commit()
            
            return {
                "imported_count": imported_count,
                "total_rows": len(import_data),
                "errors": errors
            }