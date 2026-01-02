from core.database.connection import db_manager
from modules.health_module.models.lab_technician_entity import LabTechnician
from core.shared.utils.logger import logger
from datetime import datetime

class LabTechnicianService:
    def __init__(self):
        self.logger_name = "LabTechnicianService"
    
    def create(self, technician_data, tenant_id, created_by='system'):
        try:
            with db_manager.get_session() as session:
                now = datetime.now()
                technician_code = f"LT-{tenant_id}{now.strftime('%d%m%Y%H%M%S%f')[:17]}"
                
                technician = LabTechnician(
                    tenant_id=tenant_id,
                    technician_code=technician_code,
                    created_by=created_by,
                    updated_by=created_by,
                    **technician_data
                )
                session.add(technician)
                session.flush()
                technician_id = technician.id
                logger.info(f"Lab technician created: {technician.technician_code}", self.logger_name)
                session.expunge(technician)
                technician.id = technician_id
                return technician
        except Exception as e:
            logger.error(f"Error creating lab technician: {str(e)}", self.logger_name)
            raise
    
    def get_by_id(self, technician_id, tenant_id):
        try:
            with db_manager.get_session() as session:
                technician = session.query(LabTechnician).filter(
                    LabTechnician.id == technician_id,
                    LabTechnician.tenant_id == tenant_id,
                    LabTechnician.is_deleted == False
                ).first()
                if technician:
                    session.expunge(technician)
                return technician
        except Exception as e:
            logger.error(f"Error fetching lab technician: {str(e)}", self.logger_name)
            raise
    
    def update(self, technician_id, technician_data, tenant_id, updated_by='system'):
        try:
            with db_manager.get_session() as session:
                technician = session.query(LabTechnician).filter(
                    LabTechnician.id == technician_id,
                    LabTechnician.tenant_id == tenant_id,
                    LabTechnician.is_deleted == False
                ).first()
                if technician:
                    for key, value in technician_data.items():
                        if value is not None:
                            setattr(technician, key, value)
                    technician.updated_by = updated_by
                    technician.updated_at = datetime.utcnow()
                    session.flush()
                    technician_id_val = technician.id
                    logger.info(f"Lab technician updated: {technician.technician_code}", self.logger_name)
                    session.expunge(technician)
                    technician.id = technician_id_val
                    return technician
                return None
        except Exception as e:
            logger.error(f"Error updating lab technician: {str(e)}", self.logger_name)
            raise
    
    def delete(self, technician_id, tenant_id, deleted_by='system'):
        try:
            with db_manager.get_session() as session:
                technician = session.query(LabTechnician).filter(
                    LabTechnician.id == technician_id,
                    LabTechnician.tenant_id == tenant_id,
                    LabTechnician.is_deleted == False
                ).first()
                if technician:
                    technician.is_deleted = True
                    technician.is_active = False
                    technician.updated_by = deleted_by
                    technician.updated_at = datetime.utcnow()
                    logger.info(f"Lab technician deleted: {technician.technician_code}", self.logger_name)
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting lab technician: {str(e)}", self.logger_name)
            raise
