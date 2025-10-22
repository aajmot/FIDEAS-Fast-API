from sqlalchemy import Column, Integer, String, Boolean, Text, Date
from app.db.models.base_model import BaseModel

class Patient(BaseModel):
    __tablename__ = 'patients'
    
    patient_number = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date)
    gender = Column(String(10))
    phone = Column(String(20), nullable=False)
    email = Column(String(100))
    address = Column(Text)
    emergency_contact = Column(String(100))
    emergency_phone = Column(String(20))
    blood_group = Column(String(5))
    allergies = Column(Text)
    medical_history = Column(Text)
    tenant_id = Column(Integer, nullable=False)
    created_by = Column(String(100))