from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Date, Time
from sqlalchemy.types import Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.connection import Base

class Patient(Base):
    __tablename__ = 'patients'
    
    id = Column(Integer, primary_key=True)
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
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    
    appointments = relationship("Appointment", back_populates="patient")
    prescriptions = relationship("Prescription", back_populates="patient")
    invoices = relationship("Invoice", back_populates="patient")

class Doctor(Base):
    __tablename__ = 'doctors'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    specialization = Column(String(100))
    license_number = Column(String(50))
    phone = Column(String(20), nullable=False)
    email = Column(String(100))
    schedule_start = Column(Time)
    schedule_end = Column(Time)
    consultation_fee = Column(Numeric(10, 2))
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    appointments = relationship("Appointment", back_populates="doctor")
    prescriptions = relationship("Prescription", back_populates="doctor")

class Appointment(Base):
    __tablename__ = 'appointments'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    branch_id = Column(Integer, ForeignKey('branches.id'))
    
    appointment_number = Column(String(50), nullable=False)
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer)
    
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    patient_name = Column(String(100))
    patient_phone = Column(String(20))
    
    doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=False)
    doctor_name = Column(String(100))
    doctor_phone = Column(String(20))
    doctor_license_number = Column(String(50))
    doctor_specialization = Column(String(100))
    
    agency_id = Column(Integer, ForeignKey('agencies.id'))
    agency_name = Column(String(100))
    agency_phone = Column(String(20))
    
    status = Column(String(20), default='SCHEDULED')
    reason = Column(Text)
    notes = Column(Text)
    
    medical_record_generated = Column(Boolean, default=False)
    medical_record_id = Column(Integer)
    prescription_generated = Column(Boolean, default=False)
    prescription_id = Column(Integer)
    appointment_invoice_generated = Column(Boolean, default=False)
    appointment_invoice_id = Column(Integer)
    test_order_generated = Column(Boolean, default=False)
    test_order_id = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    medical_records = relationship("MedicalRecord", back_populates="appointment")

class MedicalRecord(Base):
    __tablename__ = 'medical_records'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    branch_id = Column(Integer, ForeignKey('branches.id'))
    appointment_id = Column(Integer, ForeignKey('appointments.id'), nullable=False)
    record_number = Column(String(50), unique=True, nullable=False)
    visit_date = Column(DateTime, default=datetime.utcnow)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    patient_name = Column(String(100))
    doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=False)
    doctor_name = Column(String(100))
    chief_complaint = Column(Text)
    diagnosis = Column(Text)
    treatment_plan = Column(Text)
    vital_signs = Column(Text)
    lab_results = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    appointment = relationship("Appointment", back_populates="medical_records")

class Prescription(Base):
    __tablename__ = 'prescriptions'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    branch_id = Column(Integer, ForeignKey('branches.id'))
    appointment_id = Column(Integer, ForeignKey('appointments.id'), nullable=False)
    prescription_number = Column(String(50), unique=True, nullable=False)
    prescription_date = Column(DateTime, default=datetime.utcnow)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    patient_name = Column(String(100))
    patient_phone = Column(String(20))
    doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=False)
    doctor_name = Column(String(100))
    doctor_license_number = Column(String(50))
    instructions = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    patient = relationship("Patient", back_populates="prescriptions")
    doctor = relationship("Doctor", back_populates="prescriptions")
    appointment = relationship("Appointment")
    prescription_items = relationship("PrescriptionItem", back_populates="prescription")
    prescription_test_items = relationship("PrescriptionTestItem", back_populates="prescription")

class PrescriptionItem(Base):
    __tablename__ = 'prescription_items'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    branch_id = Column(Integer, ForeignKey('branches.id'))
    prescription_id = Column(Integer, ForeignKey('prescriptions.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    product_name = Column(String(200))
    dosage = Column(String(100))
    frequency = Column(String(100))
    duration = Column(String(100))
    quantity = Column(Numeric(10, 2))
    instructions = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    prescription = relationship("Prescription", back_populates="prescription_items")

class PrescriptionTestItem(Base):
    __tablename__ = 'prescription_test_items'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    branch_id = Column(Integer, ForeignKey('branches.id'))
    prescription_id = Column(Integer, ForeignKey('prescriptions.id'), nullable=False)
    test_id = Column(Integer, ForeignKey('tests.id'), nullable=False)
    test_name = Column(String(200))
    instructions = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    prescription = relationship("Prescription", back_populates="prescription_test_items")

class Invoice(Base):
    __tablename__ = 'clinic_invoices'
    
    id = Column(Integer, primary_key=True)
    invoice_number = Column(String(50), unique=True, nullable=False)
    appointment_id = Column(Integer, ForeignKey('appointments.id'))
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    invoice_date = Column(DateTime, default=datetime.utcnow)
    consultation_fee = Column(Numeric(10, 2), default=0)
    total_amount = Column(Numeric(10, 2), nullable=False)
    discount_percentage = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    final_amount = Column(Numeric(10, 2), nullable=False)
    payment_status = Column(String(20), default='pending')  # pending, paid, partial
    payment_method = Column(String(20))  # cash, card, insurance
    insurance_provider = Column(String(100))
    insurance_claim_number = Column(String(50))
    voucher_id = Column(Integer, ForeignKey('vouchers.id'))  # Link to accounting
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    
    patient = relationship("Patient", back_populates="invoices")
    appointment = relationship("Appointment")
    invoice_items = relationship("InvoiceItem", back_populates="invoice")

class InvoiceItem(Base):
    __tablename__ = 'clinic_invoice_items'
    
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey('clinic_invoices.id'), nullable=False)
    item_type = Column(String(20), nullable=False)  # consultation, medication, service
    product_id = Column(Integer, ForeignKey('products.id'))  # For medications from inventory
    description = Column(String(200), nullable=False)
    quantity = Column(Numeric(10, 2), default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    
    invoice = relationship("Invoice", back_populates="invoice_items")

class ClinicBillingMaster(Base):
    __tablename__ = 'clinic_billing_master'
    
    id = Column(Integer, primary_key=True)
    description = Column(Text, nullable=False)
    note = Column(Text)
    amount = Column(Numeric(12, 2), nullable=False)
    hsn_code = Column(String(20))
    gst_percentage = Column(Numeric(5, 2), nullable=False, default=0.00)
    tenant_id = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    updated_by = Column(String(100))

class Employee(Base):
    __tablename__ = 'clinic_employees'
    
    id = Column(Integer, primary_key=True)
    employee_number = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)  # nurse, receptionist, admin, technician
    department = Column(String(100))
    phone = Column(String(20), nullable=False)
    email = Column(String(100))
    hire_date = Column(Date)
    salary = Column(Numeric(10, 2))
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))