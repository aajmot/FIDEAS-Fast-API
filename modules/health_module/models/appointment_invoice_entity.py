from sqlalchemy import Column, FetchedValue, Integer, String, DateTime, Boolean, ForeignKey, Text, Numeric, ARRAY, Date, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.connection import Base

class AppointmentInvoice(Base):
    __tablename__ = 'appointment_invoices'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    branch_id = Column(Integer, ForeignKey('branches.id'))
    appointment_id = Column(Integer, ForeignKey('appointments.id'), nullable=False)
    
    # Invoice Info
    invoice_number = Column(String(50), nullable=False)
    invoice_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    due_date = Column(Date)
    
    # Patient Info (denormalized)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    patient_name = Column(String(100))
    patient_phone = Column(String(20))
    patient_email = Column(String(100))
    patient_address = Column(Text)
    patient_dob = Column(Date)
    patient_gender = Column(String(10))
    
    # Doctor Info (denormalized)
    doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=False)
    doctor_name = Column(String(100))
    doctor_phone = Column(String(20))
    doctor_email = Column(String(100))
    doctor_address = Column(Text)
    doctor_license_number = Column(String(50))
    doctor_speciality = Column(String(100))
    
    # Billing Summary
    subtotal_amount = Column(Numeric(12, 4), nullable=False, default=0)
    items_total_discount_amount = Column(Numeric(12, 4), default=0)
    taxable_amount = Column(Numeric(12, 4), nullable=False, default=0)
    
    cgst_amount = Column(Numeric(12, 4), default=0)
    sgst_amount = Column(Numeric(12, 4), default=0)
    igst_amount = Column(Numeric(12, 4), default=0)
    cess_amount = Column(Numeric(12, 4), default=0)
    
    overall_disc_percentage = Column(Numeric(5, 4), nullable=False, default=0)
    overall_disc_amount = Column(Numeric(12, 4), nullable=False, default=0)
    
    roundoff = Column(Numeric(12, 4), default=0)
    final_amount = Column(Numeric(12, 4), nullable=False)
    
    # Payment Tracking
    paid_amount = Column(Numeric(12, 4), nullable=False, default=0)
    balance_amount = Column(Numeric(12, 4), server_default=FetchedValue(), nullable=False)
    
    # Status
    payment_status = Column(String(20), default='UNPAID')
    status = Column(String(20), default='DRAFT')
    
    # Accounting
    voucher_id = Column(Integer, ForeignKey('vouchers.id'))
    
    # Notes
    notes = Column(Text)
    tags = Column(ARRAY(Text))
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    appointment = relationship("Appointment", backref="invoices")
    items = relationship("AppointmentInvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    voucher = relationship("Voucher")

class AppointmentInvoiceItem(Base):
    __tablename__ = 'appointment_invoice_items'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    invoice_id = Column(Integer, ForeignKey('appointment_invoices.id'), nullable=False)
    line_no = Column(Integer, nullable=False)
    
    # Reference to billing master
    billing_master_id = Column(Integer, ForeignKey('clinic_billing_master.id'))
    
    # Item details (denormalized)
    description = Column(Text, nullable=False)
    hsn_code = Column(String(20))
    
    # Pricing
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(12, 4), nullable=False)
    rate = Column(Numeric(12, 4), nullable=False)
    disc_percentage = Column(Numeric(5, 2), default=0)
    disc_amount = Column(Numeric(12, 4), default=0)
    
    taxable_amount = Column(Numeric(12, 4), nullable=False)
    cgst_rate = Column(Numeric(5, 2), default=0)
    cgst_amount = Column(Numeric(12, 4), default=0)
    sgst_rate = Column(Numeric(5, 2), default=0)
    sgst_amount = Column(Numeric(12, 4), default=0)
    igst_rate = Column(Numeric(5, 2), default=0)
    igst_amount = Column(Numeric(12, 4), default=0)
    cess_rate = Column(Numeric(5, 2), default=0)
    cess_amount = Column(Numeric(12, 4), default=0)
    
    total_amount = Column(Numeric(12, 4), nullable=False)
    remarks = Column(Text)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    invoice = relationship("AppointmentInvoice", back_populates="items")
