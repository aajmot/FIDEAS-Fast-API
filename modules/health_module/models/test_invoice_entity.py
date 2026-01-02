from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Numeric, ARRAY, Date, Computed
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.connection import Base

class TestInvoice(Base):
    __tablename__ = 'test_invoices'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    branch_id = Column(Integer, ForeignKey('branches.id'))
    
    invoice_number = Column(String(50), nullable=False)
    invoice_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    due_date = Column(Date)
    
    test_order_id = Column(Integer, ForeignKey('test_orders.id'), nullable=False)
    
    patient_id = Column(Integer, ForeignKey('patients.id'))
    patient_name = Column(String(200), nullable=False)
    patient_phone = Column(String(20), nullable=False)
    
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
    
    paid_amount = Column(Numeric(12, 4), nullable=False, default=0)
    
    payment_status = Column(String(20), default='UNPAID')
    status = Column(String(20), default='DRAFT')
    
    voucher_id = Column(Integer, ForeignKey('vouchers.id'))
    
    notes = Column(Text)
    tags = Column(ARRAY(Text))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    items = relationship("TestInvoiceItem", back_populates="invoice")
    voucher = relationship("Voucher")

class TestInvoiceItem(Base):
    __tablename__ = 'test_invoice_items'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    test_invoice_id = Column(Integer, ForeignKey('test_invoices.id'), nullable=False)
    line_no = Column(Integer, nullable=False)
    
    test_id = Column(Integer, ForeignKey('tests.id'))
    test_name = Column(String(200))
    panel_id = Column(Integer, ForeignKey('test_panels.id'))
    panel_name = Column(String(200))
    
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
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default='system')
    is_deleted = Column(Boolean, default=False)
    
    invoice = relationship("TestInvoice", back_populates="items")
