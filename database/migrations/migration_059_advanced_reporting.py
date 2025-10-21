"""
Migration 059: Advanced Reporting & Scheduling
"""

from sqlalchemy import text
from core.database.connection import db_manager

def upgrade():
    with db_manager.get_session() as session:
        # Custom Reports
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS custom_reports (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                report_type VARCHAR(50) NOT NULL,
                query_template TEXT NOT NULL,
                parameters JSONB,
                is_public BOOLEAN DEFAULT FALSE,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100)
            )
        """))
        
        # Scheduled Reports
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS scheduled_reports (
                id SERIAL PRIMARY KEY,
                report_id INTEGER NOT NULL,
                schedule_type VARCHAR(20) NOT NULL,
                schedule_time TIME,
                schedule_day INTEGER,
                email_recipients TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                last_run TIMESTAMP,
                next_run TIMESTAMP,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Dashboard Widgets
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS dashboard_widgets (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                widget_type VARCHAR(50) NOT NULL,
                widget_config JSONB,
                position_x INTEGER DEFAULT 0,
                position_y INTEGER DEFAULT 0,
                width INTEGER DEFAULT 4,
                height INTEGER DEFAULT 3,
                is_visible BOOLEAN DEFAULT TRUE,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        session.commit()
        print("✓ Advanced reporting tables created")

def downgrade():
    with db_manager.get_session() as session:
        session.execute(text("DROP TABLE IF EXISTS dashboard_widgets CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS scheduled_reports CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS custom_reports CASCADE"))
        session.commit()

if __name__ == "__main__":
    upgrade()
