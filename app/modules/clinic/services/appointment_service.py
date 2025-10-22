from sqlalchemy.orm import Session
from app.db.models.clinic_models.appointment_model import Appointment
from app.db.repositories.base_repository import BaseRepository

class AppointmentService:
    def __init__(self, db: Session):
        self.repository = BaseRepository(Appointment, db)
    
    def create(self, data):
        return self.repository.create(data)
    
    def update(self, entity_id, data):
        return self.repository.update(entity_id, data)
    
    def get_by_id(self, appointment_id):
        return self.repository.get(appointment_id)
    
    def get_all(self, skip=0, limit=100):
        return self.repository.get_all(skip, limit)
    
    def delete(self, appointment_id):
        return self.repository.delete(appointment_id)