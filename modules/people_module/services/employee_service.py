from typing import List, Optional, Dict, Any
from sqlalchemy import or_, and_
from modules.people_module.models.employee_entity import Employee
from core.shared.middleware.exception_handler import ExceptionMiddleware
from core.database.connection import db_manager
from core.shared.utils.logger import logger
from api.schemas.people_schema.employee_schemas import (
    EmployeeCreate, EmployeeUpdate, EmployeeResponse, 
    EmployeeListResponse, EmployeeImportRow
)
from modules.admin_module.services.user_service import UserService
from modules.admin_module.services.role_service import RoleService
from fastapi import HTTPException
from datetime import datetime

class EmployeeService:
    def __init__(self):
        self.model_class = Employee
        self.module_name = "EmployeeService"
        self.user_service = UserService()
        self.role_service = RoleService()
    
    @ExceptionMiddleware.handle_exceptions()
    def get_all(self, tenant_id: int, page: int = 1, per_page: int = 50, 
                search: Optional[str] = None, status: Optional[str] = None, 
                employee_type: Optional[str] = None) -> Dict[str, Any]:
        """Get all employees with pagination and filtering"""
        with db_manager.get_session() as session:
            query = session.query(Employee).filter(
                and_(Employee.tenant_id == tenant_id, Employee.is_deleted == False)
            )
            
            if search:
                query = query.filter(or_(
                    Employee.employee_name.ilike(f"%{search}%"),
                    Employee.employee_code.ilike(f"%{search}%"),
                    Employee.email.ilike(f"%{search}%")
                ))
            
            if status:
                query = query.filter(Employee.status == status)
            
            if employee_type:
                query = query.filter(Employee.employee_type == employee_type)
            
            total = query.count()
            offset = (page - 1) * per_page
            employees = query.offset(offset).limit(per_page).all()
            
            return {
                "items": [EmployeeListResponse.from_orm(emp) for emp in employees],
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
    
    @ExceptionMiddleware.handle_exceptions()
    def create(self, employee_data: EmployeeCreate, tenant_id: int, created_by: str) -> EmployeeResponse:
        """Create new employee with optional user account"""
        with db_manager.get_session() as session:
            try:
                # Check code uniqueness
                existing = session.query(Employee).filter(
                    and_(Employee.employee_code == employee_data.employee_code, 
                         Employee.tenant_id == tenant_id, 
                         Employee.is_deleted == False)
                ).first()
                if existing:
                    raise HTTPException(status_code=400, detail="Employee code already exists")
                
                # Create employee
                employee = Employee(
                    tenant_id=tenant_id,
                    employee_code=employee_data.employee_code,
                    employee_name=employee_data.employee_name,
                    employee_type=employee_data.employee_type.value,
                    phone=employee_data.phone,
                    email=employee_data.email,
                    qualification=employee_data.qualification,
                    specialization=employee_data.specialization,
                    license_number=employee_data.license_number,
                    license_expiry=employee_data.license_expiry,
                    employment_type=employee_data.employment_type.value,
                    status=employee_data.status.value,
                    remarks=employee_data.remarks,
                    branch_id=employee_data.branch_id,
                    department_id=employee_data.department_id,
                    created_by=created_by,
                    updated_by=created_by
                )
                
                session.add(employee)
                session.flush()
                
                # Create user account (now required)
                user_data_dict = employee_data.user_data.dict()
                user_data_dict['tenant_id'] = tenant_id
                user_data_dict['created_by'] = created_by
                
                # Create user in same session
                user_id = self.user_service.create(user_data_dict)
                
                # Assign roles if provided
                if employee_data.user_data.role_ids:
                    for role_id in employee_data.user_data.role_ids:
                        self.user_service.assign_role(user_id, role_id, user_id)
                
                session.refresh(employee)
                session.commit()
                logger.info(f"Created Employee with ID: {employee.id}", self.module_name)
                return EmployeeResponse.from_orm(employee)
                
            except Exception as e:
                session.rollback()
                raise e
    
    @ExceptionMiddleware.handle_exceptions()
    def get_by_id(self, employee_id: int, tenant_id: int) -> Optional[EmployeeResponse]:
        """Get employee by ID"""
        with db_manager.get_session() as session:
            employee = session.query(Employee).filter(
                and_(Employee.id == employee_id, 
                     Employee.tenant_id == tenant_id, 
                     Employee.is_deleted == False)
            ).first()
            return EmployeeResponse.from_orm(employee) if employee else None
    
    @ExceptionMiddleware.handle_exceptions()
    def update(self, employee_id: int, employee_data: EmployeeUpdate, 
               tenant_id: int, updated_by: str) -> Optional[EmployeeResponse]:
        """Update employee"""
        with db_manager.get_session() as session:
            employee = session.query(Employee).filter(
                and_(Employee.id == employee_id, 
                     Employee.tenant_id == tenant_id, 
                     Employee.is_deleted == False)
            ).first()
            
            if not employee:
                return None
            
            # Update fields
            update_data = employee_data.dict(exclude_unset=True)
            if 'employee_type' in update_data:
                update_data['employee_type'] = update_data['employee_type'].value
            if 'employment_type' in update_data:
                update_data['employment_type'] = update_data['employment_type'].value
            if 'status' in update_data:
                update_data['status'] = update_data['status'].value
            
            for field, value in update_data.items():
                setattr(employee, field, value)
            
            employee.updated_by = updated_by
            employee.updated_at = datetime.utcnow()
            session.flush()
            session.refresh(employee)
            logger.info(f"Updated Employee with ID: {employee_id}", self.module_name)
            return EmployeeResponse.from_orm(employee)
    
    @ExceptionMiddleware.handle_exceptions()
    def delete(self, employee_id: int, tenant_id: int, updated_by: str) -> bool:
        """Soft delete employee"""
        with db_manager.get_session() as session:
            employee = session.query(Employee).filter(
                and_(Employee.id == employee_id, 
                     Employee.tenant_id == tenant_id, 
                     Employee.is_deleted == False)
            ).first()
            
            if not employee:
                return False
            
            employee.is_deleted = True
            employee.updated_by = updated_by
            employee.updated_at = datetime.utcnow()
            session.flush()
            logger.info(f"Soft deleted Employee with ID: {employee_id}", self.module_name)
            return True
    
    @ExceptionMiddleware.handle_exceptions()
    def import_employees(self, import_data: List[EmployeeImportRow], 
                        tenant_id: int, created_by: str) -> Dict[str, Any]:
        """Import employees from CSV data"""
        with db_manager.get_session() as session:
            imported_count = 0
            errors = []
            
            for i, row in enumerate(import_data):
                try:
                    # Check if already exists
                    existing = session.query(Employee).filter(
                        and_(Employee.employee_code == row.employee_code, 
                             Employee.tenant_id == tenant_id, 
                             Employee.is_deleted == False)
                    ).first()
                    
                    if existing:
                        errors.append(f"Row {i+1}: Employee code '{row.employee_code}' already exists")
                        continue
                    
                    employee = Employee(
                        tenant_id=tenant_id,
                        employee_code=row.employee_code,
                        employee_name=row.employee_name,
                        employee_type=row.employee_type if row.employee_type in ['LAB_TECHNICIAN','DOCTOR','NURSE','ADMIN','OTHERS'] else 'OTHERS',
                        phone=row.phone,
                        email=row.email,
                        qualification=row.qualification,
                        specialization=row.specialization,
                        employment_type=row.employment_type if row.employment_type in ['INTERNAL','EXTERNAL','CONTRACT'] else 'INTERNAL',
                        status=row.status if row.status in ['ACTIVE','INACTIVE','SUSPENDED'] else 'ACTIVE',
                        created_by=created_by,
                        updated_by=created_by
                    )
                    
                    session.add(employee)
                    session.flush()
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {i+1}: {str(e)}")
            
            session.commit()
            
            return {
                "imported_count": imported_count,
                "total_rows": len(import_data),
                "errors": errors
            }