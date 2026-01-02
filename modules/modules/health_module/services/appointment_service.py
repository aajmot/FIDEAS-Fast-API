from core.database.connection import db_manager
from modules.clinic_module.models.entities import Appointment, Patient, Doctor
from modules.clinic_module.services.patient_service import PatientService
from modules.clinic_module.services.doctor_service import DoctorService
from core.shared.utils.logger import logger
from datetime import datetime, date
import csv
import io

class AppointmentService:
    def __init__(self):
        self.logger_name = "AppointmentService"
    
    def generate_appointment_number(self, tenant_id):
        """Generate appointment number in format APT-[tenantid]ddmmyyyyhhmmssfff"""
        now = datetime.now()
        timestamp = now.strftime("%d%m%Y%H%M%S") + f"{now.microsecond//1000:03d}"
        return f"APT-{tenant_id}{timestamp}"
    
    def create(self, appointment_data):
        try:
            with db_manager.get_session() as session:
                # Use appointment_number from UI if provided, otherwise generate
                tenant_id = appointment_data.get('tenant_id')
                if not tenant_id:
                    raise ValueError("tenant_id is required")
                if 'appointment_number' not in appointment_data or not appointment_data['appointment_number']:
                    appointment_data['appointment_number'] = self.generate_appointment_number(tenant_id)
                
                appointment = Appointment(**appointment_data)
                session.add(appointment)
                session.flush()
                appointment_id = appointment.id
                logger.info(f"Appointment created: {appointment.appointment_number}", self.logger_name)
                session.expunge(appointment)
                appointment.id = appointment_id
                return appointment
        except Exception as e:
            logger.error(f"Error creating appointment: {str(e)}", self.logger_name)
            raise
    
    def get_all(self, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(Appointment).join(Patient).join(Doctor)
                if tenant_id:
                    query = query.filter(Appointment.tenant_id == tenant_id)
                appointments = query.all()
                # Detach from session to avoid lazy loading issues
                for appointment in appointments:
                    session.expunge(appointment)
                return appointments
        except Exception as e:
            logger.error(f"Error fetching appointments: {str(e)}", self.logger_name)
            return []
    
    def get_by_date(self, appointment_date, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(Appointment).join(Patient).join(Doctor)
                query = query.filter(Appointment.appointment_date == appointment_date)
                if tenant_id:
                    query = query.filter(Appointment.tenant_id == tenant_id)
                appointments = query.all()
                for appointment in appointments:
                    session.expunge(appointment)
                return appointments
        except Exception as e:
            logger.error(f"Error fetching appointments by date: {str(e)}", self.logger_name)
            return []
    
    def update_status(self, appointment_id, status):
        try:
            with db_manager.get_session() as session:
                appointment = session.query(Appointment).filter(Appointment.id == appointment_id).first()
                if appointment:
                    appointment.status = status
                    session.flush()
                    appointment_id_val = appointment.id  # Access id while session is active
                    logger.info(f"Appointment status updated: {appointment.appointment_number} -> {status}", self.logger_name)
                    session.expunge(appointment)  # Detach from session
                    appointment.id = appointment_id_val  # Set id on detached object
                    return appointment
        except Exception as e:
            logger.error(f"Error updating appointment status: {str(e)}", self.logger_name)
            raise
    
    def export_template(self):
        """Generate CSV template for appointment import"""
        template_data = [
            ['Patient Name', 'Patient Phone', 'Doctor Name', 'Doctor Phone', 'Appointment Date', 'Appointment Time', 'Duration Minutes', 'Status', 'Reason', 'Notes'],
            ['John Doe', '123-456-7890', 'Dr. Jane Smith', '987-654-3210', '2024-01-15', '09:00', '30', 'scheduled', 'Regular checkup', 'Patient follow-up']
        ]
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(template_data)
        return output.getvalue()
    
    def import_appointments(self, csv_content, tenant_id):
        """Import appointments from CSV content"""
        try:
            imported_count = 0
            errors = []
            
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            with db_manager.get_session() as session:
                for row_num, row in enumerate(csv_reader, start=2):
                    try:
                        # Find or create patient
                        patient_name = row['Patient Name'].strip()
                        patient_phone = row['Patient Phone'].strip()
                        patient = session.query(Patient).filter(
                            Patient.phone == patient_phone,
                            Patient.tenant_id == tenant_id
                        ).first()
                        
                        if not patient:
                            name_parts = patient_name.split(' ', 1)
                            patient_service = PatientService()
                            patient_data = {
                                'first_name': name_parts[0],
                                'last_name': name_parts[1] if len(name_parts) > 1 else '',
                                'phone': patient_phone,
                                'tenant_id': tenant_id
                            }
                            patient = patient_service.create(patient_data)
                        
                        # Find or create doctor
                        doctor_name = row['Doctor Name'].strip()
                        doctor_phone = row['Doctor Phone'].strip()
                        doctor = session.query(Doctor).filter(
                            Doctor.phone == doctor_phone,
                            Doctor.tenant_id == tenant_id
                        ).first()
                        
                        if not doctor:
                            name_parts = doctor_name.replace('Dr. ', '').split(' ', 1)
                            doctor_service = DoctorService()
                            doctor_data = {
                                'first_name': name_parts[0],
                                'last_name': name_parts[1] if len(name_parts) > 1 else '',
                                'phone': doctor_phone,
                                'tenant_id': tenant_id
                            }
                            doctor = doctor_service.create(doctor_data)
                        
                        appointment_data = {
                            'patient_id': patient.id,
                            'doctor_id': doctor.id,
                            'appointment_date': row['Appointment Date'],
                            'appointment_time': row['Appointment Time'],
                            'duration_minutes': int(row.get('Duration Minutes', 30)),
                            'status': row.get('Status', 'scheduled'),
                            'reason': row.get('Reason', ''),
                            'notes': row.get('Notes', ''),
                            'tenant_id': tenant_id
                        }
                        
                        appointment_number = self.generate_appointment_number(tenant_id)
                        appointment = Appointment(
                            appointment_number=appointment_number,
                            **appointment_data
                        )
                        session.add(appointment)
                        imported_count += 1
                        
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
                
                session.flush()
                logger.info(f"Imported {imported_count} appointments", self.logger_name)
                
            return {'imported': imported_count, 'errors': errors}
            
        except Exception as e:
            logger.error(f"Error importing appointments: {str(e)}", self.logger_name)
            raise