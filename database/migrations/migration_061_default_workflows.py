"""
Migration 061: Insert Default Approval Workflows
Creates default multi-level approval workflows for common entities
"""

from sqlalchemy import text
from core.database.connection import db_manager

def upgrade():
    """Insert default approval workflows"""
    
    with db_manager.get_session() as session:
        # Get all tenants
        result = session.execute(text("SELECT id FROM tenants"))
        tenants = result.fetchall()
        if not tenants:
            print("No tenants found. Skipping default workflow creation.")
            return
        
        for tenant_row in tenants:
            tenant_id = tenant_row[0]
            print(f"\nCreating workflows for tenant_id: {tenant_id}")
            
            # Default workflows to create
            workflows = [
            {
                'name': 'Purchase Order Approval',
                'entity': 'purchase_order',
                'levels': [
                    {'level': 1, 'type': 'role', 'role': 'Purchase Manager'},
                    {'level': 2, 'type': 'role', 'role': 'Finance Manager'},
                    {'level': 3, 'type': 'role', 'role': 'Admin'}
                ]
            },
            {
                'name': 'Stock Transfer Approval',
                'entity': 'stock_transfer',
                'levels': [
                    {'level': 1, 'type': 'role', 'role': 'Warehouse Manager'},
                    {'level': 2, 'type': 'role', 'role': 'Inventory Manager'}
                ]
            },
            {
                'name': 'Voucher Approval (>50000)',
                'entity': 'voucher',
                'levels': [
                    {'level': 1, 'type': 'role', 'role': 'Accountant'},
                    {'level': 2, 'type': 'role', 'role': 'Finance Manager'},
                    {'level': 3, 'type': 'role', 'role': 'Admin'}
                ]
            },
            {
                'name': 'Sales Invoice Approval',
                'entity': 'sales_invoice',
                'levels': [
                    {'level': 1, 'type': 'role', 'role': 'Sales Manager'},
                    {'level': 2, 'type': 'role', 'role': 'Finance Manager'}
                ]
            }
        ]
        
        for wf in workflows:
            # Check if workflow already exists
            check = session.execute(
                text("SELECT id FROM approval_workflows WHERE name = :name AND tenant_id = :tid"),
                {'name': wf['name'], 'tid': tenant_id}
            ).fetchone()
            
            if check:
                print(f"Workflow '{wf['name']}' already exists. Skipping.")
                continue
            
            # Insert workflow
            result = session.execute(
                text("""
                    INSERT INTO approval_workflows 
                    (tenant_id, name, entity_type, is_active, created_at)
                    VALUES (:tid, :name, :entity, true, NOW())
                    RETURNING id
                """),
                {'tid': tenant_id, 'name': wf['name'], 'entity': wf['entity']}
            )
            workflow_id = result.fetchone()[0]
            
            # Insert approval levels
            for level in wf['levels']:
                # Get role_id
                role_result = session.execute(
                    text("SELECT id FROM roles WHERE name = :role AND tenant_id = :tid"),
                    {'role': level['role'], 'tid': tenant_id}
                ).fetchone()
                
                role_id = role_result[0] if role_result else None
                
                session.execute(
                    text("""
                        INSERT INTO approval_levels
                        (workflow_id, level_number, approver_role_id, tenant_id)
                        VALUES (:wid, :level, :role_id, :tid)
                    """),
                    {
                        'wid': workflow_id,
                        'level': level['level'],
                        'role_id': role_id,
                        'tid': tenant_id
                    }
                )
            
                print(f"Created workflow: {wf['name']} with {len(wf['levels'])} levels")
        
        session.commit()
        print("\nDefault approval workflows created successfully for all tenants!")

def downgrade():
    """Remove default approval workflows"""
    
    with db_manager.get_session() as session:
        workflow_names = [
            'Purchase Order Approval',
            'Stock Transfer Approval',
            'Voucher Approval (>50000)',
            'Sales Invoice Approval'
        ]
        
        for name in workflow_names:
            # Delete levels first (foreign key constraint)
            session.execute(
                text("""
                    DELETE FROM approval_levels 
                    WHERE workflow_id IN (
                        SELECT id FROM approval_workflows WHERE name = :name
                    )
                """),
                {'name': name}
            )
            
            # Delete workflow
            session.execute(
                text("DELETE FROM approval_workflows WHERE name = :name"),
                {'name': name}
            )
        
        session.commit()
        print("Default approval workflows removed!")

if __name__ == '__main__':
    print("Running migration 061: Default Approval Workflows")
    upgrade()
