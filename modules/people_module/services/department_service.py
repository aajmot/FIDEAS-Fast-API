from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import or_, and_
from modules.people_module.models.department_entity import Department
from core.shared.middleware.exception_handler import ExceptionMiddleware
from core.database.connection import db_manager
from core.shared.utils.logger import logger
from api.schemas.people_schema.department_schemas import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse, 
    DepartmentListResponse, DepartmentImportRow
)
from fastapi import HTTPException
from datetime import datetime

class DepartmentService:
    def __init__(self):
        self.model_class = Department
        self.module_name = "DepartmentService"
    
    @ExceptionMiddleware.handle_exceptions()
    def get_all(self, tenant_id: int, page: int = 1, per_page: int = 50, 
                search: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
        """Get all departments with pagination and filtering"""
        with db_manager.get_session() as session:
            query = session.query(Department).filter(
                and_(Department.tenant_id == tenant_id, Department.is_deleted == False)
            )
            
            if search:
                query = query.filter(or_(
                    Department.department_name.ilike(f"%{search}%"),
                    Department.department_code.ilike(f"%{search}%")
                ))
            
            if status:
                query = query.filter(Department.status == status)
            
            total = query.count()
            offset = (page - 1) * per_page
            departments = query.offset(offset).limit(per_page).all()
            
            return {
                "items": [DepartmentListResponse.from_orm(dept) for dept in departments],
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
    
    @ExceptionMiddleware.handle_exceptions()
    def create(self, department_data: DepartmentCreate, tenant_id: int, created_by: str) -> DepartmentResponse:
        """Create new department"""
        with db_manager.get_session() as session:
            # Validate parent exists if provided
            if department_data.parent_department_id:
                parent = session.query(Department).filter(
                    and_(Department.id == department_data.parent_department_id, 
                         Department.tenant_id == tenant_id, 
                         Department.is_deleted == False)
                ).first()
                if not parent:
                    raise HTTPException(status_code=400, detail="Parent department not found")
            
            # Check code uniqueness
            existing = session.query(Department).filter(
                and_(Department.department_code == department_data.department_code, 
                     Department.tenant_id == tenant_id, 
                     Department.is_deleted == False)
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="Department code already exists")
            
            department = Department(
                tenant_id=tenant_id,
                department_code=department_data.department_code,
                department_name=department_data.department_name,
                parent_department_id=department_data.parent_department_id,
                description=department_data.description,
                branch_id=department_data.branch_id,
                default_cost_center_id=department_data.default_cost_center_id,
                org_unit_type=department_data.org_unit_type.value,
                status=department_data.status.value,
                created_by=created_by,
                updated_by=created_by
            )
            
            session.add(department)
            session.flush()
            session.refresh(department)
            logger.info(f"Created Department with ID: {department.id}", self.module_name)
            return DepartmentResponse.from_orm(department)
    
    @ExceptionMiddleware.handle_exceptions()
    def get_by_id(self, department_id: int, tenant_id: int) -> Optional[DepartmentResponse]:
        """Get department by ID"""
        with db_manager.get_session() as session:
            department = session.query(Department).filter(
                and_(Department.id == department_id, 
                     Department.tenant_id == tenant_id, 
                     Department.is_deleted == False)
            ).first()
            return DepartmentResponse.from_orm(department) if department else None
    
    @ExceptionMiddleware.handle_exceptions()
    def update(self, department_id: int, department_data: DepartmentUpdate, 
               tenant_id: int, updated_by: str) -> Optional[DepartmentResponse]:
        """Update department"""
        with db_manager.get_session() as session:
            department = session.query(Department).filter(
                and_(Department.id == department_id, 
                     Department.tenant_id == tenant_id, 
                     Department.is_deleted == False)
            ).first()
            
            if not department:
                return None
            
            # Validate parent if being updated
            if (department_data.parent_department_id is not None and 
                department_data.parent_department_id != department.parent_department_id):
                if department_data.parent_department_id == department_id:
                    raise HTTPException(status_code=400, detail="Department cannot be its own parent")
                
                if department_data.parent_department_id:
                    parent = session.query(Department).filter(
                        and_(Department.id == department_data.parent_department_id, 
                             Department.tenant_id == tenant_id, 
                             Department.is_deleted == False)
                    ).first()
                    if not parent:
                        raise HTTPException(status_code=400, detail="Parent department not found")
            
            # Update fields
            update_data = department_data.dict(exclude_unset=True)
            if 'org_unit_type' in update_data:
                update_data['org_unit_type'] = update_data['org_unit_type'].value
            if 'status' in update_data:
                update_data['status'] = update_data['status'].value
            
            for field, value in update_data.items():
                setattr(department, field, value)
            
            department.updated_by = updated_by
            department.updated_at = datetime.utcnow()
            session.flush()
            session.refresh(department)
            logger.info(f"Updated Department with ID: {department_id}", self.module_name)
            return DepartmentResponse.from_orm(department)
    
    @ExceptionMiddleware.handle_exceptions()
    def delete(self, department_id: int, tenant_id: int, updated_by: str) -> bool:
        """Soft delete department"""
        with db_manager.get_session() as session:
            department = session.query(Department).filter(
                and_(Department.id == department_id, 
                     Department.tenant_id == tenant_id, 
                     Department.is_deleted == False)
            ).first()
            
            if not department:
                return False
            
            # Check if has children
            children = session.query(Department).filter(
                and_(Department.parent_department_id == department_id, 
                     Department.is_deleted == False)
            ).first()
            if children:
                raise HTTPException(status_code=400, detail="Cannot delete department with child departments")
            
            department.is_deleted = True
            department.updated_by = updated_by
            department.updated_at = datetime.utcnow()
            session.flush()
            logger.info(f"Soft deleted Department with ID: {department_id}", self.module_name)
            return True
    
    @ExceptionMiddleware.handle_exceptions()
    def get_hierarchy(self, tenant_id: int) -> List[Dict[str, Any]]:
        """Get department hierarchy"""
        with db_manager.get_session() as session:
            departments = session.query(Department).filter(
                and_(Department.tenant_id == tenant_id, 
                     Department.status == 'ACTIVE', 
                     Department.is_deleted == False)
            ).all()
            
            # Build hierarchy
            dept_dict = {dept.id: {
                "id": dept.id,
                "department_code": dept.department_code,
                "department_name": dept.department_name,
                "parent_department_id": dept.parent_department_id,
                "org_unit_type": dept.org_unit_type,
                "children": []
            } for dept in departments}
            
            # Build tree structure
            root_nodes = []
            for dept in dept_dict.values():
                if dept["parent_department_id"] is None:
                    root_nodes.append(dept)
                else:
                    parent = dept_dict.get(dept["parent_department_id"])
                    if parent:
                        parent["children"].append(dept)
            
            return root_nodes
    
    @ExceptionMiddleware.handle_exceptions()
    def import_departments(self, import_data: List[DepartmentImportRow], 
                          tenant_id: int, created_by: str) -> Dict[str, Any]:
        """Import departments from CSV data"""
        with db_manager.get_session() as session:
            imported_count = 0
            errors = []
            
            # First pass: create departments without parent relationships
            code_to_id = {}
            for i, row in enumerate(import_data):
                try:
                    # Check if already exists
                    existing = session.query(Department).filter(
                        and_(Department.department_code == row.department_code, 
                             Department.tenant_id == tenant_id, 
                             Department.is_deleted == False)
                    ).first()
                    
                    if existing:
                        errors.append(f"Row {i+1}: Department code '{row.department_code}' already exists")
                        continue
                    
                    department = Department(
                        tenant_id=tenant_id,
                        department_code=row.department_code,
                        department_name=row.department_name,
                        description=row.description,
                        org_unit_type=row.org_unit_type if row.org_unit_type in ['DIVISION', 'DEPARTMENT', 'TEAM'] else 'DIVISION',
                        status=row.status if row.status in ['ACTIVE', 'INACTIVE'] else 'ACTIVE',
                        created_by=created_by,
                        updated_by=created_by
                    )
                    
                    session.add(department)
                    session.flush()
                    code_to_id[row.department_code] = department.id
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {i+1}: {str(e)}")
            
            # Second pass: update parent relationships
            for i, row in enumerate(import_data):
                if row.parent_code and row.department_code in code_to_id:
                    try:
                        parent_id = code_to_id.get(row.parent_code)
                        if parent_id:
                            department = session.query(Department).filter(
                                Department.id == code_to_id[row.department_code]
                            ).first()
                            if department:
                                department.parent_department_id = parent_id
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
