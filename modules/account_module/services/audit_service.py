"""
Audit Trail Service
"""
from sqlalchemy.orm import Session
from modules.account_module.models.audit_trail import AuditTrail
from core.shared.utils.session_manager import session_manager
from datetime import datetime

class AuditService:
    """Service for audit trail management"""
    
    @staticmethod
    def log_action(session: Session, entity_type: str, entity_id: int, action: str, 
                   old_value: dict = None, new_value: dict = None, remarks: str = None):
        """
        Log an audit trail entry
        
        Args:
            session: Database session
            entity_type: Type of entity (VOUCHER, LEDGER, ACCOUNT, PAYMENT)
            entity_id: ID of the entity
            action: Action performed (CREATE, UPDATE, DELETE, POST, UNPOST, REVERSE)
            old_value: Previous value (for updates)
            new_value: New value
            remarks: Additional remarks
        """
        audit_entry = AuditTrail(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            username=session_manager.get_current_username(),
            tenant_id=session_manager.get_current_tenant_id(),
            created_at=datetime.utcnow(),
            remarks=remarks
        )
        session.add(audit_entry)
    
    @staticmethod
    def get_audit_trail(session: Session, entity_type: str = None, entity_id: int = None, 
                       tenant_id: int = None, limit: int = 100):
        """
        Get audit trail entries
        
        Args:
            session: Database session
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            tenant_id: Filter by tenant
            limit: Maximum records to return
            
        Returns:
            List of audit trail entries
        """
        query = session.query(AuditTrail)
        
        if tenant_id:
            query = query.filter(AuditTrail.tenant_id == tenant_id)
        
        if entity_type:
            query = query.filter(AuditTrail.entity_type == entity_type)
        
        if entity_id:
            query = query.filter(AuditTrail.entity_id == entity_id)
        
        return query.order_by(AuditTrail.created_at.desc()).limit(limit).all()
