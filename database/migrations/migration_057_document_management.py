"""
Migration 057: Document Management
"""

from sqlalchemy import text
from core.database.connection import db_manager

def upgrade():
    with db_manager.get_session() as session:
        # Document Attachments
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS document_attachments (
                id SERIAL PRIMARY KEY,
                entity_type VARCHAR(50) NOT NULL,
                entity_id INTEGER NOT NULL,
                file_name VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                file_size INTEGER,
                file_type VARCHAR(50),
                version INTEGER DEFAULT 1,
                is_active BOOLEAN DEFAULT TRUE,
                uploaded_by VARCHAR(100),
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tenant_id INTEGER NOT NULL
            )
        """))
        
        # Document Templates
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS document_templates (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                template_type VARCHAR(50) NOT NULL,
                template_content TEXT NOT NULL,
                is_default BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100)
            )
        """))
        
        session.commit()
        print("✓ Document management tables created")

def downgrade():
    with db_manager.get_session() as session:
        session.execute(text("DROP TABLE IF EXISTS document_templates CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS document_attachments CASCADE"))
        session.commit()

if __name__ == "__main__":
    upgrade()
