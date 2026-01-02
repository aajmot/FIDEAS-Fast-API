from core.database.connection import db_manager
from modules.clinic_module.models.entities import Patient, Doctor, Appointment, Invoice
from core.shared.utils.logger import logger
from datetime import datetime, date
from sqlalchemy import func, and_

class ReportService:
    def __init__(self):
        self.logger_name = "ReportService"
    
    def get_dashboard_stats(self, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                stats = {}
                
                # Patient count
                patient_query = session.query(func.count(Patient.id))
                if tenant_id:
                    patient_query = patient_query.filter(Patient.tenant_id == tenant_id)
                stats['total_patients'] = patient_query.filter(Patient.is_active == True).scalar() or 0
                
                # Doctor count
                doctor_query = session.query(func.count(Doctor.id))
                if tenant_id:
                    doctor_query = doctor_query.filter(Doctor.tenant_id == tenant_id)
                stats['total_doctors'] = doctor_query.filter(Doctor.is_active == True).scalar() or 0
                
                # Today's appointments
                today = date.today()
                appointment_query = session.query(func.count(Appointment.id)).filter(Appointment.appointment_date == today)
                if tenant_id:
                    appointment_query = appointment_query.filter(Appointment.tenant_id == tenant_id)
                stats['todays_appointments'] = appointment_query.scalar() or 0
                
                # Pending invoices
                invoice_query = session.query(func.count(Invoice.id)).filter(Invoice.payment_status == 'pending')
                if tenant_id:
                    invoice_query = invoice_query.filter(Invoice.tenant_id == tenant_id)
                stats['pending_invoices'] = invoice_query.scalar() or 0
                
                # Monthly revenue
                current_month = datetime.now().replace(day=1)
                revenue_query = session.query(func.sum(Invoice.total_amount)).filter(
                    and_(Invoice.invoice_date >= current_month, Invoice.payment_status == 'paid')
                )
                if tenant_id:
                    revenue_query = revenue_query.filter(Invoice.tenant_id == tenant_id)
                stats['monthly_revenue'] = float(revenue_query.scalar() or 0)
                
                return stats
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {str(e)}", self.logger_name)
            return {}
    
    def get_appointment_report(self, start_date, end_date, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(Appointment).filter(
                    and_(Appointment.appointment_date >= start_date, Appointment.appointment_date <= end_date)
                )
                if tenant_id:
                    query = query.filter(Appointment.tenant_id == tenant_id)
                
                appointments = query.all()
                for appointment in appointments:
                    session.expunge(appointment)
                return appointments
        except Exception as e:
            logger.error(f"Error getting appointment report: {str(e)}", self.logger_name)
            return []
    
    def get_revenue_report(self, start_date, end_date, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(Invoice).filter(
                    and_(Invoice.invoice_date >= start_date, Invoice.invoice_date <= end_date)
                )
                if tenant_id:
                    query = query.filter(Invoice.tenant_id == tenant_id)
                
                invoices = query.all()
                for invoice in invoices:
                    session.expunge(invoice)
                return invoices
        except Exception as e:
            logger.error(f"Error getting revenue report: {str(e)}", self.logger_name)
            return []