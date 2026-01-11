from sqlalchemy import or_
from core.database.connection import db_manager
from modules.health_module.models.clinic_entities import Patient, Prescription, PrescriptionItem, PrescriptionTestItem
from modules.health_module.services.appointment_service import AppointmentService
from modules.inventory_module.services.inventory_service import InventoryService
from core.shared.utils.logger import logger
from datetime import datetime
from sqlalchemy.orm import joinedload, selectinload

class PrescriptionService:
    def __init__(self):
        self.logger_name = "PrescriptionService"
        self.inventory_service = InventoryService()
    
    def create(self, prescription_data, items_data, test_items_data=None):
        try:
            with db_manager.get_session() as session:
                prescription_number = prescription_data.get('prescription_number')
                tenant_id = prescription_data.get('tenant_id')
                
                if not prescription_number:
                    raise ValueError("prescription_number is required")
                
                if not tenant_id:
                    raise ValueError("tenant_id is required")
                
                # Check if prescription number already exists for this tenant
                existing = session.query(Prescription).filter(
                    Prescription.prescription_number == prescription_number,
                    Prescription.tenant_id == tenant_id
                ).first()
                
                if existing:
                    raise ValueError(f"Prescription number {prescription_number} already exists")
                
                appointment_id = prescription_data.get('appointment_id')
                if not appointment_id:
                    raise ValueError("appointment_id is required")
                
                # Create prescription
                prescription = Prescription(**prescription_data)
                session.add(prescription)
                session.flush()
                prescription_id = prescription.id
                
                # Get tenant_id and branch_id from prescription
                tenant_id = prescription.tenant_id
                branch_id = prescription.branch_id
                
                # Create prescription items
                for item_data in items_data:
                    item_data['tenant_id'] = tenant_id
                    item_data['branch_id'] = branch_id
                    item_data['created_at'] = datetime.utcnow()
                    item_data['is_deleted'] = False
                    item = PrescriptionItem(
                        prescription_id=prescription_id,
                        **item_data
                    )
                    session.add(item)
                
                # Create prescription test items
                if test_items_data:
                    for test_item_data in test_items_data:
                        test_item_data['tenant_id'] = tenant_id
                        test_item_data['branch_id'] = branch_id
                        test_item_data['created_at'] = datetime.utcnow()
                        test_item_data['is_deleted'] = False
                        test_item = PrescriptionTestItem(
                            prescription_id=prescription_id,
                            **test_item_data
                        )
                        session.add(test_item)
                
                # Update appointment with prescription status in same transaction
                appointment_service = AppointmentService()
                created_by = prescription_data.get('created_by', 'system')
                appointment_service.update_prescription_status(appointment_id, prescription_id, created_by, session)
                
                logger.info(f"Prescription created: {prescription_number}", self.logger_name)
                return {'id': prescription_id, 'prescription_number': prescription_number}
        except Exception as e:
            logger.error(f"Error creating prescription: {str(e)}", self.logger_name)
            raise
    
    def dispense_prescription(self, prescription_id):
        """Dispense prescription and update inventory"""
        try:
            with db_manager.get_session() as session:
                prescription = session.query(Prescription).filter(Prescription.id == prescription_id).first()
                if not prescription:
                    raise ValueError("Prescription not found")
                
                # Check inventory and reserve items
                for item in prescription.prescription_items:
                    if item.quantity:
                        # Check if product is available in inventory
                        available = self.inventory_service.check_availability(item.product_id, item.quantity)
                        if not available:
                            raise ValueError(f"Insufficient stock for {item.product.name}")
                        
                        # Reserve inventory
                        self.inventory_service.reserve_stock(item.product_id, item.quantity)
                
                logger.info(f"Prescription dispensed: {prescription.prescription_number}", self.logger_name)
                return True
        except Exception as e:
            logger.error(f"Error dispensing prescription: {str(e)}", self.logger_name)
            raise
    
    def get_all(self, tenant_id=None, search=None, offset=0, limit=10):
        try:
            with db_manager.get_session() as session:
                # 1. Build Query with Eager Loading (Optimization)
                query = session.query(Prescription).options(
                    joinedload(Prescription.patient),
                    joinedload(Prescription.doctor),
                    joinedload(Prescription.appointment)
                )

                if tenant_id:
                    query = query.filter(Prescription.tenant_id == tenant_id)

                if search:
                    term = f"%{search}%"
                    query = query.filter(or_(
                        Prescription.prescription_number.ilike(term),
                        Patient.first_name.ilike(term),
                        Patient.last_name.ilike(term)
                    ))

                total = query.count()
                prescriptions = query.offset(offset).limit(limit).all()

                # 2. Manual serialization to dictionary
                prescription_data = []
                for prescription in prescriptions:
                    try:
                        data = {
                            "id": prescription.id,
                            "prescription_number": prescription.prescription_number,
                            "appointment_id": prescription.appointment.appointment_number if hasattr(prescription, 'appointment') and prescription.appointment else prescription.appointment_id,
                            "patient_id": prescription.patient_id,
                            "patient_name": f"{prescription.patient.first_name} {prescription.patient.last_name}" if hasattr(prescription, 'patient') and prescription.patient else f"Patient {prescription.patient_id}",
                            "doctor_id": prescription.doctor_id,
                            "doctor_name": f"{prescription.doctor.first_name} {prescription.doctor.last_name}" if hasattr(prescription, 'doctor') and prescription.doctor else f"Doctor {prescription.doctor_id}",
                            "prescription_date": prescription.prescription_date.isoformat() if prescription.prescription_date else None,
                            "instructions": prescription.instructions,
                            "created_at": prescription.created_at.isoformat() if prescription.created_at else None
                        }
                        prescription_data.append(data)
                    except Exception:
                        continue
                
                return {'prescriptions': prescription_data, 'total': total}
        except Exception as e:
            logger.error(f"Error in get_all: {str(e)}")
            raise

    def get_by_id(self, tenant_id=None, prescription_id=None):
        """Get prescription by ID with items and test items"""
        try:
            with db_manager.get_session() as session:
                from modules.health_module.models.clinic_entities import Doctor, Appointment
                from modules.inventory_module.models.product_entity import Product
                from modules.health_module.models.care_entities import Test
                
                query = session.query(Prescription).outerjoin(Patient).outerjoin(Doctor)
                if tenant_id:
                    query = query.filter(Prescription.tenant_id == tenant_id)
                
                prescription = query.filter(
                    Prescription.id == prescription_id,
                    Prescription.is_deleted == False
                ).first()
                
                if not prescription:
                    return None
                
                # Get prescription items
                items = session.query(PrescriptionItem, Product).join(
                    Product, PrescriptionItem.product_id == Product.id
                ).filter(
                    PrescriptionItem.prescription_id == prescription_id,
                    PrescriptionItem.is_deleted == False
                ).all()
                
                items_data = []
                for item, product in items:
                    items_data.append({
                        "id": item.id,
                        "product_id": item.product_id,
                        "product_name": product.name if product else f"Product {item.product_id}",
                        "dosage": item.dosage,
                        "frequency": item.frequency,
                        "duration": item.duration,
                        "quantity": float(item.quantity) if item.quantity else None,
                        "instructions": item.instructions
                    })
                
                # Get prescription test items
                test_items = session.query(PrescriptionTestItem, Test).join(
                    Test, PrescriptionTestItem.test_id == Test.id
                ).filter(
                    PrescriptionTestItem.prescription_id == prescription_id,
                    PrescriptionTestItem.is_deleted == False
                ).all()
                
                test_items_data = []
                for test_item, test in test_items:
                    test_items_data.append({
                        "id": test_item.id,
                        "test_id": test_item.test_id,
                        "test_name": test.name if test else test_item.test_name,
                        "instructions": test_item.instructions
                    })
                
                # Calculate patient age
                patient_age = None
                if hasattr(prescription, 'patient') and prescription.patient and prescription.patient.date_of_birth:
                    from datetime import date
                    today = date.today()
                    dob = prescription.patient.date_of_birth
                    patient_age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                
                # Get appointment number
                appointment_number = None
                if prescription.appointment_id:
                    appointment = session.query(Appointment).filter(Appointment.id == prescription.appointment_id).first()
                    if appointment:
                        appointment_number = appointment.appointment_number
                
                result = {
                    "id": prescription.id,
                    "prescription_number": prescription.prescription_number,
                    "appointment_id": prescription.appointment_id,
                    "appointment_number": appointment_number,
                    "patient_id": prescription.patient_id,
                    "patient_name": f"{prescription.patient.first_name} {prescription.patient.last_name}" if hasattr(prescription, 'patient') and prescription.patient else f"Patient {prescription.patient_id}",
                    "patient_phone": prescription.patient.phone if hasattr(prescription, 'patient') and prescription.patient else None,
                    "patient_age": patient_age,
                    "doctor_id": prescription.doctor_id,
                    "doctor_name": f"{prescription.doctor.first_name} {prescription.doctor.last_name}" if hasattr(prescription, 'doctor') and prescription.doctor else f"Doctor {prescription.doctor_id}",
                    "doctor_license_number": prescription.doctor.license_number if hasattr(prescription, 'doctor') and prescription.doctor else None,
                    "prescription_date": prescription.prescription_date.isoformat() if prescription.prescription_date else None,
                    "instructions": prescription.instructions,
                    "items": items_data,
                    "test_items": test_items_data,
                    "created_at": prescription.created_at.isoformat() if prescription.created_at else None
                }
                return result
        except Exception as e:
            logger.error(f"Error fetching prescription: {str(e)}", self.logger_name)
            raise

    def update(self, prescription_id, prescription_data, items_data=None, test_items_data=None):
        try:
            with db_manager.get_session() as session:
                prescription = session.query(Prescription).filter(Prescription.id == prescription_id).first()
                if not prescription:
                    return None
                
                # Update prescription fields
                for key, value in prescription_data.items():
                    if hasattr(prescription, key):
                        setattr(prescription, key, value)
                
                session.flush()
                
                # Get tenant_id and branch_id from prescription
                tenant_id = prescription.tenant_id
                branch_id = prescription.branch_id
                prescription_number = prescription.prescription_number
                
                # Update prescription items if provided
                if items_data is not None:
                    # Mark existing items as deleted
                    session.query(PrescriptionItem).filter(PrescriptionItem.prescription_id == prescription_id).update({'is_deleted': True, 'updated_at': datetime.utcnow()})
                    session.flush()
                    
                    # Add new items
                    for item_data in items_data:
                        item_data.pop('id', None)
                        item_data['tenant_id'] = tenant_id
                        item_data['branch_id'] = branch_id
                        item_data['created_at'] = datetime.utcnow()
                        item_data['is_deleted'] = False
                        item = PrescriptionItem(
                            prescription_id=prescription.id,
                            **item_data
                        )
                        session.add(item)
                
                # Update prescription test items if provided
                if test_items_data is not None:
                    # Mark existing test items as deleted
                    session.query(PrescriptionTestItem).filter(PrescriptionTestItem.prescription_id == prescription_id).update({'is_deleted': True, 'updated_at': datetime.utcnow()})
                    session.flush()
                    
                    # Add new test items
                    for test_item_data in test_items_data:
                        test_item_data.pop('id', None)
                        test_item_data['tenant_id'] = tenant_id
                        test_item_data['branch_id'] = branch_id
                        test_item_data['created_at'] = datetime.utcnow()
                        test_item_data['is_deleted'] = False
                        test_item = PrescriptionTestItem(
                            prescription_id=prescription.id,
                            **test_item_data
                        )
                        session.add(test_item)
                
                session.flush()
                logger.info(f"Prescription updated: {prescription_number}", self.logger_name)
                return {'id': prescription_id, 'prescription_number': prescription_number}
        except Exception as e:
            logger.error(f"Error updating prescription: {str(e)}", self.logger_name)
            return None
    
    def delete(self, prescription_id, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(Prescription).filter(Prescription.id == prescription_id)
                if tenant_id:
                    query = query.filter(Prescription.tenant_id == tenant_id)
                prescription = query.first()
                if not prescription:
                    logger.warning(f"Prescription not found: id={prescription_id}, tenant_id={tenant_id}", self.logger_name)
                    return False
                
                # Delete prescription items first
                session.query(PrescriptionItem).filter(PrescriptionItem.prescription_id == prescription_id).delete()
                session.query(PrescriptionTestItem).filter(PrescriptionTestItem.prescription_id == prescription_id).delete()
                session.flush()
                
                # Delete prescription
                session.delete(prescription)
                
                logger.info(f"Prescription deleted: {prescription.prescription_number}", self.logger_name)
                return True
        except Exception as e:
            logger.error(f"Error deleting prescription: {str(e)}", self.logger_name)
            raise