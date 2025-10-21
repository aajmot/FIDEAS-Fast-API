from sqlalchemy import text
from core.database.connection import db_manager

def run_migration():
    with db_manager.get_session() as session:
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS product_batches (
                batch_id SERIAL PRIMARY KEY,
                product_id INTEGER,
                batch_no VARCHAR(50) NOT NULL,
                mfg_date DATE,
                exp_date DATE,
                quantity DECIMAL(15,3) DEFAULT 0,
                mrp DECIMAL(15,2),
                tenant_id INTEGER,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(product_id, batch_no, tenant_id)
            )
        """))
        
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS currencies (
                currency_id SERIAL PRIMARY KEY,
                currency_code VARCHAR(3) NOT NULL,
                currency_name VARCHAR(100),
                symbol VARCHAR(10),
                exchange_rate DECIMAL(15,6) DEFAULT 1.0,
                is_base BOOLEAN DEFAULT false,
                tenant_id INTEGER,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(currency_code, tenant_id)
            )
        """))
        
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS bank_statements (
                statement_id SERIAL PRIMARY KEY,
                account_id INTEGER,
                trans_date DATE NOT NULL,
                description TEXT,
                debit DECIMAL(15,2) DEFAULT 0,
                credit DECIMAL(15,2) DEFAULT 0,
                balance DECIMAL(15,2),
                is_reconciled BOOLEAN DEFAULT false,
                voucher_id INTEGER,
                reconciled_at TIMESTAMP,
                tenant_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS notification_logs (
                log_id SERIAL PRIMARY KEY,
                tenant_id INTEGER,
                notification_type VARCHAR(20),
                recipient VARCHAR(255),
                subject TEXT,
                status VARCHAR(20),
                error_message TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        session.commit()
        print("Essential features migration completed successfully")

if __name__ == "__main__":
    run_migration()
