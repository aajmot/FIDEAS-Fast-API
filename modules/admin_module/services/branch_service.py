# modules/admin_module/services/branch_service.py
from typing import List, Optional, Dict, Any, Tuple
from modules.admin_module.services.base_service import BaseService
from modules.admin_module.models.branch import Branch
from core.shared.middleware.exception_handler import ExceptionMiddleware
from core.database.connection import db_manager
from core.shared.utils.logger import logger
from sqlalchemy import or_

class BranchService(BaseService):
    def __init__(self):
        super().__init__(Branch)
    
    @ExceptionMiddleware.handle_exceptions()
    def get_by_code(self, branch_code: str, tenant_id: int) -> Optional[Branch]:
        with db_manager.get_session() as session:
            return session.query(Branch).filter(
                Branch.branch_code == branch_code,
                Branch.tenant_id == tenant_id,
                Branch.is_deleted == False
            ).first()
    
    @ExceptionMiddleware.handle_exceptions()
    def get_active_branches(self, tenant_id: int) -> List[Branch]:
        with db_manager.get_session() as session:
            return session.query(Branch).filter(
                Branch.tenant_id == tenant_id,
                Branch.status == 'ACTIVE',
                Branch.is_deleted == False
            ).all()
    
    @ExceptionMiddleware.handle_exceptions()
    def get_paginated(self, filters: Dict[str, Any], offset: int, limit: int, search: Optional[str] = None) -> Tuple[List[Branch], int]:
        with db_manager.get_session() as session:
            query = session.query(Branch)
            
            for key, value in filters.items():
                if hasattr(Branch, key):
                    query = query.filter(getattr(Branch, key) == value)
            
            if search:
                query = query.filter(
                    or_(
                        Branch.branch_code.ilike(f"%{search}%"),
                        Branch.branch_name.ilike(f"%{search}%"),
                        Branch.city.ilike(f"%{search}%")
                    )
                )
            
            total = query.count()
            branches = query.offset(offset).limit(limit).all()
            return branches, total
    
    @ExceptionMiddleware.handle_exceptions()
    def soft_delete(self, entity_id: int, username: str) -> bool:
        with db_manager.get_session() as session:
            branch = session.query(Branch).filter(Branch.id == entity_id).first()
            if branch:
                branch.is_deleted = True
                branch.updated_by = username
                session.flush()
                logger.info(f"Soft deleted Branch with ID: {entity_id}", self.module_name)
                return True
            return False
