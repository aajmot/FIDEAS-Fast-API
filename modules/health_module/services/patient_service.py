from core.database.connection import db_manager
from modules.health_module.models.clinic_entities import Patient
from core.shared.utils.logger import logger
from datetime import datetime

class PatientService:
    def __init__(self):
        self.logger_name = "PatientService"
    
    def create(self, patient_data):
        try:
            with db_manager.get_session() as session:
                # Generate patient number in P-[tenantid]ddmmyyyyhhmmssfff format
                tenant_id = patient_data.get('tenant_id')
                if not tenant_id:
                    raise ValueError("tenant_id is required")
                now = datetime.now()
                patient_number = f"P-{tenant_id}{now.strftime('%d%m%Y%H%M%S%f')[:17]}"
                
                patient = Patient(
                    patient_number=patient_number,
                    **patient_data
                )
                session.add(patient)
                session.flush()
                patient_id = patient.id  # Access id while session is active
                logger.info(f"Patient created: {patient.patient_number}", self.logger_name)
                session.expunge(patient)  # Detach from session
                patient.id = patient_id  # Set id on detached object
                return patient
        except Exception as e:
            logger.error(f"Error creating patient: {str(e)}", self.logger_name)
            raise
    
    def get_all(self, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(Patient)
                if tenant_id:
                    query = query.filter(Patient.tenant_id == tenant_id)
                patients = query.filter(Patient.is_active == True).all()
                # Detach from session to avoid lazy loading issues
                for patient in patients:
                    session.expunge(patient)
                return patients
        except Exception as e:
            logger.error(f"Error fetching patients: {str(e)}", self.logger_name)
            return []
    
    def get_by_id(self, patient_id):
        try:
            with db_manager.get_session() as session:
                return session.query(Patient).filter(Patient.id == patient_id).first()
        except Exception as e:
            logger.error(f"Error fetching patient: {str(e)}", self.logger_name)
            return None
    
    def update(self, patient_id, patient_data):
        try:
            with db_manager.get_session() as session:
                patient = session.query(Patient).filter(Patient.id == patient_id).first()
                if patient:
                    for key, value in patient_data.items():
                        setattr(patient, key, value)
                    session.flush()
                    patient_id_val = patient.id  # Access id while session is active
                    logger.info(f"Patient updated: {patient.patient_number}", self.logger_name)
                    session.expunge(patient)  # Detach from session
                    patient.id = patient_id_val  # Set id on detached object
                    return patient
        except Exception as e:
            logger.error(f"Error updating patient: {str(e)}", self.logger_name)
            raise
    
    def delete(self, patient_id):
        try:
            with db_manager.get_session() as session:
                patient = session.query(Patient).filter(Patient.id == patient_id).first()
                if patient:
                    patient.is_active = False
                    logger.info(f"Patient deactivated: {patient.patient_number}", self.logger_name)
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting patient: {str(e)}", self.logger_name)
            raise