from core.database.connection import db_manager
from modules.health_module.models.clinic_entities import Appointment, Patient, Doctor
from modules.health_module.services.patient_service import PatientService
from modules.health_module.services.doctor_service import DoctorService
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
                tenant_id = appointment_data.get('tenant_id')
                if not tenant_id:
                    raise ValueError("tenant_id is required")
                
                if 'appointment_number' not in appointment_data or not appointment_data['appointment_number']:
                    appointment_data['appointment_number'] = self.generate_appointment_number(tenant_id)
                
                # Populate denormalized fields from related entities
                patient_id = appointment_data.get('patient_id')
                if patient_id and not appointment_data.get('patient_name'):
                    patient = session.query(Patient).filter(Patient.id == patient_id).first()
                    if patient:
                        appointment_data['patient_name'] = f"{patient.first_name} {patient.last_name}"
                        appointment_data['patient_phone'] = patient.phone
                
                doctor_id = appointment_data.get('doctor_id')
                if doctor_id and not appointment_data.get('doctor_name'):
                    doctor = session.query(Doctor).filter(Doctor.id == doctor_id).first()
                    if doctor:
                        appointment_data['doctor_name'] = f"{doctor.first_name} {doctor.last_name}"
                        appointment_data['doctor_phone'] = doctor.phone
                        appointment_data['doctor_license_number'] = doctor.license_number
                        appointment_data['doctor_specialization'] = doctor.specialization
                
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
    
    def get_all(self, tenant_id=None, search=None, offset=0, limit=10, 
                medical_record_generated=None, 
                prescription_generated=None, 
                appointment_invoice_generated=None, 
                test_order_generated=None):
        try:
            with db_manager.get_session() as session:
                # 1. Base query: always exclude deleted records
                query = session.query(Appointment).filter(Appointment.tenant_id==tenant_id,Appointment.is_deleted == False)
                
                # # 2. Tenant filtering
                # if tenant_id is not None:
                #     query = query.filter(Appointment.tenant_id == tenant_id)
                
                # 3. Boolean Flag Filtering
                # We use "is not None" so that False values are treated as valid filters
                filters = {
                    "medical_record_generated": medical_record_generated,
                    "prescription_generated": prescription_generated,
                    "appointment_invoice_generated": appointment_invoice_generated,
                    "test_order_generated": test_order_generated
                }

                for field, value in filters.items():
                    if value is not None:
                        # Dynamically apply the filter based on the field name
                        query = query.filter(getattr(Appointment, field) == value)

                # 4. Global Search Filter
                if search:
                    from sqlalchemy import or_
                    query = query.filter(or_(
                        Appointment.appointment_number.ilike(f"%{search}%"),
                        Appointment.patient_name.ilike(f"%{search}%"),
                        Appointment.doctor_name.ilike(f"%{search}%"),
                        Appointment.status.ilike(f"%{search}%")
                    ))
                
                # 5. Sorting and Pagination
                query = query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())
                
                total = query.count()
                appointments = query.offset(offset).limit(limit).all()
                
                return {'appointments': appointments, 'total': total}
                
        except Exception as e:
            logger.error(f"Error fetching appointments: {str(e)}", self.logger_name)
            raise
        
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
    
    def get_by_id(self, appointment_id=None, appointment_number=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(Appointment).filter(Appointment.is_deleted == False)
                
                if appointment_id:
                    query = query.filter(Appointment.id == appointment_id)
                elif appointment_number:
                    query = query.filter(Appointment.appointment_number == appointment_number)
                else:
                    return None
                
                return query.first()
        except Exception as e:
            logger.error(f"Error fetching appointment: {str(e)}", self.logger_name)
            raise
    
    def update(self, appointment_id, update_data, updated_by='system'):
        try:
            with db_manager.get_session() as session:
                appointment = session.query(Appointment).filter(
                    Appointment.id == appointment_id,
                    Appointment.is_deleted == False
                ).first()
                
                if not appointment:
                    return None
                
                # Auto-populate denormalized fields if IDs changed
                if 'patient_id' in update_data and update_data['patient_id']:
                    patient = session.query(Patient).filter(Patient.id == update_data['patient_id']).first()
                    if patient:
                        update_data['patient_name'] = f"{patient.first_name} {patient.last_name}"
                        update_data['patient_phone'] = patient.phone
                
                if 'doctor_id' in update_data and update_data['doctor_id']:
                    doctor = session.query(Doctor).filter(Doctor.id == update_data['doctor_id']).first()
                    if doctor:
                        update_data['doctor_name'] = f"{doctor.first_name} {doctor.last_name}"
                        update_data['doctor_phone'] = doctor.phone
                        update_data['doctor_license_number'] = doctor.license_number
                        update_data['doctor_specialization'] = doctor.specialization
                
                update_data['updated_by'] = updated_by
                update_data['updated_at'] = datetime.utcnow()
                
                for key, value in update_data.items():
                    setattr(appointment, key, value)
                
                session.flush()
                logger.info(f"Appointment updated: {appointment.appointment_number}", self.logger_name)
                return appointment
        except Exception as e:
            logger.error(f"Error updating appointment: {str(e)}", self.logger_name)
            raise
    
    def delete(self, appointment_id, deleted_by='system'):
        try:
            with db_manager.get_session() as session:
                appointment = session.query(Appointment).filter(
                    Appointment.id == appointment_id,
                    Appointment.is_deleted == False
                ).first()
                
                if not appointment:
                    return False
                
                appointment.is_deleted = True
                appointment.is_active = False
                appointment.updated_by = deleted_by
                appointment.updated_at = datetime.utcnow()
                session.flush()
                logger.info(f"Appointment deleted: {appointment.appointment_number}", self.logger_name)
                return True
        except Exception as e:
            logger.error(f"Error deleting appointment: {str(e)}", self.logger_name)
            raise
    
    def update_medical_record_status(self, appointment_id: int, medical_record_id: int, updated_by: str = 'system', session=None) -> bool:
        """Update appointment with medical record generation status"""
        try:
            if session:
                # Use provided session (same transaction)
                appointment = session.query(Appointment).filter(
                    Appointment.id == appointment_id,
                    Appointment.is_deleted == False
                ).first()
                
                if not appointment:
                    raise ValueError(f"Appointment {appointment_id} not found")
                
                appointment.medical_record_generated = True
                appointment.medical_record_id = medical_record_id
                appointment.updated_by = updated_by
                appointment.updated_at = datetime.utcnow()
                # No flush needed - will commit with parent transaction
                logger.info(f"Appointment {appointment.appointment_number} updated with medical record {medical_record_id}", self.logger_name)
                return True
            else:
                # Create new session
                with db_manager.get_session() as new_session:
                    appointment = new_session.query(Appointment).filter(
                        Appointment.id == appointment_id,
                        Appointment.is_deleted == False
                    ).first()
                    
                    if not appointment:
                        raise ValueError(f"Appointment {appointment_id} not found")
                    
                    appointment.medical_record_generated = True
                    appointment.medical_record_id = medical_record_id
                    appointment.updated_by = updated_by
                    appointment.updated_at = datetime.utcnow()
                    # Commit happens automatically via context manager
                    logger.info(f"Appointment {appointment.appointment_number} updated with medical record {medical_record_id}", self.logger_name)
                    return True
        except Exception as e:
            logger.error(f"Error updating appointment medical record status: {str(e)}", self.logger_name)
            raise
    
    def update_prescription_status(self, appointment_id: int, prescription_id: int, updated_by: str = 'system', session=None) -> bool:
        """Update appointment with prescription generation status"""
        try:
            if session:
                appointment = session.query(Appointment).filter(
                    Appointment.id == appointment_id,
                    Appointment.is_deleted == False
                ).first()
                
                if not appointment:
                    raise ValueError(f"Appointment {appointment_id} not found")
                
                appointment.prescription_generated = True
                appointment.prescription_id = prescription_id
                appointment.updated_by = updated_by
                appointment.updated_at = datetime.utcnow()
                logger.info(f"Appointment {appointment.appointment_number} updated with prescription {prescription_id}", self.logger_name)
                return True
            else:
                with db_manager.get_session() as new_session:
                    appointment = new_session.query(Appointment).filter(
                        Appointment.id == appointment_id,
                        Appointment.is_deleted == False
                    ).first()
                    
                    if not appointment:
                        raise ValueError(f"Appointment {appointment_id} not found")
                    
                    appointment.prescription_generated = True
                    appointment.prescription_id = prescription_id
                    appointment.updated_by = updated_by
                    appointment.updated_at = datetime.utcnow()
                    logger.info(f"Appointment {appointment.appointment_number} updated with prescription {prescription_id}", self.logger_name)
                    return True
        except Exception as e:
            logger.error(f"Error updating appointment prescription status: {str(e)}", self.logger_name)
            raise
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