"""
Migration 047: Add Audit Trail Table
"""
from sqlalchemy import text

def upgrade(session):
    """Add audit trail table for comprehensive tracking"""
    
    # Create audit_trail table
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS audit_trail (
            id SERIAL PRIMARY KEY,
            entity_type VARCHAR(50) NOT NULL,
            entity_id INTEGER NOT NULL,
            action VARCHAR(20) NOT NULL,
            old_value JSONB,
            new_value JSONB,
            user_id INTEGER REFERENCES users(id),
            username VARCHAR(100),
            ip_address VARCHAR(50),
            tenant_id INTEGER NOT NULL REFERENCES tenants(id),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            remarks TEXT
        )
    """))
    
    # Create indexes for performance
    session.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_audit_trail_tenant 
        ON audit_trail(tenant_id, created_at DESC)
    """))
    
    session.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_audit_trail_entity 
        ON audit_trail(entity_type, entity_id)
    """))
    
    session.commit()
    print("✅ Migration 047: Audit trail table created successfully")

def downgrade(session):
    """Remove audit trail table"""
    session.execute(text("DROP TABLE IF EXISTS audit_trail CASCADE"))
    session.commit()
    print("✅ Migration 047: Audit trail table removed")

if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    
    from core.database.connection import db_manager
    
    print("Running Migration 047: Audit Trail")
    with db_manager.get_session() as session:
        upgrade(session)
