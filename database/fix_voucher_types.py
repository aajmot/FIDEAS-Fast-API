#!/usr/bin/env python3
"""Fix voucher type codes"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_manager
from sqlalchemy import text

def fix_voucher_types():
    print("Fixing voucher type codes...")
    
    with db_manager.get_session() as session:
        updates = [
            ("UPDATE voucher_types SET code = 'SAL', prefix = 'SAL-' WHERE code = 'SL'", "Sales"),
            ("UPDATE voucher_types SET code = 'PUR', prefix = 'PUR-' WHERE code = 'PU'", "Purchase"),
            ("UPDATE voucher_types SET code = 'PAY', prefix = 'PAY-' WHERE code = 'PY'", "Payment"),
            ("UPDATE voucher_types SET code = 'REC', prefix = 'REC-' WHERE code = 'RC'", "Receipt"),
        ]
        
        for sql, name in updates:
            result = session.execute(text(sql))
            if result.rowcount > 0:
                print(f"✓ Fixed {name} voucher type")
        
        session.commit()
        print("\n✓ All voucher types fixed!")

if __name__ == "__main__":
    fix_voucher_types()
