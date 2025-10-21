from sqlalchemy import text
from core.database.connection import db_manager

def upgrade():
    """Add order_commission_number column to order_commissions table"""
    with db_manager.get_session() as session:
        try:
            # Add order_commission_number column
            session.execute(text("""
                ALTER TABLE order_commissions 
                ADD COLUMN order_commission_number VARCHAR(50)
            """))
            
            session.commit()
            print("Added order_commission_number column to order_commissions table")
            
        except Exception as e:
            session.rollback()
            print(f"Error adding order_commission_number column: {str(e)}")
            raise

def downgrade():
    """Remove order_commission_number column from order_commissions table"""
    with db_manager.get_session() as session:
        try:
            session.execute(text("""
                ALTER TABLE order_commissions 
                DROP COLUMN order_commission_number
            """))
            
            session.commit()
            print("Removed order_commission_number column from order_commissions table")
            
        except Exception as e:
            session.rollback()
            print(f"Error removing order_commission_number column: {str(e)}")
            raise

if __name__ == "__main__":
    print("Running migration: Add order_commission_number to order_commissions")
    upgrade()
    print("Migration completed successfully")
