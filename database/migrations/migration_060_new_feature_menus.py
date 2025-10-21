"""
Migration 060: Menu entries for Priority 1 & 2 features
"""

from sqlalchemy import text
from core.database.connection import db_manager

def upgrade():
    with db_manager.get_session() as session:
        # Check if menu_master table exists
        result = session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'menu_master'
            )
        """))
        
        if not result.scalar():
            print("⚠ menu_master table does not exist. Run base migrations first.")
            return
        
        # Invoice Management Menus
        session.execute(text("""
            INSERT INTO menu_master (menu_name, menu_code, module_code, icon, route, sort_order, is_active)
            VALUES 
            ('Sales Invoice', 'SALES_INVOICE', 'INVENTORY', '📄', '/inventory/sales-invoice', 51, TRUE),
            ('Purchase Invoice', 'PURCHASE_INVOICE', 'INVENTORY', '📋', '/inventory/purchase-invoice', 52, TRUE),
            ('Payment Terms', 'PAYMENT_TERMS', 'ADMIN', '📅', '/admin/payment-terms', 41, TRUE)
            ON CONFLICT (menu_code) DO NOTHING
        """))
        
        # Multi-Warehouse Menus
        session.execute(text("""
            INSERT INTO menu_master (menu_name, menu_code, module_code, icon, route, sort_order, is_active)
            VALUES 
            ('Warehouses', 'WAREHOUSES', 'INVENTORY', '🏭', '/inventory/warehouses', 53, TRUE),
            ('Stock Transfer', 'STOCK_TRANSFER', 'INVENTORY', '🔄', '/inventory/stock-transfer', 54, TRUE),
            ('Stock by Location', 'STOCK_BY_LOCATION', 'INVENTORY', '📍', '/inventory/stock-by-location', 55, TRUE)
            ON CONFLICT (menu_code) DO NOTHING
        """))
        
        # Fixed Assets Menus
        session.execute(text("""
            INSERT INTO menu_master (menu_name, menu_code, module_code, icon, route, sort_order, is_active)
            VALUES 
            ('Fixed Assets', 'FIXED_ASSETS', 'ACCOUNT', '🏢', '/account/fixed-assets', 41, TRUE),
            ('Asset Categories', 'ASSET_CATEGORIES', 'ACCOUNT', '📂', '/account/asset-categories', 42, TRUE),
            ('Depreciation', 'DEPRECIATION', 'ACCOUNT', '📉', '/account/depreciation', 43, TRUE)
            ON CONFLICT (menu_code) DO NOTHING
        """))
        
        # Approval Workflow Menus
        session.execute(text("""
            INSERT INTO menu_master (menu_name, menu_code, module_code, icon, route, sort_order, is_active)
            VALUES 
            ('Approval Workflows', 'APPROVAL_WORKFLOWS', 'ADMIN', '✅', '/admin/approval-workflows', 42, TRUE),
            ('Pending Approvals', 'PENDING_APPROVALS', 'ADMIN', '⏳', '/admin/pending-approvals', 43, TRUE)
            ON CONFLICT (menu_code) DO NOTHING
        """))
        
        # GST Compliance Menus
        session.execute(text("""
            INSERT INTO menu_master (menu_name, menu_code, module_code, icon, route, sort_order, is_active)
            VALUES 
            ('E-Invoice', 'EINVOICE', 'ACCOUNT', '🔐', '/account/einvoice', 44, TRUE),
            ('E-Way Bill', 'EWAY_BILL', 'ACCOUNT', '🚚', '/account/eway-bill', 45, TRUE),
            ('GSTR-1', 'GSTR1', 'ACCOUNT', '📊', '/account/gstr1', 46, TRUE),
            ('TDS Returns', 'TDS_RETURNS', 'ACCOUNT', '💰', '/account/tds-returns', 47, TRUE)
            ON CONFLICT (menu_code) DO NOTHING
        """))
        
        # Document Management Menus
        session.execute(text("""
            INSERT INTO menu_master (menu_name, menu_code, module_code, icon, route, sort_order, is_active)
            VALUES 
            ('Document Templates', 'DOC_TEMPLATES', 'ADMIN', '📝', '/admin/document-templates', 44, TRUE)
            ON CONFLICT (menu_code) DO NOTHING
        """))
        
        # Advanced Reporting Menus
        session.execute(text("""
            INSERT INTO menu_master (menu_name, menu_code, module_code, icon, route, sort_order, is_active)
            VALUES 
            ('Custom Reports', 'CUSTOM_REPORTS', 'ACCOUNT', '📈', '/account/custom-reports', 48, TRUE),
            ('Scheduled Reports', 'SCHEDULED_REPORTS', 'ACCOUNT', '⏰', '/account/scheduled-reports', 49, TRUE)
            ON CONFLICT (menu_code) DO NOTHING
        """))
        
        session.commit()
        print("✓ New feature menus created")

def downgrade():
    with db_manager.get_session() as session:
        session.execute(text("""
            DELETE FROM menu_master WHERE menu_code IN (
                'SALES_INVOICE', 'PURCHASE_INVOICE', 'PAYMENT_TERMS',
                'WAREHOUSES', 'STOCK_TRANSFER', 'STOCK_BY_LOCATION',
                'FIXED_ASSETS', 'ASSET_CATEGORIES', 'DEPRECIATION',
                'APPROVAL_WORKFLOWS', 'PENDING_APPROVALS',
                'EINVOICE', 'EWAY_BILL', 'GSTR1', 'TDS_RETURNS',
                'DOC_TEMPLATES', 'CUSTOM_REPORTS', 'SCHEDULED_REPORTS'
            )
        """))
        session.commit()

if __name__ == "__main__":
    upgrade()
