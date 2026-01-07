from core.database.connection import db_manager
from modules.health_module.models.test_invoice_entity import TestInvoice, TestInvoiceItem
from modules.health_module.models.test_order_entity import TestOrder
from modules.account_module.models.entities import Voucher, VoucherLine, VoucherType
from modules.account_module.services.account_master_service import AccountMasterService
from core.shared.utils.logger import logger
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import or_
import math

class TestInvoiceService:
    def __init__(self):
        self.logger_name = "TestInvoiceService"
    
    def _generate_voucher_number(self, session, tenant_id, prefix="VOU"):
        today = datetime.now().strftime("%Y%m%d")
        last_voucher = session.query(Voucher).filter(
            Voucher.voucher_number.like(f"{prefix}{today}%"),
            Voucher.tenant_id == tenant_id
        ).order_by(Voucher.id.desc()).first()
        
        seq = int(last_voucher.voucher_number[-3:]) + 1 if last_voucher else 1
        return f"{prefix}{today}{seq:03d}"
    
    def _create_voucher(self, session, invoice, tenant_id, username):
        account_service = AccountMasterService()
        
        # Get accounts using specific methods
        receivable_account = account_service.get_accounts_receivable(session, tenant_id)
        revenue_account = account_service.get_test_revenue(session, tenant_id)
        
        if not receivable_account:
            raise ValueError("Accounts Receivable account not found")
        if not revenue_account:
            raise ValueError("Test Revenue account not found")
        
        voucher_type = session.query(VoucherType).filter(
            VoucherType.code == 'SALES',
            VoucherType.tenant_id == tenant_id
        ).first()
        
        if not voucher_type:
            voucher_type = session.query(VoucherType).filter(
                VoucherType.tenant_id == tenant_id
            ).first()
        
        if not voucher_type:
            raise ValueError("No voucher type found")
        
        voucher = Voucher(
            tenant_id=tenant_id,
            voucher_type_id=voucher_type.id,
            voucher_number=self._generate_voucher_number(session, tenant_id),
            voucher_date=invoice.invoice_date,
            base_currency_id=1,
            base_total_amount=float(invoice.final_amount),
            base_total_debit=float(invoice.final_amount),
            base_total_credit=float(invoice.final_amount),
            reference_type='TEST_INVOICE',
            reference_id=invoice.id,
            reference_number=invoice.invoice_number,
            narration=f"Test Invoice {invoice.invoice_number} - {invoice.patient_name}",
            created_by=username
        )
        session.add(voucher)
        session.flush()
        
        # Debit: Accounts Receivable
        debit_line = VoucherLine(
            tenant_id=tenant_id,
            voucher_id=voucher.id,
            line_no=1,
            account_id=receivable_account['id'],
            description=f"Test Invoice - {invoice.patient_name}",
            debit_base=float(invoice.final_amount),
            credit_base=0,
            created_by=username
        )
        session.add(debit_line)
        
        # Credit: Revenue
        credit_line = VoucherLine(
            tenant_id=tenant_id,
            voucher_id=voucher.id,
            line_no=2,
            account_id=revenue_account['id'],
            description=f"Test Revenue - {invoice.invoice_number}",
            debit_base=0,
            credit_base=float(invoice.final_amount),
            created_by=username
        )
        session.add(credit_line)
        
        return voucher.id
    
    def create(self, data):
        try:
            with db_manager.get_session() as session:
                items = data.pop('items', [])
                tenant_id = data['tenant_id']
                username = data.pop('created_by', 'system')
                
                invoice = TestInvoice(**data)
                session.add(invoice)
                session.flush()
                
                for item in items:
                    item['test_invoice_id'] = invoice.id
                    item['tenant_id'] = tenant_id
                    item['created_by'] = username
                    invoice_item = TestInvoiceItem(**item)
                    session.add(invoice_item)
                
                # Create voucher if status is POSTED
                if invoice.status == 'POSTED':
                    voucher_id = self._create_voucher(session, invoice, tenant_id, username)
                    invoice.voucher_id = voucher_id
                
                session.flush()
                invoice_id = invoice.id
                logger.info(f"Test invoice created: {invoice.invoice_number}", self.logger_name)
                return invoice_id
        except Exception as e:
            logger.error(f"Error creating test invoice: {str(e)}", self.logger_name)
            raise
    
    def get_by_id(self, invoice_id, tenant_id, include_barcode=False):
        try:
            with db_manager.get_session() as session:
                invoice = session.query(TestInvoice).filter(
                    TestInvoice.id == invoice_id,
                    TestInvoice.tenant_id == tenant_id,
                    TestInvoice.is_deleted == False
                ).first()
                
                if not invoice:
                    return None
                
                items = session.query(TestInvoiceItem).filter(
                    TestInvoiceItem.test_invoice_id == invoice_id,
                    TestInvoiceItem.is_deleted == False
                ).all()
                
                # Get order details
                order = session.query(TestOrder).filter(
                    TestOrder.id == invoice.test_order_id,
                    TestOrder.is_deleted == False
                ).first()
                
                order_data = None
                if order:
                    order_data = {
                        "id": order.id,
                        "test_order_number": order.test_order_number,
                        "order_date": order.order_date.isoformat() if order.order_date else None,
                        "doctor_name": order.doctor_name,
                        "doctor_phone": order.doctor_phone,
                        "urgency": order.urgency,
                        "status": order.status
                    }
                
                result = {
                    "id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
                    "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
                    "test_order_id": invoice.test_order_id,
                    "order": order_data,
                    "patient_id": invoice.patient_id,
                    "patient_name": invoice.patient_name,
                    "patient_phone": invoice.patient_phone,
                    "subtotal_amount": float(invoice.subtotal_amount),
                    "items_total_discount_amount": float(invoice.items_total_discount_amount or 0),
                    "taxable_amount": float(invoice.taxable_amount),
                    "cgst_amount": float(invoice.cgst_amount or 0),
                    "sgst_amount": float(invoice.sgst_amount or 0),
                    "igst_amount": float(invoice.igst_amount or 0),
                    "cess_amount": float(invoice.cess_amount or 0),
                    "overall_disc_percentage": float(invoice.overall_disc_percentage or 0),
                    "overall_disc_amount": float(invoice.overall_disc_amount or 0),
                    "roundoff": float(invoice.roundoff or 0),
                    "final_amount": float(invoice.final_amount),
                    "paid_amount": float(invoice.paid_amount or 0),
                    "balance_amount":float(invoice.balance_amount or 0),
                    "payment_status": invoice.payment_status,
                    "status": invoice.status,
                    "voucher_id": invoice.voucher_id,
                    "notes": invoice.notes,
                    "tags": invoice.tags,
                    "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
                    "created_by": invoice.created_by,
                    "items": [{
                        "id": item.id,
                        "line_no": item.line_no,
                        "test_id": item.test_id,
                        "test_name": item.test_name,
                        "panel_id": item.panel_id,
                        "panel_name": item.panel_name,
                        "rate": float(item.rate),
                        "disc_percentage": float(item.disc_percentage or 0),
                        "disc_amount": float(item.disc_amount or 0),
                        "taxable_amount": float(item.taxable_amount),
                        "cgst_rate": float(item.cgst_rate or 0),
                        "cgst_amount": float(item.cgst_amount or 0),
                        "sgst_rate": float(item.sgst_rate or 0),
                        "sgst_amount": float(item.sgst_amount or 0),
                        "igst_rate": float(item.igst_rate or 0),
                        "igst_amount": float(item.igst_amount or 0),
                        "cess_rate": float(item.cess_rate or 0),
                        "cess_amount": float(item.cess_amount or 0),
                        "total_amount": float(item.total_amount),
                        "remarks": item.remarks
                    } for item in items]
                }
                
                if include_barcode:
                    from core.shared.utils.barcode_utils import BarcodeGenerator
                    try:
                        #result["barcode"] = BarcodeGenerator.generate_barcode(invoice.invoice_number)
                        qr_data = f"/test-invoice?TEST_INVOICE={invoice.invoice_number}"
                        result["qr_code"] = BarcodeGenerator.generate_qr_code(qr_data)
                    except Exception as e:
                        logger.error(f"Barcode generation failed: {str(e)}", self.logger_name)
                        # result["barcode"] = None
                        result["qr_code"] = None
                
                return result
        except Exception as e:
            logger.error(f"Error fetching test invoice: {str(e)}", self.logger_name)
            raise
    
    def get_all(self, tenant_id, page=1, per_page=10, search=None, status=None, payment_status=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(TestInvoice).join(TestOrder).filter(
                    TestInvoice.tenant_id == tenant_id,
                    TestInvoice.is_deleted == False
                ).order_by(TestInvoice.id.desc())
                
                if search:
                    query = query.filter(or_(
                        TestInvoice.invoice_number.ilike(f"%{search}%"),
                        TestInvoice.patient_name.ilike(f"%{search}%")
                    ))
                
                if status:
                    query = query.filter(TestInvoice.status == status)
                else:
                    query = query.filter(TestInvoice.status=="POSTED")
                
                if payment_status:
                    query = query.filter(TestInvoice.payment_status == payment_status)
                
                total = query.count()
                offset = (page - 1) * per_page
                results = query.offset(offset).limit(per_page).all()
                
                data = []
                for inv in results:
                    order = session.query(TestOrder).filter(
                        TestOrder.id == inv.test_order_id,
                        TestOrder.is_deleted == False
                    ).first()
                    
                    order_data = None
                    if order:
                        order_data = {
                            "id": order.id,
                            "test_order_number": order.test_order_number,
                            "order_date": order.order_date.isoformat() if order.order_date else None,
                            "doctor_name": order.doctor_name,
                            "urgency": order.urgency,
                            "status": order.status
                        }
                    
                    data.append({
                        "id": inv.id,
                        "invoice_number": inv.invoice_number,
                        "invoice_date": inv.invoice_date.isoformat() if inv.invoice_date else None,
                        "test_order_id": inv.test_order_id,
                        "order": order_data,
                        "patient_id": inv.patient_id,
                        "patient_name": inv.patient_name,
                        "patient_phone": inv.patient_phone,
                        "final_amount": float(inv.final_amount),
                        "paid_amount": float(inv.paid_amount or 0),
                        "balance_amount":float(inv.balance_amount or 0),   
                        "payment_status": inv.payment_status,
                        "status": inv.status
                    })
                
                return {
                    "data": data,
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": math.ceil(total / per_page)
                }
        except Exception as e:
            logger.error(f"Error fetching test invoices: {str(e)}", self.logger_name)
            raise
    
    def update(self, invoice_id, data, tenant_id):
        try:
            with db_manager.get_session() as session:
                invoice = session.query(TestInvoice).filter(
                    TestInvoice.id == invoice_id,
                    TestInvoice.tenant_id == tenant_id,
                    TestInvoice.is_deleted == False
                ).first()
                
                if not invoice:
                    raise HTTPException(status_code=404, detail="Invoice not found")
                
                for key, value in data.items():
                    if key not in ['id', 'created_at', 'created_by', 'tenant_id']:
                        setattr(invoice, key, value)
                
                invoice.updated_at = datetime.utcnow()
                session.flush()
                logger.info(f"Test invoice updated: {invoice.invoice_number}", self.logger_name)
                return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating test invoice: {str(e)}", self.logger_name)
            raise
