#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from modules.admin_module.models.entities import MenuMaster

def add_care_menus():
    """Add Test Category and Test Master menus under Clinic->Master"""
    print("Adding care module menus...")
    
    try:
        with db_manager.get_session() as session:
            # Get Clinic main menu
            clinic_menu = session.query(MenuMaster).filter_by(menu_code="CLINIC_MAIN").first()
            
            if not clinic_menu:
                print("[ERROR] Clinic main menu not found")
                return
            
            # Check if Master submenu exists
            master_menu = session.query(MenuMaster).filter_by(menu_code="CLINIC_MASTER").first()
            
            if not master_menu:
                # Create Master submenu
                master_menu = MenuMaster(
                    menu_name="Master",
                    menu_code="CLINIC_MASTER",
                    module_code="CLINIC",
                    parent_menu_id=clinic_menu.id,
                    icon="📋",
                    route="/clinic/master",
                    sort_order=8,
                    is_admin_only=False
                )
                session.add(master_menu)
                session.flush()
            
            # Add Test Category menu
            test_category_exists = session.query(MenuMaster).filter_by(menu_code="TEST_CATEGORY").first()
            if not test_category_exists:
                test_category_menu = MenuMaster(
                    menu_name="Test Category",
                    menu_code="TEST_CATEGORY",
                    module_code="CLINIC",
                    parent_menu_id=master_menu.id,
                    icon="🏷️",
                    route="/clinic/test-category",
                    sort_order=1,
                    is_admin_only=False
                )
                session.add(test_category_menu)
            
            # Add Test Master menu
            test_master_exists = session.query(MenuMaster).filter_by(menu_code="TEST_MASTER").first()
            if not test_master_exists:
                test_master_menu = MenuMaster(
                    menu_name="Test Master",
                    menu_code="TEST_MASTER",
                    module_code="CLINIC",
                    parent_menu_id=master_menu.id,
                    icon="🧪",
                    route="/clinic/test-master",
                    sort_order=2,
                    is_admin_only=False
                )
                session.add(test_master_menu)
            
            session.commit()
            print("✓ Care module menus added successfully")
            
    except Exception as e:
        print(f"[ERROR] Error adding care menus: {str(e)}")
        raise

if __name__ == "__main__":
    add_care_menus()
