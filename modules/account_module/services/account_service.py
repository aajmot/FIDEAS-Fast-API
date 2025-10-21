from core.database.connection import db_manager
from modules.account_module.models.entities import *
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware
from datetime import datetime
from decimal import Decimal

class AccountService:
    @ExceptionMiddleware.handle_exceptions("AccountService")
    def initialize_default_accounts(self):
        """Initialize default chart of accounts"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            # Use default tenant ID (1) if no user is logged in during initialization
            if tenant_id is None:
                tenant_id = 1
            
            # Check if accounts already exist
            existing = session.query(AccountGroup).filter(AccountGroup.tenant_id == tenant_id).first()
            if existing:
                return
            
            # Create default account groups
            groups = [
                {'name': 'Current Assets', 'code': 'CA', 'account_type': 'ASSET'},
                {'name': 'Cash & Bank', 'code': 'CB', 'account_type': 'ASSET', 'parent_code': 'CA'},
                {'name': 'Accounts Receivable', 'code': 'AR', 'account_type': 'ASSET', 'parent_code': 'CA'},
                {'name': 'Inventory', 'code': 'INV', 'account_type': 'ASSET', 'parent_code': 'CA'},
                {'name': 'Current Liabilities', 'code': 'CL', 'account_type': 'LIABILITY'},
                {'name': 'Accounts Payable', 'code': 'AP', 'account_type': 'LIABILITY', 'parent_code': 'CL'},
                {'name': 'Revenue', 'code': 'REV', 'account_type': 'INCOME'},
                {'name': 'Sales', 'code': 'SAL', 'account_type': 'INCOME', 'parent_code': 'REV'},
                {'name': 'Expenses', 'code': 'EXP', 'account_type': 'EXPENSE'},
                {'name': 'Cost of Goods Sold', 'code': 'COGS', 'account_type': 'EXPENSE', 'parent_code': 'EXP'},
            ]
            
            group_map = {}
            for group_data in groups:
                parent_id = None
                if 'parent_code' in group_data:
                    parent_id = group_map.get(group_data['parent_code'])
                
                group = AccountGroup(
                    name=group_data['name'],
                    code=group_data['code'],
                    account_type=group_data['account_type'],
                    parent_id=parent_id,
                    tenant_id=tenant_id
                )
                session.add(group)
                session.flush()
                group_map[group_data['code']] = group.id
            
            # Create default accounts
            accounts = [
                {'name': 'Cash in Hand', 'code': 'CASH001', 'group_code': 'CB'},
                {'name': 'Bank Account', 'code': 'BANK001', 'group_code': 'CB'},
                {'name': 'Accounts Receivable', 'code': 'AR001', 'group_code': 'AR'},
                {'name': 'Inventory Account', 'code': 'INV001', 'group_code': 'INV'},
                {'name': 'Accounts Payable', 'code': 'AP001', 'group_code': 'AP'},
                {'name': 'Sales Revenue', 'code': 'SAL001', 'group_code': 'SAL'},
                {'name': 'Cost of Goods Sold', 'code': 'COGS001', 'group_code': 'COGS'},
                {'name': 'General Expenses', 'code': 'EXP001', 'group_code': 'EXP'},
            ]
            
            for account_data in accounts:
                account = AccountMaster(
                    name=account_data['name'],
                    code=account_data['code'],
                    account_group_id=group_map[account_data['group_code']],
                    tenant_id=tenant_id,
                    created_by=session_manager.get_current_username()
                )
                session.add(account)
            
            # Create default voucher types
            voucher_types = [
                {'name': 'Sales', 'code': 'SAL', 'prefix': 'SAL'},
                {'name': 'Purchase', 'code': 'PUR', 'prefix': 'PUR'},
                {'name': 'Payment', 'code': 'PAY', 'prefix': 'PAY'},
                {'name': 'Receipt', 'code': 'REC', 'prefix': 'REC'},
                {'name': 'Journal', 'code': 'JV', 'prefix': 'JV'},
            ]
            
            for vt_data in voucher_types:
                voucher_type = VoucherType(
                    name=vt_data['name'],
                    code=vt_data['code'],
                    prefix=vt_data['prefix'],
                    tenant_id=tenant_id
                )
                session.add(voucher_type)
            
            session.commit()
    
    @ExceptionMiddleware.handle_exceptions("AccountService")
    def update_account_balance(self, account_id, amount, transaction_type):
        """Update account balance"""
        with db_manager.get_session() as session:
            self.update_account_balance_in_session(session, account_id, amount, transaction_type)
            session.commit()
    
    def update_account_balance_in_session(self, session, account_id, amount, transaction_type):
        """Update account balance within existing session"""
        account = session.query(AccountMaster).filter(AccountMaster.id == account_id).first()
        if account:
            if account.current_balance is None:
                account.current_balance = Decimal('0')
            
            if transaction_type == 'DEBIT':
                if account.account_group.account_type in ['ASSET', 'EXPENSE']:
                    account.current_balance += Decimal(str(amount))
                else:
                    account.current_balance -= Decimal(str(amount))
            else:  # CREDIT
                if account.account_group.account_type in ['LIABILITY', 'EQUITY', 'INCOME']:
                    account.current_balance += Decimal(str(amount))
                else:
                    account.current_balance -= Decimal(str(amount))