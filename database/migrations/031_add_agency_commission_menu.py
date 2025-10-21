#!/usr/bin/env python3
"""
Add Agency Commission Setup menu to Admin Transaction section
"""

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def upgrade():
    """Add Agency Commission Setup menu"""
    print("Adding Agency Commission Setup menu...")
    
    try:
        with db_manager.get_session() as session:
            # Get Admin Transaction parent menu ID
            result = session.execute(text(
                "SELECT id FROM menu_master WHERE menu_code = 'ADMIN_TRANSACTION'"
            )).fetchone()
            
            if not result:
                print("[ERROR] Admin Transaction menu not found")
                return
            
            parent_id = result[0]
            
            # Check if menu already exists
            existing = session.execute(text(
                "SELECT id FROM menu_master WHERE menu_code = 'AGENCY_COMMISSION_SETUP'"
            )).fetchone()
            
            if existing:
                print("[INFO] Agency Commission Setup menu already exists")
                return
            
            # Insert Agency Commission Setup menu
            session.execute(text(
                """INSERT INTO menu_master 
                (menu_name, menu_code, module_code, parent_menu_id, icon, route, sort_order) 
                VALUES (:name, :code, :module, :parent, :icon, :route, :sort)"""
            ), {
                "name": "Agency Commission Setup",
                "code": "AGENCY_COMMISSION_SETUP",
                "module": "ADMIN",
                "parent": parent_id,
                "icon": "💰",
                "route": "/admin/agency-commission-setup",
                "sort": 4
            })
            
            session.commit()
            print("[OK] Agency Commission Setup menu added")
            
    except Exception as e:
        print(f"[ERROR] Error adding menu: {str(e)}")
        raise

if __name__ == "__main__":
    print("Running migration 031...")
    upgrade()
    print("Migration 031 completed!")
