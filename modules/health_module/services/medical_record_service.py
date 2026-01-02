from core.database.connection import db_manager
from modules.health_module.models.clinic_entities import MedicalRecord, Patient, Doctor
from modules.health_module.services.patient_service import PatientService
from modules.health_module.services.doctor_service import DoctorService
from core.shared.utils.logger import logger
from datetime import datetime
import csv
import io

class MedicalRecordService:
    def __init__(self):
        self.logger_name = "MedicalRecordService"
    
    def create(self, record_data):
        try:
            with db_manager.get_session() as session:
                # Generate record number in format MR-[tenantid]ddmmyyyyhhmmssfff
                now = datetime.now()
                timestamp = now.strftime("%d%m%Y%H%M%S") + f"{now.microsecond//1000:03d}"
                tenant_id = record_data.get('tenant_id')
                if not tenant_id:
                    raise ValueError("tenant_id is required")
                record_number = f"MR-{tenant_id}{timestamp}"
                
                # Remove id and record_number from record_data if present to avoid conflicts
                record_data_clean = {k: v for k, v in record_data.items() if k not in ['id', 'record_number']}
                
                record = MedicalRecord(
                    record_number=record_number,
                    **record_data_clean
                )
                session.add(record)
                session.flush()
                record_id = record.id  # Access id while session is active
                logger.info(f"Medical record created: {record.record_number}", self.logger_name)
                session.expunge(record)  # Detach from session
                record.id = record_id  # Set id on detached object
                return record
        except Exception as e:
            logger.error(f"Error creating medical record: {str(e)}", self.logger_name)
            raise
    
    def get_all(self, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(MedicalRecord)
                if tenant_id:
                    query = query.filter(MedicalRecord.tenant_id == tenant_id)
                records = query.all()
                for record in records:
                    session.expunge(record)
                return records
        except Exception as e:
            logger.error(f"Error fetching medical records: {str(e)}", self.logger_name)
            return []
    
    def get_by_patient(self, patient_id):
        try:
            with db_manager.get_session() as session:
                records = session.query(MedicalRecord).filter(MedicalRecord.patient_id == patient_id).all()
                for record in records:
                    session.expunge(record)
                return records
        except Exception as e:
            logger.error(f"Error fetching patient records: {str(e)}", self.logger_name)
            return []
    
    def update(self, record_id, record_data):
        try:
            with db_manager.get_session() as session:
                record = session.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
                if not record:
                    return None
                
                # Update record fields
                for key, value in record_data.items():
                    if hasattr(record, key) and key != 'id':
                        setattr(record, key, value)
                
                session.flush()
                record_id_result = record.id
                logger.info(f"Medical record updated: {record.record_number}", self.logger_name)
                session.expunge(record)
                record.id = record_id_result
                return record
        except Exception as e:
            logger.error(f"Error updating medical record: {str(e)}", self.logger_name)
            raise
    
    def delete(self, record_id):
        try:
            with db_manager.get_session() as session:
                record = session.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
                if not record:
                    return False
                
                session.delete(record)
                logger.info(f"Medical record deleted: {record.record_number}", self.logger_name)
                return True
        except Exception as e:
            logger.error(f"Error deleting medical record: {str(e)}", self.logger_name)
            return False
    
    def import_medical_records(self, csv_content, tenant_id):
        """Import medical records from CSV content"""
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
                        
                        # Find or create appointment
                        from modules.health_module.models.clinic_entities import Appointment
                        from modules.health_module.services.appointment_service import AppointmentService
                        
                        visit_date = datetime.strptime(row['Visit Date'], '%Y-%m-%d').date()
                        appointment = session.query(Appointment).filter(
                            Appointment.patient_id == patient.id,
                            Appointment.doctor_id == doctor.id,
                            Appointment.appointment_date == visit_date,
                            Appointment.tenant_id == tenant_id
                        ).first()
                        
                        if not appointment:
                            appointment_service = AppointmentService()
                            appointment_data = {
                                'patient_id': patient.id,
                                'doctor_id': doctor.id,
                                'appointment_date': visit_date,
                                'appointment_time': '09:00',
                                'status': 'Completed',
                                'tenant_id': tenant_id
                            }
                            appointment = appointment_service.create(appointment_data)
                        
                        # Create vital signs JSON
                        vital_signs = {
                            'bp': row.get('BP', ''),
                            'temp': row.get('Temperature', ''),
                            'pulse': row.get('Pulse', ''),
                            'weight': row.get('Weight', '')
                        }
                        
                        record_data = {
                            'patient_id': patient.id,
                            'doctor_id': doctor.id,
                            'appointment_id': appointment.id,
                            'visit_date': row['Visit Date'],
                            'chief_complaint': row.get('Chief Complaint', ''),
                            'diagnosis': row.get('Diagnosis', ''),
                            'treatment_plan': row.get('Treatment Plan', ''),
                            'vital_signs': str(vital_signs).replace("'", '"'),
                            'lab_results': row.get('Lab Results', ''),
                            'notes': row.get('Notes', ''),
                            'tenant_id': tenant_id
                        }
                        
                        # Generate record number
                        now = datetime.now()
                        timestamp = now.strftime("%d%m%Y%H%M%S") + f"{now.microsecond//1000:03d}"
                        record_number = f"MR-{tenant_id}{timestamp}"
                        
                        record = MedicalRecord(
                            record_number=record_number,
                            **record_data
                        )
                        session.add(record)
                        imported_count += 1
                        
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
                
                session.flush()
                logger.info(f"Imported {imported_count} medical records", self.logger_name)
                
            return {'imported': imported_count, 'errors': errors}
            
        except Exception as e:
            logger.error(f"Error importing medical records: {str(e)}", self.logger_name)
            raise