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
from sqlalchemy.orm import joinedload, selectinload

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
    
    def _map_invoice_to_dict(self, inv, include_items=False, include_order_details=False):
        """Helper to serialize invoice objects consistently."""
        # Map Order data
        order_data = None
        if inv.test_order:
            order_data = {
                "id": inv.test_order.id,
                "test_order_number": inv.test_order.test_order_number,
                "status": inv.test_order.status
            }
            if include_order_details:
                order_data.update({
                    "order_date": inv.test_order.order_date.isoformat() if inv.test_order.order_date else None,
                    "doctor_name": inv.test_order.doctor_name,
                    "doctor_phone": inv.test_order.doctor_phone,
                    "urgency": inv.test_order.urgency,
                })

        # Base Invoice Data
        result = {
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "invoice_date": inv.invoice_date.isoformat() if inv.invoice_date else None,
            "patient_id": inv.patient_id,
            "patient_name": inv.patient_name,
            "patient_phone": inv.patient_phone,
            "final_amount": float(inv.final_amount),
            "paid_amount": float(inv.paid_amount or 0),
            "balance_amount": float(inv.balance_amount or 0),
            "payment_status": inv.payment_status,
            "status": inv.status,
            "order": order_data
        }

        # Include Items if loaded
        if include_items and hasattr(inv, 'items'):
            result["items"] = [{
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
            } for item in inv.items if not item.is_deleted]

        return result

    def get_by_id(self, invoice_id, tenant_id, include_barcode=False):
        try:
            with db_manager.get_session() as session:
                # Fetch everything in a single optimized query
                invoice = session.query(TestInvoice).options(
                    joinedload(TestInvoice.test_order),
                    selectinload(TestInvoice.items)
                ).filter(
                    TestInvoice.id == invoice_id,
                    TestInvoice.tenant_id == tenant_id,
                    TestInvoice.is_deleted == False
                ).first()

                if not invoice:
                    return None

                # Reuse mapper for high-detail view
                result = self._map_invoice_to_dict(invoice, include_items=True, include_order_details=True)
                
                # Add extra fields specific to get_by_id
                result.update({
                    "branch_id": invoice.branch_id,
                    "test_order_id": invoice.test_order_id,
                    "subtotal_amount": float(invoice.subtotal_amount or 0),
                    "items_total_discount_amount": float(invoice.items_total_discount_amount or 0),
                    "taxable_amount": float(invoice.taxable_amount or 0),
                    "cgst_amount": float(invoice.cgst_amount or 0),
                    "sgst_amount": float(invoice.sgst_amount or 0),
                    "igst_amount": float(invoice.igst_amount or 0),
                    "cess_amount": float(invoice.cess_amount or 0),
                    "overall_disc_percentage": float(invoice.overall_disc_percentage or 0),
                    "overall_disc_amount": float(invoice.overall_disc_amount or 0),
                    "roundoff": float(invoice.roundoff or 0),
                    "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
                    "voucher_id": invoice.voucher_id,
                    "notes": invoice.notes,
                    "tags": invoice.tags,
                    "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
                    "created_by": invoice.created_by,
                    "updated_at": invoice.updated_at.isoformat() if invoice.updated_at else None,
                    "updated_by": invoice.updated_by,
                    "is_active": invoice.is_active
                })

                if include_barcode:
                    from core.shared.utils.barcode_utils import BarcodeGenerator
                    try:
                        qr_data = f"/test-invoice?TEST_INVOICE={invoice.invoice_number}"
                        result["qr_code"] = BarcodeGenerator.generate_qr_code(qr_data)
                    except Exception as e:
                        logger.error(f"Barcode generation failed: {str(e)}", self.logger_name)
                        result["qr_code"] = None

                return result
        except Exception as e:
            logger.error(f"Error fetching test invoice {invoice_id}: {str(e)}", self.logger_name)
            raise

    def get_all(self, tenant_id, page=1, per_page=10, search=None, patient_id=None, status=None, payment_status=None, include_items=False):
        try:
            with db_manager.get_session() as session:
                # 1. Base query with eager loading
                query = session.query(TestInvoice).options(joinedload(TestInvoice.test_order))
                
                if include_items:
                    query = query.options(selectinload(TestInvoice.items))

                # 2. Filtering
                query = query.filter(TestInvoice.tenant_id == tenant_id, TestInvoice.is_deleted == False)

                if patient_id:
                    query = query.filter(TestInvoice.patient_id == patient_id)
                
                if search:
                    query = query.filter(or_(
                        TestInvoice.invoice_number.ilike(f"%{search}%"),
                        TestInvoice.patient_name.ilike(f"%{search}%")
                    ))

                # Handle Statuses
                if status:
                    query = query.filter(TestInvoice.status.in_(status) if isinstance(status, list) else TestInvoice.status == status)
                else:
                    query = query.filter(TestInvoice.status == "POSTED")

                if payment_status:
                    query = query.filter(TestInvoice.payment_status.in_(payment_status) if isinstance(payment_status, list) else TestInvoice.payment_status == payment_status)

                # 3. Pagination & Execution
                total = query.count()
                results = query.order_by(TestInvoice.id.desc()).offset((page - 1) * per_page).limit(per_page).all()

                return {
                    "data": [self._map_invoice_to_dict(inv, include_items=include_items) for inv in results],
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": math.ceil(total / per_page)
                }
        except Exception as e:
            logger.error(f"Error listing invoices: {str(e)}", self.logger_name)
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

