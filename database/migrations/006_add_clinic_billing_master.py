"""
Migration: Add clinic_billing_master table
Created: 2024-01-01
"""

from core.database.connection import db_manager
import logging

logger = logging.getLogger(__name__)

def upgrade():
    """Add clinic_billing_master table"""
    try:
        with db_manager.get_session() as session:
            # Create clinic_billing_master table
            session.execute("""
                CREATE TABLE IF NOT EXISTS clinic_billing_master (
                    id SERIAL PRIMARY KEY,
                    description TEXT NOT NULL,
                    note TEXT,
                    amount NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
                    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_by CHARACTER VARYING(100),
                    updated_by CHARACTER VARYING(100)
                );
            """)
            
            # Create indexes
            session.execute("""
                CREATE INDEX IF NOT EXISTS idx_clinic_billing_master_tenant_id 
                ON clinic_billing_master(tenant_id);
            """)
            
            session.execute("""
                CREATE INDEX IF NOT EXISTS idx_clinic_billing_master_active_deleted 
                ON clinic_billing_master(is_active, is_deleted);
            """)
            
            session.commit()
            logger.info("Successfully created clinic_billing_master table")
            
    except Exception as e:
        logger.error(f"Error creating clinic_billing_master table: {e}")
        raise

def downgrade():
    """Remove clinic_billing_master table"""
    try:
        with db_manager.get_session() as session:
            session.execute("DROP TABLE IF EXISTS clinic_billing_master CASCADE;")
            session.commit()
            logger.info("Successfully dropped clinic_billing_master table")
            
    except Exception as e:
        logger.error(f"Error dropping clinic_billing_master table: {e}")
        raise

if __name__ == "__main__":
    upgrade()