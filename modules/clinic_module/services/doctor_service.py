from core.database.connection import db_manager
from modules.clinic_module.models.entities import Doctor
from core.shared.utils.logger import logger
from datetime import datetime

class DoctorService:
    def __init__(self):
        self.logger_name = "DoctorService"
    
    def create(self, doctor_data):
        try:
            with db_manager.get_session() as session:
                # Generate employee ID in D-[tenantid]ddmmyyyyhhmmssfff format
                tenant_id = doctor_data.get('tenant_id', 1)
                now = datetime.now()
                employee_id = f"D-{tenant_id}{now.strftime('%d%m%Y%H%M%S%f')[:17]}"
                
                # Convert empty strings to None for time fields
                clean_data = {}
                for key, value in doctor_data.items():
                    if key in ['schedule_start', 'schedule_end'] and value == '':
                        clean_data[key] = None
                    else:
                        clean_data[key] = value
                
                doctor = Doctor(
                    employee_id=employee_id,
                    **clean_data
                )
                session.add(doctor)
                session.flush()
                doctor_id = doctor.id  # Access id while session is active
                logger.info(f"Doctor created: {doctor.employee_id}", self.logger_name)
                session.expunge(doctor)  # Detach from session
                doctor.id = doctor_id  # Set id on detached object
                return doctor
        except Exception as e:
            logger.error(f"Error creating doctor: {str(e)}", self.logger_name)
            raise
    
    def get_all(self, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(Doctor)
                if tenant_id:
                    query = query.filter(Doctor.tenant_id == tenant_id)
                doctors = query.filter(Doctor.is_active == True).all()
                # Detach from session
                for doctor in doctors:
                    session.expunge(doctor)
                return doctors
        except Exception as e:
            logger.error(f"Error fetching doctors: {str(e)}", self.logger_name)
            return []
    
    def update(self, doctor_id, doctor_data):
        try:
            with db_manager.get_session() as session:
                doctor = session.query(Doctor).filter(Doctor.id == doctor_id).first()
                if doctor:
                    for key, value in doctor_data.items():
                        # Convert empty strings to None for time fields
                        if key in ['schedule_start', 'schedule_end'] and value == '':
                            value = None
                        setattr(doctor, key, value)
                    session.flush()
                    doctor_id_val = doctor.id  # Access id while session is active
                    logger.info(f"Doctor updated: {doctor.employee_id}", self.logger_name)
                    session.expunge(doctor)  # Detach from session
                    doctor.id = doctor_id_val  # Set id on detached object
                    return doctor
        except Exception as e:
            logger.error(f"Error updating doctor: {str(e)}", self.logger_name)
            raise
    
    def delete(self, doctor_id):
        try:
            with db_manager.get_session() as session:
                doctor = session.query(Doctor).filter(Doctor.id == doctor_id).first()
                if doctor:
                    doctor.is_active = False
                    logger.info(f"Doctor deactivated: {doctor.employee_id}", self.logger_name)
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting doctor: {str(e)}", self.logger_name)
            raise