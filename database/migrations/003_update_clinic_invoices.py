"""
Update clinic invoices table structure
- Add appointment_id field
- Add discount_percentage field  
- Add final_amount field
- Remove medication_amount field
- Remove other_charges field
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def upgrade():
    """Apply the migration"""
    with db_manager.get_session() as session:
        try:
            # Add new columns
            session.execute(text("ALTER TABLE clinic_invoices ADD COLUMN appointment_id INTEGER"))
            session.execute(text("ALTER TABLE clinic_invoices ADD COLUMN discount_percentage DECIMAL(5,2) DEFAULT 0"))
            session.execute(text("ALTER TABLE clinic_invoices ADD COLUMN final_amount DECIMAL(10,2) DEFAULT 0"))
            
            # Update final_amount with current total_amount values
            session.execute(text("UPDATE clinic_invoices SET final_amount = total_amount WHERE final_amount = 0"))
            
            # Add foreign key constraint for appointment_id
            session.execute(text("ALTER TABLE clinic_invoices ADD CONSTRAINT fk_clinic_invoices_appointment_id FOREIGN KEY (appointment_id) REFERENCES appointments(id)"))
            
            # Drop old columns if they exist
            try:
                session.execute(text("ALTER TABLE clinic_invoices DROP COLUMN medication_amount"))
            except:
                pass  # Column might not exist
                
            try:
                session.execute(text("ALTER TABLE clinic_invoices DROP COLUMN other_charges"))
            except:
                pass  # Column might not exist
            
            session.commit()
            print("✓ Clinic invoices table updated successfully")
            
        except Exception as e:
            session.rollback()
            print(f"✗ Error updating clinic invoices table: {str(e)}")
            raise

def downgrade():
    """Reverse the migration"""
    with db_manager.get_session() as session:
        try:
            # Add back old columns
            session.execute(text("ALTER TABLE clinic_invoices ADD COLUMN medication_amount DECIMAL(10,2) DEFAULT 0"))
            session.execute(text("ALTER TABLE clinic_invoices ADD COLUMN other_charges DECIMAL(10,2) DEFAULT 0"))
            
            # Drop new columns
            session.execute(text("ALTER TABLE clinic_invoices DROP CONSTRAINT fk_clinic_invoices_appointment_id"))
            session.execute(text("ALTER TABLE clinic_invoices DROP COLUMN appointment_id"))
            session.execute(text("ALTER TABLE clinic_invoices DROP COLUMN discount_percentage"))
            session.execute(text("ALTER TABLE clinic_invoices DROP COLUMN final_amount"))
            
            session.commit()
            print("✓ Clinic invoices table downgrade completed")
            
        except Exception as e:
            session.rollback()
            print(f"✗ Error downgrading clinic invoices table: {str(e)}")
            raise

if __name__ == "__main__":
    upgrade()