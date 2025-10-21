#!/usr/bin/env python3
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from modules.admin_module.models.entities import MenuMaster

def add_diagnostics_menus():
    """Add Diagnostics module menus"""
    print("Adding diagnostics module menus...")
    
    try:
        with db_manager.get_session() as session:
            # Check if Diagnostics main menu exists
            diagnostics_main = session.query(MenuMaster).filter_by(menu_code="DIAGNOSTICS_MAIN").first()
            
            if not diagnostics_main:
                diagnostics_main = MenuMaster(
                    menu_name="Diagnostics",
                    menu_code="DIAGNOSTICS_MAIN",
                    module_code="DIAGNOSTICS",
                    parent_menu_id=None,
                    icon="🔬",
                    route="/diagnostics",
                    sort_order=5,
                    is_admin_only=False
                )
                session.add(diagnostics_main)
                session.flush()
            
            # Add Test Orders menu
            if not session.query(MenuMaster).filter_by(menu_code="TEST_ORDERS").first():
                session.add(MenuMaster(
                    menu_name="Test Orders",
                    menu_code="TEST_ORDERS",
                    module_code="DIAGNOSTICS",
                    parent_menu_id=diagnostics_main.id,
                    icon="📝",
                    route="/diagnostics/test-orders",
                    sort_order=1,
                    is_admin_only=False
                ))
            
            # Add Test Results menu
            if not session.query(MenuMaster).filter_by(menu_code="TEST_RESULTS").first():
                session.add(MenuMaster(
                    menu_name="Test Results",
                    menu_code="TEST_RESULTS",
                    module_code="DIAGNOSTICS",
                    parent_menu_id=diagnostics_main.id,
                    icon="📊",
                    route="/diagnostics/test-results",
                    sort_order=2,
                    is_admin_only=False
                ))
            
            # Add Test Panels menu
            if not session.query(MenuMaster).filter_by(menu_code="TEST_PANELS").first():
                session.add(MenuMaster(
                    menu_name="Test Panels",
                    menu_code="TEST_PANELS",
                    module_code="DIAGNOSTICS",
                    parent_menu_id=diagnostics_main.id,
                    icon="📋",
                    route="/diagnostics/test-panels",
                    sort_order=3,
                    is_admin_only=False
                ))
            
            session.commit()
            print("✓ Diagnostics module menus added successfully")
            
    except Exception as e:
        print(f"[ERROR] Error adding diagnostics menus: {str(e)}")
        raise

if __name__ == "__main__":
    add_diagnostics_menus()
