from typing import List, Optional, Dict, Any, Tuple
from modules.people_module.models.employee_entity import Employee
from core.shared.middleware.exception_handler import ExceptionMiddleware
from core.database.connection import db_manager
from core.shared.utils.logger import logger
from sqlalchemy import or_

class EmployeeService:
    def __init__(self):
        self.model_class = Employee
        self.module_name = "EmployeeService"
    
    @ExceptionMiddleware.handle_exceptions()
    def create(self, data: Dict[str, Any]) -> Employee:
        with db_manager.get_session() as session:
            employee = Employee(**data)
            session.add(employee)
            session.flush()
            session.refresh(employee)
            logger.info(f"Created Employee with ID: {employee.id}", self.module_name)
            return employee
    
    @ExceptionMiddleware.handle_exceptions()
    def get_by_id(self, employee_id: int) -> Optional[Employee]:
        with db_manager.get_session() as session:
            return session.query(Employee).filter(Employee.id == employee_id).first()
    
    @ExceptionMiddleware.handle_exceptions()
    def get_by_code(self, employee_code: str, tenant_id: int) -> Optional[Employee]:
        with db_manager.get_session() as session:
            return session.query(Employee).filter(
                Employee.employee_code == employee_code,
                Employee.tenant_id == tenant_id,
                Employee.is_deleted == False
            ).first()
    
    @ExceptionMiddleware.handle_exceptions()
    def get_active_employees(self, tenant_id: int) -> List[Employee]:
        with db_manager.get_session() as session:
            return session.query(Employee).filter(
                Employee.tenant_id == tenant_id,
                Employee.status == 'ACTIVE',
                Employee.is_deleted == False
            ).all()
    
    @ExceptionMiddleware.handle_exceptions()
    def get_by_type(self, tenant_id: int, employee_type: str) -> List[Employee]:
        with db_manager.get_session() as session:
            return session.query(Employee).filter(
                Employee.tenant_id == tenant_id,
                Employee.employee_type == employee_type,
                Employee.status == 'ACTIVE',
                Employee.is_deleted == False
            ).all()
    
    @ExceptionMiddleware.handle_exceptions()
    def get_paginated(self, filters: Dict[str, Any], offset: int, limit: int, search: Optional[str] = None) -> Tuple[List[Employee], int]:
        with db_manager.get_session() as session:
            query = session.query(Employee)
            
            for key, value in filters.items():
                if hasattr(Employee, key):
                    query = query.filter(getattr(Employee, key) == value)
            
            if search:
                query = query.filter(
                    or_(
                        Employee.employee_code.ilike(f"%{search}%"),
                        Employee.employee_name.ilike(f"%{search}%"),
                        Employee.email.ilike(f"%{search}%")
                    )
                )
            
            total = query.count()
            employees = query.offset(offset).limit(limit).all()
            return employees, total
    
    @ExceptionMiddleware.handle_exceptions()
    def update(self, employee_id: int, data: Dict[str, Any]) -> Optional[Employee]:
        with db_manager.get_session() as session:
            employee = session.query(Employee).filter(Employee.id == employee_id).first()
            if employee:
                for key, value in data.items():
                    if hasattr(employee, key):
                        setattr(employee, key, value)
                session.flush()
                session.refresh(employee)
                logger.info(f"Updated Employee with ID: {employee_id}", self.module_name)
                return employee
            return None
    
    @ExceptionMiddleware.handle_exceptions()
    def soft_delete(self, employee_id: int, username: str) -> bool:
        with db_manager.get_session() as session:
            employee = session.query(Employee).filter(Employee.id == employee_id).first()
            if employee:
                employee.is_deleted = True
                employee.updated_by = username
                session.flush()
                logger.info(f"Soft deleted Employee with ID: {employee_id}", self.module_name)
                return True
            return False
