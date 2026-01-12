from core.database.connection import db_manager
from modules.health_module.models.appointment_invoice_entity import AppointmentInvoice, AppointmentInvoiceItem
from modules.health_module.models.clinic_entities import Appointment
from modules.account_module.models.entities import Voucher, VoucherLine, VoucherType
from modules.account_module.services.account_master_service import AccountMasterService
from core.shared.utils.logger import logger
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import joinedload, selectinload
import math
from core.shared.utils.crypto_utils import crypto_utils

class AppointmentInvoiceService:
    def __init__(self):
        self.logger_name = "AppointmentInvoiceService"
    
    def _generate_voucher_number(self, session, tenant_id, prefix="VOU"):
        try:
            today = datetime.now().strftime("%Y%m%d")
            last_voucher = session.query(Voucher).filter(
                Voucher.voucher_number.like(f"{prefix}{today}%"),
                Voucher.tenant_id == tenant_id
            ).order_by(Voucher.id.desc()).first()
            
            seq = int(last_voucher.voucher_number[-3:]) + 1 if last_voucher else 1
            return f"{prefix}{today}{seq:03d}"
        except Exception as e:
            logger.error(f"Error generating voucher number: {str(e)}", self.logger_name)
            raise
    
    def _create_voucher(self, session, invoice, tenant_id, username):
        try:
            account_service = AccountMasterService()
            
            receivable_account = account_service.get_accounts_receivable(session, tenant_id)
            revenue_account = account_service.get_consultation_revenue(session, tenant_id)
            
            if not receivable_account:
                raise ValueError("Accounts Receivable account not found")
            if not revenue_account:
                raise ValueError("Consultation Revenue account not found")
            
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
                reference_type='APPOINTMENT_INVOICE',
                reference_id=invoice.id,
                reference_number=invoice.invoice_number,
                narration=f"Appointment Invoice {invoice.invoice_number} - {invoice.patient_name}",
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
                description=f"Appointment Invoice - {invoice.patient_name}",
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
                description=f"Consultation Revenue - {invoice.invoice_number}",
                debit_base=0,
                credit_base=float(invoice.final_amount),
                created_by=username
            )
            session.add(credit_line)
            
            return voucher.id
        except Exception as e:
            logger.error(f"Error creating voucher: {str(e)}", self.logger_name)
            raise
    
    def _update_appointment_invoice_status(self, session, appointment_id, invoice_id, username):
        try:
            appointment = session.query(Appointment).filter(
                Appointment.id == appointment_id,
                Appointment.is_deleted == False
            ).first()
            
            if not appointment:
                raise ValueError(f"Appointment {appointment_id} not found")
            
            appointment.appointment_invoice_generated = True
            appointment.appointment_invoice_id = invoice_id
            appointment.updated_by = username
            appointment.updated_at = datetime.utcnow()
            
            logger.info(f"Appointment {appointment_id} updated with invoice {invoice_id}", self.logger_name)
        except Exception as e:
            logger.error(f"Error updating appointment status: {str(e)}", self.logger_name)
            raise
    
    def create(self, data):
        try:
            with db_manager.get_session() as session:
                items = data.pop('items', [])
                tenant_id = data['tenant_id']
                username = data.pop('created_by', 'system')
                appointment_id = data['appointment_id']
                
                # Validate appointment exists
                appointment = session.query(Appointment).filter(
                    Appointment.id == appointment_id,
                    Appointment.tenant_id == tenant_id,
                    Appointment.is_deleted == False
                ).first()
                
                if not appointment:
                    raise ValueError(f"Appointment {appointment_id} not found")
                
                if appointment.appointment_invoice_generated:
                    raise ValueError(f"Invoice already generated for appointment {appointment_id}")
                
                invoice = AppointmentInvoice(**data)
                session.add(invoice)
                session.flush()
                
                # Add items
                for item in items:
                    item['invoice_id'] = invoice.id
                    item['tenant_id'] = tenant_id
                    item['created_by'] = username
                    invoice_item = AppointmentInvoiceItem(**item)
                    session.add(invoice_item)
                
                # Create voucher if POSTED
                if invoice.status == 'POSTED':
                    voucher_id = self._create_voucher(session, invoice, tenant_id, username)
                    invoice.voucher_id = voucher_id
                
                # Update appointment in same transaction if status is not POSTED
                if invoice.status == 'POSTED':
                    self._update_appointment_invoice_status(session, appointment_id, invoice.id, username)
                
                session.flush()
                invoice_id = invoice.id
                logger.info(f"Appointment invoice created: {invoice.invoice_number}", self.logger_name)
                return invoice_id
        except ValueError as ve:
            logger.error(f"Validation error: {str(ve)}", self.logger_name)
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            logger.error(f"Error creating appointment invoice: {str(e)}", self.logger_name)
            raise
    
    def _map_invoice_to_dict(self, inv, include_items=False, include_appointment_details=False):
        appointment_data = None
        if inv.appointment:
            appointment_data = {
                "id": inv.appointment.id,
                "appointment_number": inv.appointment.appointment_number,
                "status": inv.appointment.status
            }
            if include_appointment_details:
                appointment_data.update({
                    "appointment_date": inv.appointment.appointment_date.isoformat() if inv.appointment.appointment_date else None,
                    "appointment_time": str(inv.appointment.appointment_time) if inv.appointment.appointment_time else None,
                    "reason": inv.appointment.reason
                })
        
        result = {
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "invoice_date": inv.invoice_date.isoformat() if inv.invoice_date else None,
            "patient_id": inv.patient_id,
            "patient_name": inv.patient_name,
            "patient_phone": inv.patient_phone,
            "doctor_id": inv.doctor_id,
            "doctor_name": inv.doctor_name,
            "final_amount": float(inv.final_amount),
            "paid_amount": float(inv.paid_amount or 0),
            "balance_amount": float(inv.balance_amount or 0),
            "payment_status": inv.payment_status,
            "status": inv.status,
            "appointment": appointment_data
        }
        
        if include_items and hasattr(inv, 'items'):
            result["items"] = [{
                "id": item.id,
                "line_no": item.line_no,
                "billing_master_id": item.billing_master_id,
                "description": item.description,
                "hsn_code": item.hsn_code,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
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
                invoice = session.query(AppointmentInvoice).options(
                    joinedload(AppointmentInvoice.appointment),
                    selectinload(AppointmentInvoice.items)
                ).filter(
                    AppointmentInvoice.id == invoice_id,
                    AppointmentInvoice.tenant_id == tenant_id,
                    AppointmentInvoice.is_deleted == False
                ).first()
                
                if not invoice:
                    return None
                
                result = self._map_invoice_to_dict(invoice, include_items=True, include_appointment_details=True)
                
                result.update({
                    "branch_id": invoice.branch_id,
                    "appointment_id": invoice.appointment_id,
                    "patient_email": invoice.patient_email,
                    "patient_address": invoice.patient_address,
                    "patient_dob": invoice.patient_dob.isoformat() if invoice.patient_dob else None,
                    "patient_gender": invoice.patient_gender,
                    "doctor_phone": invoice.doctor_phone,
                    "doctor_email": invoice.doctor_email,
                    "doctor_address": invoice.doctor_address,
                    "doctor_license_number": invoice.doctor_license_number,
                    "doctor_speciality": invoice.doctor_speciality,
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
                        # qr_data = f"/appointment-invoice?INVOICE={invoice.invoice_number}"
                        # result["qr_code"] = BarcodeGenerator.generate_qr_code(crypto)
                        print("=======",invoice.invoice_number)
                        qr_data = crypto_utils.generate_appointment_invoice_url(invoice.invoice_number)
                        result["qr_code"] = BarcodeGenerator.generate_qr_code(qr_data)
                        
                    except Exception as e:
                        logger.error(f"Barcode generation failed: {str(e)}", self.logger_name)
                        result["qr_code"] = None
                
                return result
        except Exception as e:
            logger.error(f"Error fetching appointment invoice {invoice_id}: {str(e)}", self.logger_name)
            raise
    
    def get_all(self, tenant_id, page=1, per_page=10, search=None, patient_id=None, doctor_id=None, 
                appointment_id=None, status=None, payment_status=None, include_items=False):
        try:
            with db_manager.get_session() as session:
                query = session.query(AppointmentInvoice).options(
                    joinedload(AppointmentInvoice.appointment)
                )
                
                if include_items:
                    query = query.options(selectinload(AppointmentInvoice.items))
                
                query = query.filter(
                    AppointmentInvoice.tenant_id == tenant_id,
                    AppointmentInvoice.is_deleted == False
                )
                
                if patient_id:
                    query = query.filter(AppointmentInvoice.patient_id == patient_id)
                
                if doctor_id:
                    query = query.filter(AppointmentInvoice.doctor_id == doctor_id)
                
                if appointment_id:
                    query = query.filter(AppointmentInvoice.appointment_id == appointment_id)
                
                if search:
                    query = query.filter(or_(
                        AppointmentInvoice.invoice_number.ilike(f"%{search}%"),
                        AppointmentInvoice.patient_name.ilike(f"%{search}%"),
                        AppointmentInvoice.doctor_name.ilike(f"%{search}%")
                    ))
                
                if status:
                    query = query.filter(
                        AppointmentInvoice.status.in_(status) if isinstance(status, list) 
                        else AppointmentInvoice.status == status
                    )
                
                if payment_status:
                    query = query.filter(
                        AppointmentInvoice.payment_status.in_(payment_status) if isinstance(payment_status, list)
                        else AppointmentInvoice.payment_status == payment_status
                    )
                
                total = query.count()
                results = query.order_by(AppointmentInvoice.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
                
                return {
                    "data": [self._map_invoice_to_dict(inv, include_items=include_items) for inv in results],
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": math.ceil(total / per_page)
                }
        except Exception as e:
            logger.error(f"Error listing appointment invoices: {str(e)}", self.logger_name)
            raise
    
    def update(self, invoice_id, data, tenant_id):
        try:
            with db_manager.get_session() as session:
                invoice = session.query(AppointmentInvoice).filter(
                    AppointmentInvoice.id == invoice_id,
                    AppointmentInvoice.tenant_id == tenant_id,
                    AppointmentInvoice.is_deleted == False
                ).first()
                
                if not invoice:
                    raise HTTPException(status_code=404, detail="Invoice not found")
                
                for key, value in data.items():
                    if key not in ['id', 'created_at', 'created_by', 'tenant_id', 'appointment_id']:
                        setattr(invoice, key, value)
                
                invoice.updated_at = datetime.utcnow()
                session.flush()
                logger.info(f"Appointment invoice updated: {invoice.invoice_number}", self.logger_name)
                return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating appointment invoice: {str(e)}", self.logger_name)
            raise
    
    def delete(self, invoice_id, tenant_id, deleted_by='system'):
        try:
            with db_manager.get_session() as session:
                invoice = session.query(AppointmentInvoice).filter(
                    AppointmentInvoice.id == invoice_id,
                    AppointmentInvoice.tenant_id == tenant_id,
                    AppointmentInvoice.is_deleted == False
                ).first()
                
                if not invoice:
                    raise HTTPException(status_code=404, detail="Invoice not found")
                
                invoice.is_deleted = True
                invoice.is_active = False
                invoice.updated_by = deleted_by
                invoice.updated_at = datetime.utcnow()
                session.flush()
                logger.info(f"Appointment invoice deleted: {invoice.invoice_number}", self.logger_name)
                return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting appointment invoice: {str(e)}", self.logger_name)
            raise
