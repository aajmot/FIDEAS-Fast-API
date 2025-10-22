from sqlalchemy.orm import Session
from app.db.models.clinic_models.patient_model import Patient
from app.db.repositories.base_repository import BaseRepository

class PatientService:
    def __init__(self, db: Session):
        self.repository = BaseRepository(Patient, db)
    
    def create(self, data):
        return self.repository.create(data)
    
    def update(self, entity_id, data):
        return self.repository.update(entity_id, data)
    
    def get_by_id(self, patient_id):
        return self.repository.get(patient_id)
    
    def get_all(self, skip=0, limit=100):
        return self.repository.get_all(skip, limit)
    
    def delete(self, patient_id):
        return self.repository.delete(patient_id)