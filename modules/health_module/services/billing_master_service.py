from core.shared.services.base_service import BaseService
from modules.health_module.models.clinic_entities import ClinicBillingMaster
from core.database.connection import db_manager
import csv
import io
from datetime import datetime

class BillingMasterService(BaseService):
    def __init__(self):
        super().__init__(ClinicBillingMaster)
    
    def create(self, data):
        with db_manager.get_session() as session:
            billing_master = ClinicBillingMaster(**data)
            session.add(billing_master)
            session.commit()
            session.refresh(billing_master)
            # Return a dict instead of the detached instance
            return {
                'id': billing_master.id,
                'description': billing_master.description,
                'note': billing_master.note,
                'amount': billing_master.amount,
                'hsn_code': billing_master.hsn_code,
                'gst_percentage': billing_master.gst_percentage,
                'tenant_id': billing_master.tenant_id,
                'is_active': billing_master.is_active,
                'is_deleted': billing_master.is_deleted,
                'created_at': billing_master.created_at,
                'updated_at': billing_master.updated_at
            }
    
    def update(self, billing_master_id, data):
        with db_manager.get_session() as session:
            billing_master = session.query(ClinicBillingMaster).filter(
                ClinicBillingMaster.id == billing_master_id,
                ClinicBillingMaster.is_deleted == False
            ).first()
            
            if billing_master:
                for key, value in data.items():
                    if hasattr(billing_master, key):
                        setattr(billing_master, key, value)
                billing_master.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(billing_master)
                # Return a dict instead of the detached instance
                return {
                    'id': billing_master.id,
                    'description': billing_master.description,
                    'note': billing_master.note,
                    'amount': billing_master.amount,
                    'hsn_code': billing_master.hsn_code,
                    'gst_percentage': billing_master.gst_percentage,
                    'tenant_id': billing_master.tenant_id,
                    'is_active': billing_master.is_active,
                    'is_deleted': billing_master.is_deleted,
                    'created_at': billing_master.created_at,
                    'updated_at': billing_master.updated_at
                }
            return None
    
    def delete(self, billing_master_id):
        with db_manager.get_session() as session:
            billing_master = session.query(ClinicBillingMaster).filter(
                ClinicBillingMaster.id == billing_master_id,
                ClinicBillingMaster.is_deleted == False
            ).first()
            
            if billing_master:
                billing_master.is_deleted = True
                billing_master.is_active = False
                billing_master.updated_at = datetime.utcnow()
                session.commit()
                return True
            return False
    
    def export_template(self):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["description", "note", "amount", "hsn_code", "gst_percentage"])
        writer.writerow(["Consultation Fee", "Standard consultation", "500.00", "9904", "18.00"])
        writer.writerow(["Lab Test", "Blood test", "200.00", "9018", "5.00"])
        output.seek(0)
        return output.getvalue()
    
    def import_billing_masters(self, csv_content, tenant_id):
        csv_data = csv.DictReader(io.StringIO(csv_content))
        imported_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_data, start=2):
            try:
                billing_master_data = {
                    "description": row["description"].strip(),
                    "note": row.get("note", "").strip(),
                    "amount": float(row["amount"]),
                    "hsn_code": row.get("hsn_code", "").strip(),
                    "gst_percentage": float(row.get("gst_percentage", 0)),
                    "tenant_id": tenant_id,
                    "is_active": True,
                    "is_deleted": False
                }
                
                self.create(billing_master_data)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                continue
        
        return {
            "imported": imported_count,
            "errors": errors
        }