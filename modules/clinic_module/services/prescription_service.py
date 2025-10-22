from core.database.connection import db_manager
from modules.clinic_module.models.entities import Prescription, PrescriptionItem, PrescriptionTestItem
from modules.inventory_module.services.inventory_service import InventoryService
from core.shared.utils.logger import logger
from datetime import datetime

class PrescriptionService:
    def __init__(self):
        self.logger_name = "PrescriptionService"
        self.inventory_service = InventoryService()
    
    def create(self, prescription_data, items_data, test_items_data=None):
        try:
            with db_manager.get_session() as session:
                # Use prescription_number from UI data if provided, otherwise generate one
                if 'prescription_number' not in prescription_data or not prescription_data['prescription_number']:
                    today = datetime.now().strftime("%Y%m%d")
                    last_prescription = session.query(Prescription).filter(
                        Prescription.prescription_number.like(f"RX{today}%")
                    ).order_by(Prescription.id.desc()).first()
                    
                    if last_prescription:
                        seq = int(last_prescription.prescription_number[-3:]) + 1
                    else:
                        seq = 1
                    
                    prescription_data['prescription_number'] = f"RX{today}{seq:03d}"
                
                # Create prescription
                prescription = Prescription(**prescription_data)
                session.add(prescription)
                session.flush()
                
                # Create prescription items
                for item_data in items_data:
                    item_data['created_at'] = datetime.utcnow()
                    item_data['is_deleted'] = False
                    item = PrescriptionItem(
                        prescription_id=prescription.id,
                        **item_data
                    )
                    session.add(item)
                
                # Create prescription test items
                if test_items_data:
                    for test_item_data in test_items_data:
                        test_item_data['created_at'] = datetime.utcnow()
                        test_item_data['is_deleted'] = False
                        test_item = PrescriptionTestItem(
                            prescription_id=prescription.id,
                            **test_item_data
                        )
                        session.add(test_item)
                
                prescription_id = prescription.id
                logger.info(f"Prescription created: {prescription.prescription_number}", self.logger_name)
                session.expunge(prescription)
                prescription.id = prescription_id
                return prescription
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
    
    def get_all(self, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(Prescription)
                if tenant_id:
                    query = query.filter(Prescription.tenant_id == tenant_id)
                prescriptions = query.all()
                for prescription in prescriptions:
                    session.expunge(prescription)
                return prescriptions
        except Exception as e:
            logger.error(f"Error fetching prescriptions: {str(e)}", self.logger_name)
            return []
    
    def get_by_patient(self, patient_id):
        try:
            with db_manager.get_session() as session:
                prescriptions = session.query(Prescription).filter(Prescription.patient_id == patient_id).all()
                for prescription in prescriptions:
                    session.expunge(prescription)
                return prescriptions
        except Exception as e:
            logger.error(f"Error fetching prescriptions: {str(e)}", self.logger_name)
            return []
    
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
                
                # Update prescription items if provided
                if items_data is not None:
                    # Mark existing items as deleted
                    session.query(PrescriptionItem).filter(PrescriptionItem.prescription_id == prescription_id).update({'is_deleted': True, 'updated_at': datetime.utcnow()})
                    session.flush()
                    
                    # Add new items
                    for item_data in items_data:
                        item_data.pop('id', None)
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
                        test_item_data['created_at'] = datetime.utcnow()
                        test_item_data['is_deleted'] = False
                        test_item = PrescriptionTestItem(
                            prescription_id=prescription.id,
                            **test_item_data
                        )
                        session.add(test_item)
                
                session.flush()
                prescription_id_result = prescription.id
                logger.info(f"Prescription updated: {prescription.prescription_number}", self.logger_name)
                session.expunge(prescription)
                prescription.id = prescription_id_result
                return prescription
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