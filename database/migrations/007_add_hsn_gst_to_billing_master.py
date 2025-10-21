"""
Migration: Add HSN code and GST percentage to clinic_billing_master table
Created: 2024-01-01
"""

from core.database.connection import db_manager
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def upgrade():
    """Add HSN code and GST percentage fields to clinic_billing_master table"""
    try:
        with db_manager.get_session() as session:
            # Add HSN code column (optional)
            session.execute(text("""
                ALTER TABLE clinic_billing_master 
                ADD COLUMN IF NOT EXISTS hsn_code VARCHAR(20);
            """))
            
            # Add GST percentage column (mandatory)
            session.execute(text("""
                ALTER TABLE clinic_billing_master 
                ADD COLUMN IF NOT EXISTS gst_percentage NUMERIC(5,2) NOT NULL DEFAULT 0.00 
                CHECK (gst_percentage >= 0 AND gst_percentage <= 100);
            """))
            
            # Create index for HSN code
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_clinic_billing_master_hsn_code 
                ON clinic_billing_master(hsn_code);
            """))
            
            session.commit()
            logger.info("Successfully added HSN code and GST percentage to clinic_billing_master table")
            
    except Exception as e:
        logger.error(f"Error adding HSN code and GST percentage to clinic_billing_master table: {e}")
        raise

def downgrade():
    """Remove HSN code and GST percentage fields from clinic_billing_master table"""
    try:
        with db_manager.get_session() as session:
            # Drop index
            session.execute(text("DROP INDEX IF EXISTS idx_clinic_billing_master_hsn_code;"))
            
            # Drop columns
            session.execute(text("ALTER TABLE clinic_billing_master DROP COLUMN IF EXISTS hsn_code;"))
            session.execute(text("ALTER TABLE clinic_billing_master DROP COLUMN IF EXISTS gst_percentage;"))
            
            session.commit()
            logger.info("Successfully removed HSN code and GST percentage from clinic_billing_master table")
            
    except Exception as e:
        logger.error(f"Error removing HSN code and GST percentage from clinic_billing_master table: {e}")
        raise

if __name__ == "__main__":
    upgrade()