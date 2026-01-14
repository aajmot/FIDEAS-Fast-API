from typing import List, Optional, Dict, Any
from sqlalchemy import and_
from modules.people_module.models.employee_entity import EmployeeCostAllocation, Employee
from core.shared.middleware.exception_handler import ExceptionMiddleware
from core.database.connection import db_manager
from core.shared.utils.logger import logger
from api.schemas.people_schema.employee_schemas import (
    CostAllocationCreate, CostAllocationUpdate, CostAllocationResponse
)
from fastapi import HTTPException
from datetime import datetime

class EmployeeCostAllocationService:
    def __init__(self):
        self.model_class = EmployeeCostAllocation
        self.module_name = "EmployeeCostAllocationService"
    
    @ExceptionMiddleware.handle_exceptions()
    def get_by_employee(self, employee_id: int, tenant_id: int) -> List[CostAllocationResponse]:
        """Get all cost allocations for an employee"""
        with db_manager.get_session() as session:
            allocations = session.query(EmployeeCostAllocation).filter(
                and_(EmployeeCostAllocation.employee_id == employee_id,
                     EmployeeCostAllocation.tenant_id == tenant_id)
            ).all()
            
            return [CostAllocationResponse.from_orm(alloc) for alloc in allocations]
    
    @ExceptionMiddleware.handle_exceptions()
    def create(self, allocation_data: CostAllocationCreate, tenant_id: int, created_by: str) -> CostAllocationResponse:
        """Create new cost allocation"""
        with db_manager.get_session() as session:
            # Validate employee exists
            employee = session.query(Employee).filter(
                and_(Employee.id == allocation_data.employee_id,
                     Employee.tenant_id == tenant_id,
                     Employee.is_deleted == False)
            ).first()
            if not employee:
                raise HTTPException(status_code=400, detail="Employee not found")
            
            # Check total allocation doesn't exceed 100%
            existing_total = session.query(EmployeeCostAllocation).filter(
                and_(EmployeeCostAllocation.employee_id == allocation_data.employee_id,
                     EmployeeCostAllocation.status == 'ACTIVE')
            ).with_entities(EmployeeCostAllocation.percentage).all()
            
            current_total = sum([alloc.percentage for alloc in existing_total]) if existing_total else 0
            if current_total + allocation_data.percentage > 100:
                raise HTTPException(status_code=400, detail="Total allocation cannot exceed 100%")
            
            allocation = EmployeeCostAllocation(
                tenant_id=tenant_id,
                branch_id=allocation_data.branch_id,
                employee_id=allocation_data.employee_id,
                cost_center_id=allocation_data.cost_center_id,
                percentage=allocation_data.percentage,
                effective_start_date=allocation_data.effective_start_date,
                effective_end_date=allocation_data.effective_end_date,
                status=allocation_data.status.value,
                created_by=created_by,
                updated_by=created_by
            )
            
            session.add(allocation)
            session.flush()
            session.refresh(allocation)
            logger.info(f"Created Cost Allocation with ID: {allocation.id}", self.module_name)
            return CostAllocationResponse.from_orm(allocation)
    
    @ExceptionMiddleware.handle_exceptions()
    def get_by_id(self, allocation_id: int, tenant_id: int) -> Optional[CostAllocationResponse]:
        """Get cost allocation by ID"""
        with db_manager.get_session() as session:
            allocation = session.query(EmployeeCostAllocation).filter(
                and_(EmployeeCostAllocation.id == allocation_id,
                     EmployeeCostAllocation.tenant_id == tenant_id)
            ).first()
            return CostAllocationResponse.from_orm(allocation) if allocation else None
    
    @ExceptionMiddleware.handle_exceptions()
    def update(self, allocation_id: int, allocation_data: CostAllocationUpdate, 
               tenant_id: int, updated_by: str) -> Optional[CostAllocationResponse]:
        """Update cost allocation"""
        with db_manager.get_session() as session:
            allocation = session.query(EmployeeCostAllocation).filter(
                and_(EmployeeCostAllocation.id == allocation_id,
                     EmployeeCostAllocation.tenant_id == tenant_id)
            ).first()
            
            if not allocation:
                return None
            
            # Check total allocation if percentage is being updated
            if allocation_data.percentage is not None:
                existing_total = session.query(EmployeeCostAllocation).filter(
                    and_(EmployeeCostAllocation.employee_id == allocation.employee_id,
                         EmployeeCostAllocation.status == 'ACTIVE',
                         EmployeeCostAllocation.id != allocation_id)
                ).with_entities(EmployeeCostAllocation.percentage).all()
                
                current_total = sum([alloc.percentage for alloc in existing_total]) if existing_total else 0
                if current_total + allocation_data.percentage > 100:
                    raise HTTPException(status_code=400, detail="Total allocation cannot exceed 100%")
            
            # Update fields
            update_data = allocation_data.dict(exclude_unset=True)
            if 'status' in update_data:
                update_data['status'] = update_data['status'].value
            
            for field, value in update_data.items():
                setattr(allocation, field, value)
            
            allocation.updated_by = updated_by
            allocation.updated_at = datetime.utcnow()
            session.flush()
            session.refresh(allocation)
            logger.info(f"Updated Cost Allocation with ID: {allocation_id}", self.module_name)
            return CostAllocationResponse.from_orm(allocation)
    
    @ExceptionMiddleware.handle_exceptions()
    def delete(self, allocation_id: int, tenant_id: int) -> bool:
        """Delete cost allocation"""
        with db_manager.get_session() as session:
            allocation = session.query(EmployeeCostAllocation).filter(
                and_(EmployeeCostAllocation.id == allocation_id,
                     EmployeeCostAllocation.tenant_id == tenant_id)
            ).first()
            
            if not allocation:
                return False
            
            session.delete(allocation)
            session.flush()
            logger.info(f"Deleted Cost Allocation with ID: {allocation_id}", self.module_name)
            return True