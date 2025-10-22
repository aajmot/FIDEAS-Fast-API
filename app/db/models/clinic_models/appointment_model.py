from sqlalchemy import Column, Integer, String, Text, Date, Time
from app.db.models.base_model import BaseModel

class Appointment(BaseModel):
    __tablename__ = 'appointments'
    
    appointment_number = Column(String(50), unique=True, nullable=False)
    patient_id = Column(Integer, nullable=False)
    doctor_id = Column(Integer, nullable=False)
    agency_id = Column(Integer)
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, default=30)
    status = Column(String(20), default='scheduled')
    reason = Column(Text)
    notes = Column(Text)
    tenant_id = Column(Integer, nullable=False)
    created_by = Column(String(100))