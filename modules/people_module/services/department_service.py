from typing import List, Optional, Dict, Any, Tuple
from modules.people_module.models.department_entity import Department
from core.shared.middleware.exception_handler import ExceptionMiddleware
from core.database.connection import db_manager
from core.shared.utils.logger import logger
from sqlalchemy import or_

class DepartmentService:
    def __init__(self):
        self.model_class = Department
        self.module_name = "DepartmentService"
    
    @ExceptionMiddleware.handle_exceptions()
    def create(self, data: Dict[str, Any]) -> Department:
        with db_manager.get_session() as session:
            department = Department(**data)
            session.add(department)
            session.flush()
            session.refresh(department)
            logger.info(f"Created Department with ID: {department.id}", self.module_name)
            return department
    
    @ExceptionMiddleware.handle_exceptions()
    def get_by_id(self, department_id: int) -> Optional[Department]:
        with db_manager.get_session() as session:
            return session.query(Department).filter(Department.id == department_id).first()
    
    @ExceptionMiddleware.handle_exceptions()
    def get_by_code(self, department_code: str, tenant_id: int) -> Optional[Department]:
        with db_manager.get_session() as session:
            return session.query(Department).filter(
                Department.department_code == department_code,
                Department.tenant_id == tenant_id,
                Department.is_deleted == False
            ).first()
    
    @ExceptionMiddleware.handle_exceptions()
    def get_active_departments(self, tenant_id: int) -> List[Department]:
        with db_manager.get_session() as session:
            return session.query(Department).filter(
                Department.tenant_id == tenant_id,
                Department.status == 'ACTIVE',
                Department.is_deleted == False
            ).all()
    
    @ExceptionMiddleware.handle_exceptions()
    def get_paginated(self, filters: Dict[str, Any], offset: int, limit: int, search: Optional[str] = None) -> Tuple[List[Department], int]:
        with db_manager.get_session() as session:
            query = session.query(Department)
            
            for key, value in filters.items():
                if hasattr(Department, key):
                    query = query.filter(getattr(Department, key) == value)
            
            if search:
                query = query.filter(
                    or_(
                        Department.department_code.ilike(f"%{search}%"),
                        Department.department_name.ilike(f"%{search}%")
                    )
                )
            
            total = query.count()
            departments = query.offset(offset).limit(limit).all()
            return departments, total
    
    @ExceptionMiddleware.handle_exceptions()
    def update(self, department_id: int, data: Dict[str, Any]) -> Optional[Department]:
        with db_manager.get_session() as session:
            department = session.query(Department).filter(Department.id == department_id).first()
            if department:
                for key, value in data.items():
                    if hasattr(department, key):
                        setattr(department, key, value)
                session.flush()
                session.refresh(department)
                logger.info(f"Updated Department with ID: {department_id}", self.module_name)
                return department
            return None
    
    @ExceptionMiddleware.handle_exceptions()
    def soft_delete(self, department_id: int, username: str) -> bool:
        with db_manager.get_session() as session:
            department = session.query(Department).filter(Department.id == department_id).first()
            if department:
                department.is_deleted = True
                department.updated_by = username
                session.flush()
                logger.info(f"Soft deleted Department with ID: {department_id}", self.module_name)
                return True
            return False
