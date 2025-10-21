"""
Migration 056: Approval Workflows
"""

from sqlalchemy import text
from core.database.connection import db_manager

def upgrade():
    with db_manager.get_session() as session:
        # Approval Workflows
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS approval_workflows (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                entity_type VARCHAR(50) NOT NULL,
                min_amount DECIMAL(15,2) DEFAULT 0,
                max_amount DECIMAL(15,2),
                is_active BOOLEAN DEFAULT TRUE,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100)
            )
        """))
        
        # Approval Levels
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS approval_levels (
                id SERIAL PRIMARY KEY,
                workflow_id INTEGER NOT NULL,
                level_number INTEGER NOT NULL,
                approver_role_id INTEGER,
                approver_user_id INTEGER,
                is_mandatory BOOLEAN DEFAULT TRUE,
                tenant_id INTEGER NOT NULL,
                FOREIGN KEY (workflow_id) REFERENCES approval_workflows(id) ON DELETE CASCADE
            )
        """))
        
        # Approval Requests
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS approval_requests (
                id SERIAL PRIMARY KEY,
                workflow_id INTEGER NOT NULL,
                entity_type VARCHAR(50) NOT NULL,
                entity_id INTEGER NOT NULL,
                entity_number VARCHAR(50),
                amount DECIMAL(15,2),
                current_level INTEGER DEFAULT 1,
                status VARCHAR(20) DEFAULT 'PENDING',
                requested_by VARCHAR(100),
                requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                tenant_id INTEGER NOT NULL
            )
        """))
        
        # Approval History
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS approval_history (
                id SERIAL PRIMARY KEY,
                request_id INTEGER NOT NULL,
                level_number INTEGER NOT NULL,
                approver_id INTEGER NOT NULL,
                action VARCHAR(20) NOT NULL,
                comments TEXT,
                action_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tenant_id INTEGER NOT NULL,
                FOREIGN KEY (request_id) REFERENCES approval_requests(id) ON DELETE CASCADE
            )
        """))
        
        # Add approval fields to transactions
        session.execute(text("""
            ALTER TABLE purchase_orders
            ADD COLUMN IF NOT EXISTS approval_status VARCHAR(20) DEFAULT 'DRAFT',
            ADD COLUMN IF NOT EXISTS approval_request_id INTEGER
        """))
        
        session.execute(text("""
            ALTER TABLE vouchers
            ADD COLUMN IF NOT EXISTS approval_status VARCHAR(20) DEFAULT 'DRAFT',
            ADD COLUMN IF NOT EXISTS approval_request_id INTEGER
        """))
        
        session.commit()
        print("✓ Approval workflow tables created")

def downgrade():
    with db_manager.get_session() as session:
        session.execute(text("DROP TABLE IF EXISTS approval_history CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS approval_requests CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS approval_levels CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS approval_workflows CASCADE"))
        session.commit()

if __name__ == "__main__":
    upgrade()
