from core.database.connection import db_manager
from modules.clinic_module.models.entities import Invoice, InvoiceItem, Patient
from modules.account_module.models.entities import Voucher, VoucherType
from modules.account_module.services.voucher_service import VoucherService
from core.shared.utils.logger import logger
from datetime import datetime

class BillingService:
    def __init__(self):
        self.logger_name = "BillingService"
        self.voucher_service = VoucherService()
    
    def create_invoice(self, invoice_data, items_data):
        try:
            with db_manager.get_session() as session:
                # Use provided invoice number or generate new one
                now = datetime.now()
                tenant_id = invoice_data.get('tenant_id', 1)
                invoice_number = invoice_data.get('invoice_number')
                if not invoice_number:
                    invoice_number = f"CINV-{tenant_id}{now.strftime('%d%m%Y%H%M%S%f')[:15]}"
                
                # Ensure required fields have default values
                total_amount = invoice_data.get('total_amount', 0)
                final_amount = invoice_data.get('final_amount', total_amount)
                
                # Create invoice with only valid fields
                invoice = Invoice(
                    invoice_number=invoice_number,
                    appointment_id=invoice_data.get('appointment_id'),
                    patient_id=invoice_data['patient_id'],
                    invoice_date=invoice_data.get('invoice_date', now),
                    consultation_fee=invoice_data.get('consultation_fee', 0),
                    total_amount=total_amount,
                    discount_percentage=invoice_data.get('discount_percentage', 0),
                    discount_amount=invoice_data.get('discount_amount', 0),
                    final_amount=final_amount,
                    payment_status=invoice_data.get('payment_status', 'pending'),
                    payment_method=invoice_data.get('payment_method'),
                    insurance_provider=invoice_data.get('insurance_provider'),
                    insurance_claim_number=invoice_data.get('insurance_claim_number'),
                    tenant_id=tenant_id,
                    created_by=invoice_data.get('created_by')
                )
                session.add(invoice)
                session.flush()
                
                # Create invoice items
                for item_data in items_data:
                    item = InvoiceItem(
                        invoice_id=invoice.id,
                        item_type=item_data['item_type'],
                        product_id=item_data.get('product_id'),
                        description=item_data['description'],
                        quantity=item_data.get('quantity', 1),
                        unit_price=item_data['unit_price'],
                        total_price=item_data['total_price']
                    )
                    session.add(item)
                
                session.commit()
                invoice_id = invoice.id
                session.expunge(invoice)
                invoice.id = invoice_id
                return invoice
        except Exception as e:
            logger.error(f"Error creating invoice: {str(e)}", self.logger_name)
            raise
    
    def _get_sales_voucher_type_id(self, session):
        voucher_type = session.query(VoucherType).filter(VoucherType.code == 'SV').first()
        return voucher_type.id if voucher_type else 1
    
    def update(self, invoice_id, invoice_data, items_data=None):
        try:
            with db_manager.get_session() as session:
                invoice = session.query(Invoice).filter(Invoice.id == invoice_id).first()
                if invoice:
                    for key, value in invoice_data.items():
                        if hasattr(invoice, key):
                            setattr(invoice, key, value)
                    
                    # Update invoice items if provided
                    if items_data is not None:
                        # Delete existing items
                        session.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice_id).delete()
                        
                        # Create new items
                        for item_data in items_data:
                            item = InvoiceItem(
                                invoice_id=invoice.id,
                                item_type=item_data['item_type'],
                                product_id=item_data.get('product_id'),
                                description=item_data['description'],
                                quantity=item_data.get('quantity', 1),
                                unit_price=item_data['unit_price'],
                                total_price=item_data['total_price']
                            )
                            session.add(item)
                    
                    session.flush()
                    invoice_id_val = invoice.id  # Access id while session is active
                    logger.info(f"Invoice updated: {invoice.invoice_number}", self.logger_name)
                    session.expunge(invoice)  # Detach from session
                    invoice.id = invoice_id_val  # Set id on detached object
                    return invoice
                return None
        except Exception as e:
            logger.error(f"Error updating invoice: {str(e)}", self.logger_name)
            raise
    
    def update_payment_status(self, invoice_id, payment_status, payment_method=None):
        try:
            with db_manager.get_session() as session:
                invoice = session.query(Invoice).filter(Invoice.id == invoice_id).first()
                if invoice:
                    invoice.payment_status = payment_status
                    if payment_method:
                        invoice.payment_method = payment_method
                    session.flush()
                    invoice_id_val = invoice.id  # Access id while session is active
                    logger.info(f"Invoice payment status updated: {invoice.invoice_number} -> {payment_status}", self.logger_name)
                    session.expunge(invoice)  # Detach from session
                    invoice.id = invoice_id_val  # Set id on detached object
                    return invoice
        except Exception as e:
            logger.error(f"Error updating payment status: {str(e)}", self.logger_name)
            raise
    
    def get_all(self, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                from modules.clinic_module.models.entities import Appointment
                query = session.query(Invoice).outerjoin(Patient).outerjoin(Appointment)
                if tenant_id:
                    query = query.filter(Invoice.tenant_id == tenant_id)
                invoices = query.all()
                return invoices
        except Exception as e:
            logger.error(f"Error fetching invoices: {str(e)}", self.logger_name)
            return []
    
    def get_pending_invoices(self, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(Invoice).join(Patient).filter(Invoice.payment_status == 'pending')
                if tenant_id:
                    query = query.filter(Invoice.tenant_id == tenant_id)
                invoices = query.all()
                # Access related objects before expunging
                for invoice in invoices:
                    _ = invoice.patient.first_name  # Force load patient data
                    session.expunge(invoice)
                return invoices
        except Exception as e:
            logger.error(f"Error fetching pending invoices: {str(e)}", self.logger_name)
            return []
    
    def delete(self, invoice_id):
        try:
            with db_manager.get_session() as session:
                invoice = session.query(Invoice).filter(Invoice.id == invoice_id).first()
                if invoice:
                    # Delete invoice items first
                    session.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice_id).delete()
                    # Delete invoice
                    session.delete(invoice)
                    session.commit()
                    logger.info(f"Invoice deleted: {invoice.invoice_number}", self.logger_name)
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting invoice: {str(e)}", self.logger_name)
            raise