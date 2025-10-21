#!/usr/bin/env python3
"""
Add accounts and default posting rules for debit and credit notes
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def add_accounts_and_rules():
    """Add necessary accounts and posting rules"""
    print("Adding accounts and posting rules for debit/credit notes...")
    
    try:
        with db_manager.get_session() as session:
            # Get account group IDs
            revenue_group = session.execute(text(
                "SELECT id FROM account_groups WHERE code = 'REV' AND tenant_id = 1"
            )).scalar()
            
            expense_group = session.execute(text(
                "SELECT id FROM account_groups WHERE code = 'EXP' AND tenant_id = 1"
            )).scalar()
            
            # Add Sales Return account if not exists
            sales_return = session.execute(text("""
                SELECT id FROM account_masters 
                WHERE code = 'SR001' AND tenant_id = 1
            """)).scalar()
            
            if not sales_return:
                session.execute(text("""
                    INSERT INTO account_masters 
                    (name, code, account_group_id, opening_balance, current_balance, 
                     is_active, tenant_id, created_by)
                    VALUES 
                    ('Sales Return', 'SR001', :group_id, 0, 0, TRUE, 1, 'system')
                """), {"group_id": revenue_group})
                sales_return = session.execute(text(
                    "SELECT id FROM account_masters WHERE code = 'SR001' AND tenant_id = 1"
                )).scalar()
                print("Added Sales Return account")
            
            # Add Purchase Return account if not exists
            purchase_return = session.execute(text("""
                SELECT id FROM account_masters 
                WHERE code = 'PR001' AND tenant_id = 1
            """)).scalar()
            
            if not purchase_return:
                session.execute(text("""
                    INSERT INTO account_masters 
                    (name, code, account_group_id, opening_balance, current_balance, 
                     is_active, tenant_id, created_by)
                    VALUES 
                    ('Purchase Return', 'PR001', :group_id, 0, 0, TRUE, 1, 'system')
                """), {"group_id": expense_group})
                purchase_return = session.execute(text(
                    "SELECT id FROM account_masters WHERE code = 'PR001' AND tenant_id = 1"
                )).scalar()
                print("Added Purchase Return account")
            
            # Get AR and AP account IDs
            ar_account = session.execute(text(
                "SELECT id FROM account_masters WHERE code = 'AR001' AND tenant_id = 1"
            )).scalar()
            
            ap_account = session.execute(text(
                "SELECT id FROM account_masters WHERE code = 'AP001' AND tenant_id = 1"
            )).scalar()
            
            # Get template IDs
            credit_note_template = session.execute(text(
                "SELECT id FROM transaction_templates WHERE code = 'CREDIT_NOTE'"
            )).scalar()
            
            debit_note_template = session.execute(text(
                "SELECT id FROM transaction_templates WHERE code = 'DEBIT_NOTE'"
            )).scalar()
            
            # Add Credit Note posting rules
            if credit_note_template:
                # Check if rules already exist
                existing_rules = session.execute(text("""
                    SELECT COUNT(*) FROM transaction_template_rules 
                    WHERE template_id = :template_id
                """), {"template_id": credit_note_template}).scalar()
                
                if existing_rules == 0:
                    # Rule 1: Debit Sales Return
                    session.execute(text("""
                        INSERT INTO transaction_template_rules
                        (template_id, line_number, account_type, account_id, entry_type, 
                         amount_source, narration, tenant_id)
                        VALUES
                        (:template_id, 1, 'SALES_RETURN', :account_id, 'DEBIT', 
                         'TOTAL_AMOUNT', 'Sales return as per credit note', 1)
                    """), {"template_id": credit_note_template, "account_id": sales_return})
                    
                    # Rule 2: Credit Accounts Receivable
                    session.execute(text("""
                        INSERT INTO transaction_template_rules
                        (template_id, line_number, account_type, account_id, entry_type, 
                         amount_source, narration, tenant_id)
                        VALUES
                        (:template_id, 2, 'ACCOUNTS_RECEIVABLE', :account_id, 'CREDIT', 
                         'TOTAL_AMOUNT', 'Customer account credited', 1)
                    """), {"template_id": credit_note_template, "account_id": ar_account})
                    
                    print("Added Credit Note posting rules")
            
            # Add Debit Note posting rules
            if debit_note_template:
                # Check if rules already exist
                existing_rules = session.execute(text("""
                    SELECT COUNT(*) FROM transaction_template_rules 
                    WHERE template_id = :template_id
                """), {"template_id": debit_note_template}).scalar()
                
                if existing_rules == 0:
                    # Rule 1: Debit Accounts Payable
                    session.execute(text("""
                        INSERT INTO transaction_template_rules
                        (template_id, line_number, account_type, account_id, entry_type, 
                         amount_source, narration, tenant_id)
                        VALUES
                        (:template_id, 1, 'ACCOUNTS_PAYABLE', :account_id, 'DEBIT', 
                         'TOTAL_AMOUNT', 'Supplier account debited', 1)
                    """), {"template_id": debit_note_template, "account_id": ap_account})
                    
                    # Rule 2: Credit Purchase Return
                    session.execute(text("""
                        INSERT INTO transaction_template_rules
                        (template_id, line_number, account_type, account_id, entry_type, 
                         amount_source, narration, tenant_id)
                        VALUES
                        (:template_id, 2, 'PURCHASE_RETURN', :account_id, 'CREDIT', 
                         'TOTAL_AMOUNT', 'Purchase return as per debit note', 1)
                    """), {"template_id": debit_note_template, "account_id": purchase_return})
                    
                    print("Added Debit Note posting rules")
            
            # Add account type mappings
            mappings = [
                ('SALES_RETURN', sales_return),
                ('PURCHASE_RETURN', purchase_return)
            ]
            
            for account_type, account_id in mappings:
                existing = session.execute(text("""
                    SELECT id FROM account_type_mappings 
                    WHERE account_type = :account_type AND tenant_id = 1
                """), {"account_type": account_type}).scalar()
                
                if not existing:
                    session.execute(text("""
                        INSERT INTO account_type_mappings
                        (account_type, account_id, tenant_id, created_by)
                        VALUES (:account_type, :account_id, 1, 'system')
                    """), {"account_type": account_type, "account_id": account_id})
                    print(f"Added account type mapping: {account_type}")
            
            session.commit()
            print("[OK] Accounts and posting rules added successfully")
            
    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
        raise

if __name__ == "__main__":
    print("Running migration: Add debit/credit note accounts and rules...")
    add_accounts_and_rules()
    print("Migration completed!")
