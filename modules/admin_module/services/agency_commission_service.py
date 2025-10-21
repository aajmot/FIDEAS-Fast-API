from core.database.connection import db_manager
from modules.admin_module.models.agency_commission import AgencyCommission
from core.shared.utils.logger import logger
from datetime import datetime

class AgencyCommissionService:
    def __init__(self):
        self.logger_name = "AgencyCommissionService"
    
    def create(self, data):
        try:
            # Validate product_type
            product_type = data.get('product_type')
            if not product_type or product_type not in ['Products', 'Tests']:
                raise ValueError("product_type must be 'Products' or 'Tests'")
            
            # Validate commission_type
            commission_type = data.get('commission_type')
            if commission_type and commission_type not in [None, '', 'Inherit_default', 'Percentage', 'Fixed']:
                raise ValueError("commission_type must be null/empty, 'Inherit_default', 'Percentage', or 'Fixed'")
            
            with db_manager.get_session() as session:
                commission = AgencyCommission(**data)
                session.add(commission)
                session.flush()
                commission_id = commission.id
                logger.info(f"Agency commission created: {commission_id}", self.logger_name)
                session.expunge(commission)
                commission.id = commission_id
                return commission
        except Exception as e:
            logger.error(f"Error creating agency commission: {str(e)}", self.logger_name)
            raise
    
    def get_all(self, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(AgencyCommission).filter(AgencyCommission.is_deleted == False)
                if tenant_id:
                    query = query.filter(AgencyCommission.tenant_id == tenant_id)
                commissions = query.all()
                for commission in commissions:
                    session.expunge(commission)
                return commissions
        except Exception as e:
            logger.error(f"Error fetching agency commissions: {str(e)}", self.logger_name)
            return []
    
    def get_by_id(self, commission_id, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(AgencyCommission).filter(
                    AgencyCommission.id == commission_id,
                    AgencyCommission.is_deleted == False
                )
                if tenant_id:
                    query = query.filter(AgencyCommission.tenant_id == tenant_id)
                commission = query.first()
                if commission:
                    session.expunge(commission)
                return commission
        except Exception as e:
            logger.error(f"Error fetching agency commission: {str(e)}", self.logger_name)
            return None
    
    def update(self, commission_id, data):
        try:
            # Validate product_type
            product_type = data.get('product_type')
            if product_type and product_type not in ['Products', 'Tests']:
                raise ValueError("product_type must be 'Products' or 'Tests'")
            
            # Validate commission_type
            commission_type = data.get('commission_type')
            if commission_type and commission_type not in [None, '', 'Inherit_default', 'Percentage', 'Fixed']:
                raise ValueError("commission_type must be null/empty, 'Inherit_default', 'Percentage', or 'Fixed'")
            
            with db_manager.get_session() as session:
                commission = session.query(AgencyCommission).filter(
                    AgencyCommission.id == commission_id,
                    AgencyCommission.is_deleted == False
                ).first()
                if commission:
                    for key, value in data.items():
                        if key not in ['id', 'created_at', 'created_by']:
                            setattr(commission, key, value)
                    commission.updated_at = datetime.utcnow()
                    session.flush()
                    logger.info(f"Agency commission updated: {commission_id}", self.logger_name)
                    session.expunge(commission)
                    return commission
                return None
        except Exception as e:
            logger.error(f"Error updating agency commission: {str(e)}", self.logger_name)
            raise
    
    def delete(self, commission_id):
        try:
            with db_manager.get_session() as session:
                commission = session.query(AgencyCommission).filter(
                    AgencyCommission.id == commission_id
                ).first()
                if commission:
                    commission.is_deleted = True
                    commission.updated_at = datetime.utcnow()
                    logger.info(f"Agency commission deleted: {commission_id}", self.logger_name)
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting agency commission: {str(e)}", self.logger_name)
            raise
