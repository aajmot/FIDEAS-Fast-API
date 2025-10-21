#!/usr/bin/env python3
"""
Database Schema Setup Migration
Creates all required tables for FIDEAS application
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def create_schema():
    """Create all database tables and indexes"""
    print("Creating database schema...")
    
    try:
        # Create base tables first (from SQLAlchemy models)
        db_manager.create_tables()
        
        with db_manager.get_session() as session:
            # Additional tables SQL
            schema_sql = """
            -- Account Groups table
            CREATE TABLE IF NOT EXISTS account_groups (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                code VARCHAR(20) UNIQUE NOT NULL,
                parent_id INTEGER REFERENCES account_groups(id),
                account_type VARCHAR(20) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(100),
                is_deleted BOOLEAN DEFAULT FALSE
            );

            -- Account Master table
            CREATE TABLE IF NOT EXISTS account_masters (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                code VARCHAR(50) UNIQUE NOT NULL,
                account_group_id INTEGER NOT NULL REFERENCES account_groups(id),
                opening_balance DECIMAL(15,2) DEFAULT 0,
                current_balance DECIMAL(15,2) DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(100),
                is_deleted BOOLEAN DEFAULT FALSE
            );

            -- Voucher Types table
            CREATE TABLE IF NOT EXISTS voucher_types (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                code VARCHAR(10) UNIQUE NOT NULL,
                prefix VARCHAR(10),
                is_active BOOLEAN DEFAULT TRUE,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(100),
                is_deleted BOOLEAN DEFAULT FALSE
            );

            -- Vouchers table
            CREATE TABLE IF NOT EXISTS vouchers (
                id SERIAL PRIMARY KEY,
                voucher_number VARCHAR(50) UNIQUE NOT NULL,
                voucher_type_id INTEGER NOT NULL REFERENCES voucher_types(id),
                voucher_date TIMESTAMP NOT NULL,
                reference_type VARCHAR(20),
                reference_id INTEGER,
                reference_number VARCHAR(50),
                narration TEXT,
                total_amount DECIMAL(15,2) NOT NULL,
                is_posted BOOLEAN DEFAULT FALSE,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(100),
                is_deleted BOOLEAN DEFAULT FALSE
            );

            -- Journals table
            CREATE TABLE IF NOT EXISTS journals (
                id SERIAL PRIMARY KEY,
                voucher_id INTEGER NOT NULL REFERENCES vouchers(id),
                journal_date TIMESTAMP NOT NULL,
                total_debit DECIMAL(15,2) NOT NULL,
                total_credit DECIMAL(15,2) NOT NULL,
                is_balanced BOOLEAN DEFAULT TRUE,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(100),
                is_deleted BOOLEAN DEFAULT FALSE
            );

            -- Journal Details table
            CREATE TABLE IF NOT EXISTS journal_details (
                id SERIAL PRIMARY KEY,
                journal_id INTEGER NOT NULL REFERENCES journals(id),
                account_id INTEGER NOT NULL REFERENCES account_masters(id),
                debit_amount DECIMAL(15,2) DEFAULT 0,
                credit_amount DECIMAL(15,2) DEFAULT 0,
                narration TEXT,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(100),
                is_deleted BOOLEAN DEFAULT FALSE
            );

            -- Ledgers table
            CREATE TABLE IF NOT EXISTS ledgers (
                id SERIAL PRIMARY KEY,
                account_id INTEGER NOT NULL REFERENCES account_masters(id),
                voucher_id INTEGER NOT NULL REFERENCES vouchers(id),
                transaction_date TIMESTAMP NOT NULL,
                debit_amount DECIMAL(15,2) DEFAULT 0,
                credit_amount DECIMAL(15,2) DEFAULT 0,
                balance DECIMAL(15,2) DEFAULT 0,
                narration TEXT,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(100),
                is_deleted BOOLEAN DEFAULT FALSE
            );

            -- Payments table
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                payment_number VARCHAR(50) UNIQUE NOT NULL,
                payment_date TIMESTAMP NOT NULL,
                payment_type VARCHAR(20) NOT NULL,
                payment_mode VARCHAR(20) NOT NULL,
                reference_type VARCHAR(20) NOT NULL,
                reference_id INTEGER NOT NULL,
                reference_number VARCHAR(50) NOT NULL,
                amount DECIMAL(15,2) NOT NULL,
                account_id INTEGER REFERENCES account_masters(id),
                voucher_id INTEGER REFERENCES vouchers(id),
                remarks TEXT,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(100),
                is_deleted BOOLEAN DEFAULT FALSE
            );

            -- Patients table
            CREATE TABLE IF NOT EXISTS patients (
                id SERIAL PRIMARY KEY,
                patient_number VARCHAR(50) UNIQUE NOT NULL,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                date_of_birth DATE,
                gender VARCHAR(10),
                phone VARCHAR(20) NOT NULL,
                email VARCHAR(100),
                address TEXT,
                emergency_contact VARCHAR(100),
                emergency_phone VARCHAR(20),
                blood_group VARCHAR(5),
                allergies TEXT,
                medical_history TEXT,
                tenant_id INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100)
            );

            -- Doctors table
            CREATE TABLE IF NOT EXISTS doctors (
                id SERIAL PRIMARY KEY,
                employee_id VARCHAR(50) UNIQUE NOT NULL,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                specialization VARCHAR(100),
                license_number VARCHAR(50),
                phone VARCHAR(20) NOT NULL,
                email VARCHAR(100),
                schedule_start TIME,
                schedule_end TIME,
                consultation_fee DECIMAL(10,2),
                tenant_id INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Appointments table
            CREATE TABLE IF NOT EXISTS appointments (
                id SERIAL PRIMARY KEY,
                appointment_number VARCHAR(50) UNIQUE NOT NULL,
                patient_id INTEGER NOT NULL REFERENCES patients(id),
                doctor_id INTEGER NOT NULL REFERENCES doctors(id),
                appointment_date DATE NOT NULL,
                appointment_time TIME NOT NULL,
                duration_minutes INTEGER DEFAULT 30,
                status VARCHAR(20) DEFAULT 'scheduled',
                reason TEXT,
                notes TEXT,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100)
            );

            -- Medical Records table
            CREATE TABLE IF NOT EXISTS medical_records (
                id SERIAL PRIMARY KEY,
                record_number VARCHAR(50) UNIQUE NOT NULL,
                patient_id INTEGER NOT NULL REFERENCES patients(id),
                doctor_id INTEGER NOT NULL REFERENCES doctors(id),
                appointment_id INTEGER REFERENCES appointments(id),
                visit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                chief_complaint TEXT,
                diagnosis TEXT,
                treatment_plan TEXT,
                vital_signs TEXT,
                lab_results TEXT,
                notes TEXT,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Prescriptions table
            CREATE TABLE IF NOT EXISTS prescriptions (
                id SERIAL PRIMARY KEY,
                prescription_number VARCHAR(50) UNIQUE NOT NULL,
                patient_id INTEGER NOT NULL REFERENCES patients(id),
                doctor_id INTEGER NOT NULL REFERENCES doctors(id),
                prescription_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                instructions TEXT,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Prescription Items table
            CREATE TABLE IF NOT EXISTS prescription_items (
                id SERIAL PRIMARY KEY,
                prescription_id INTEGER NOT NULL REFERENCES prescriptions(id),
                product_id INTEGER REFERENCES products(id),
                dosage VARCHAR(100),
                frequency VARCHAR(100),
                duration VARCHAR(100),
                quantity DECIMAL(10,2),
                instructions TEXT
            );

            -- Fiscal Years table
            CREATE TABLE IF NOT EXISTS fiscal_years (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                is_active BOOLEAN DEFAULT FALSE,
                is_closed BOOLEAN DEFAULT FALSE,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(100),
                is_deleted BOOLEAN DEFAULT FALSE,
                UNIQUE(tenant_id, name)
            );

            -- Clinic Invoices table
            CREATE TABLE IF NOT EXISTS clinic_invoices (
                id SERIAL PRIMARY KEY,
                invoice_number VARCHAR(50) UNIQUE NOT NULL,
                patient_id INTEGER NOT NULL REFERENCES patients(id),
                invoice_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                consultation_fee DECIMAL(10,2) DEFAULT 0,
                medication_amount DECIMAL(10,2) DEFAULT 0,
                other_charges DECIMAL(10,2) DEFAULT 0,
                discount_amount DECIMAL(10,2) DEFAULT 0,
                total_amount DECIMAL(10,2) NOT NULL,
                payment_status VARCHAR(20) DEFAULT 'pending',
                payment_method VARCHAR(20),
                insurance_provider VARCHAR(100),
                insurance_claim_number VARCHAR(50),
                voucher_id INTEGER REFERENCES vouchers(id),
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100)
            );

            -- Clinic Invoice Items table
            CREATE TABLE IF NOT EXISTS clinic_invoice_items (
                id SERIAL PRIMARY KEY,
                invoice_id INTEGER NOT NULL REFERENCES clinic_invoices(id),
                item_type VARCHAR(20) NOT NULL,
                product_id INTEGER REFERENCES products(id),
                description VARCHAR(200) NOT NULL,
                quantity DECIMAL(10,2) DEFAULT 1,
                unit_price DECIMAL(10,2) NOT NULL,
                total_price DECIMAL(10,2) NOT NULL
            );

            -- Clinic Employees table
            CREATE TABLE IF NOT EXISTS clinic_employees (
                id SERIAL PRIMARY KEY,
                employee_number VARCHAR(50) UNIQUE NOT NULL,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                role VARCHAR(50) NOT NULL,
                department VARCHAR(100),
                phone VARCHAR(20) NOT NULL,
                email VARCHAR(100),
                hire_date DATE,
                salary DECIMAL(10,2),
                tenant_id INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100)
            );

            -- Stock Balances table
            CREATE TABLE IF NOT EXISTS stock_balances (
                id SERIAL PRIMARY KEY,
                product_id INTEGER NOT NULL REFERENCES products(id),
                batch_number VARCHAR(50),
                available_quantity DECIMAL(10,2) DEFAULT 0,
                reserved_quantity DECIMAL(10,2) DEFAULT 0,
                total_quantity DECIMAL(10,2) DEFAULT 0,
                average_cost DECIMAL(10,2) DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tenant_id INTEGER NOT NULL
            );

            -- Stock Transactions table
            CREATE TABLE IF NOT EXISTS stock_transactions (
                id SERIAL PRIMARY KEY,
                product_id INTEGER NOT NULL REFERENCES products(id),
                transaction_type VARCHAR(20) NOT NULL,
                transaction_source VARCHAR(20) NOT NULL,
                reference_id INTEGER NOT NULL,
                reference_number VARCHAR(50) NOT NULL,
                batch_number VARCHAR(50),
                quantity DECIMAL(10,2) NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tenant_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100)
            );

            -- Add reversal columns to existing tables
            ALTER TABLE sales_orders 
            ADD COLUMN IF NOT EXISTS reversal_reason TEXT,
            ADD COLUMN IF NOT EXISTS reversed_at TIMESTAMP,
            ADD COLUMN IF NOT EXISTS reversed_by VARCHAR(100);

            ALTER TABLE purchase_orders 
            ADD COLUMN IF NOT EXISTS reversal_reason TEXT,
            ADD COLUMN IF NOT EXISTS reversed_at TIMESTAMP,
            ADD COLUMN IF NOT EXISTS reversed_by VARCHAR(100);
            
            -- Update units table structure
            ALTER TABLE units 
            ADD COLUMN IF NOT EXISTS tenant_id INTEGER REFERENCES tenants(id),
            ADD COLUMN IF NOT EXISTS parent_id INTEGER REFERENCES units(id),
            ADD COLUMN IF NOT EXISTS conversion_factor DECIMAL(10,4) DEFAULT 1.0,
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS created_by VARCHAR(100),
            ADD COLUMN IF NOT EXISTS updated_by VARCHAR(100);
            
            -- Update existing units to have tenant_id = 1 (default tenant)
            UPDATE units SET tenant_id = 1 WHERE tenant_id IS NULL;
            
            -- Make tenant_id NOT NULL after setting default values
            ALTER TABLE units ALTER COLUMN tenant_id SET NOT NULL;
            
            -- Remove subunit_id from products if it exists
            ALTER TABLE products DROP COLUMN IF EXISTS subunit_id;
            
            -- Drop subunits table if it exists
            DROP TABLE IF EXISTS subunits CASCADE;
            """
            
            # Execute schema creation
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
            for stmt in statements:
                if stmt:
                    try:
                        session.execute(text(stmt))
                    except Exception as e:
                        print(f"[WARNING] Error executing statement: {e}")
                        continue
            
            session.commit()
            
        # Create indexes
        create_indexes()
        
        print("[OK] Database schema created successfully")
        
    except Exception as e:
        print(f"[ERROR] Error creating schema: {str(e)}")
        raise

def create_indexes():
    """Create database indexes for performance"""
    print("Creating database indexes...")
    
    try:
        with db_manager.get_session() as session:
            indexes = [
                # Core indexes
                "CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id);",
                "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
                "CREATE INDEX IF NOT EXISTS idx_roles_tenant_id ON roles(tenant_id);",
                "CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON user_roles(role_id);",
                
                # Inventory indexes
                "CREATE INDEX IF NOT EXISTS idx_categories_tenant_id ON categories(tenant_id);",
                "CREATE INDEX IF NOT EXISTS idx_products_tenant_id ON products(tenant_id);",
                "CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);",
                "CREATE INDEX IF NOT EXISTS idx_customers_tenant_id ON customers(tenant_id);",
                "CREATE INDEX IF NOT EXISTS idx_suppliers_tenant_id ON suppliers(tenant_id);",
                "CREATE INDEX IF NOT EXISTS idx_units_tenant_id ON units(tenant_id);",
                "CREATE INDEX IF NOT EXISTS idx_units_parent_id ON units(parent_id);",
                "CREATE INDEX IF NOT EXISTS idx_units_updated_at ON units(updated_at);",
                "CREATE INDEX IF NOT EXISTS idx_stock_transactions_product ON stock_transactions(product_id);",
                "CREATE INDEX IF NOT EXISTS idx_stock_transactions_tenant ON stock_transactions(tenant_id);",
                "CREATE INDEX IF NOT EXISTS idx_stock_balances_product ON stock_balances(product_id);",
                "CREATE INDEX IF NOT EXISTS idx_stock_balances_tenant ON stock_balances(tenant_id);",
                
                # Account indexes
                "CREATE INDEX IF NOT EXISTS idx_account_groups_tenant ON account_groups(tenant_id);",
                "CREATE INDEX IF NOT EXISTS idx_account_masters_tenant ON account_masters(tenant_id);",
                "CREATE INDEX IF NOT EXISTS idx_vouchers_tenant ON vouchers(tenant_id);",
                "CREATE INDEX IF NOT EXISTS idx_journals_tenant ON journals(tenant_id);",
                "CREATE INDEX IF NOT EXISTS idx_ledgers_tenant ON ledgers(tenant_id);",
                "CREATE INDEX IF NOT EXISTS idx_ledgers_account ON ledgers(account_id);",
                
                # Clinic indexes
                "CREATE INDEX IF NOT EXISTS idx_patients_tenant ON patients(tenant_id);",
                "CREATE INDEX IF NOT EXISTS idx_doctors_tenant ON doctors(tenant_id);",
                "CREATE INDEX IF NOT EXISTS idx_appointments_tenant ON appointments(tenant_id);",
                "CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);",
                "CREATE INDEX IF NOT EXISTS idx_medical_records_tenant ON medical_records(tenant_id);",
                "CREATE INDEX IF NOT EXISTS idx_medical_records_patient ON medical_records(patient_id);",
                "CREATE INDEX IF NOT EXISTS idx_prescriptions_tenant ON prescriptions(tenant_id);",
                "CREATE INDEX IF NOT EXISTS idx_prescriptions_patient ON prescriptions(patient_id);",
                "CREATE INDEX IF NOT EXISTS idx_clinic_invoices_tenant ON clinic_invoices(tenant_id);",
                "CREATE INDEX IF NOT EXISTS idx_clinic_invoices_patient ON clinic_invoices(patient_id);",
                "CREATE INDEX IF NOT EXISTS idx_clinic_employees_tenant ON clinic_employees(tenant_id);"
            ]
            
            for index_sql in indexes:
                try:
                    session.execute(text(index_sql))
                except Exception as e:
                    print(f"[WARNING] Error creating index: {e}")
                    continue
            
            session.commit()
            print("[OK] Database indexes created successfully")
            
    except Exception as e:
        print(f"[ERROR] Error creating indexes: {str(e)}")
        raise

if __name__ == "__main__":
    print("Running schema setup migration...")
    create_schema()
    print("Schema migration completed!")