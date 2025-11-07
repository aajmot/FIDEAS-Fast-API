from core.database.connection import db_manager
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware
from modules.account_module.models.entities import AccountMaster, AccountGroup
from sqlalchemy import func, or_
from decimal import Decimal
import math


class AccountMasterService:
    """Service layer for account master management"""
    
    @ExceptionMiddleware.handle_exceptions("AccountMasterService")
    def create(self, account_data: dict):
        """Create a new account master"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            username = session_manager.get_current_username()
            
            # Check if account code already exists
            existing = session.query(AccountMaster).filter(
                AccountMaster.tenant_id == tenant_id,
                AccountMaster.code == account_data.get('code'),
                AccountMaster.is_deleted == False
            ).first()
            
            if existing:
                raise ValueError(f"Account code '{account_data.get('code')}' already exists")
            
            # Validate account group exists
            account_group = session.query(AccountGroup).filter(
                AccountGroup.id == account_data.get('account_group_id'),
                AccountGroup.tenant_id == tenant_id
            ).first()
            
            if not account_group:
                raise ValueError(f"Account group ID {account_data.get('account_group_id')} not found")
            
            # Validate parent if provided
            if account_data.get('parent_id'):
                parent = session.query(AccountMaster).filter(
                    AccountMaster.id == account_data['parent_id'],
                    AccountMaster.tenant_id == tenant_id,
                    AccountMaster.is_deleted == False
                ).first()
                
                if not parent:
                    raise ValueError(f"Parent account ID {account_data['parent_id']} not found")
                
                # Calculate level based on parent
                account_data['level'] = parent.level + 1
            
            # Create account
            account = AccountMaster(
                tenant_id=tenant_id,
                parent_id=account_data.get('parent_id'),
                account_group_id=account_data.get('account_group_id'),
                code=account_data.get('code'),
                name=account_data.get('name'),
                description=account_data.get('description'),
                account_type=account_data.get('account_type'),
                normal_balance=account_data.get('normal_balance', 'D'),
                is_system_account=account_data.get('is_system_account', False),
                system_code=account_data.get('system_code'),
                level=account_data.get('level', 1),
                path=account_data.get('path'),
                opening_balance=account_data.get('opening_balance', 0),
                current_balance=account_data.get('current_balance', 0),
                is_reconciled=account_data.get('is_reconciled', False),
                is_active=account_data.get('is_active', True),
                created_by=username,
                updated_by=username
            )
            
            session.add(account)
            session.commit()
            session.refresh(account)
            
            return self.get_by_id(account.id)
    
    @ExceptionMiddleware.handle_exceptions("AccountMasterService")
    def get_all(self, page=1, page_size=100, search=None, account_type=None, 
                account_group_id=None, is_active=None, parent_id=None):
        """Get all account masters with pagination and filters"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            query = session.query(AccountMaster).filter(
                AccountMaster.tenant_id == tenant_id,
                AccountMaster.is_deleted == False
            )
            
            # Apply filters
            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    or_(
                        AccountMaster.code.ilike(search_pattern),
                        AccountMaster.name.ilike(search_pattern),
                        AccountMaster.description.ilike(search_pattern)
                    )
                )
            
            if account_type:
                query = query.filter(AccountMaster.account_type == account_type)
            
            if account_group_id:
                query = query.filter(AccountMaster.account_group_id == account_group_id)
            
            if is_active is not None:
                query = query.filter(AccountMaster.is_active == is_active)
            
            if parent_id is not None:
                query = query.filter(AccountMaster.parent_id == parent_id)
            
            # Get total count
            total = query.count()
            
            # Apply pagination and ordering
            query = query.order_by(AccountMaster.code)
            offset = (page - 1) * page_size
            accounts = query.offset(offset).limit(page_size).all()
            
            return {
                'total': total,
                'page': page,
                'per_page': page_size,
                'total_pages': math.ceil(total / page_size) if total > 0 else 0,
                'data': [self._to_dict(acc) for acc in accounts]
            }
    
    @ExceptionMiddleware.handle_exceptions("AccountMasterService")
    def get_by_id(self, account_id: int):
        """Get a specific account master by ID"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            account = session.query(AccountMaster).filter(
                AccountMaster.id == account_id,
                AccountMaster.tenant_id == tenant_id,
                AccountMaster.is_deleted == False
            ).first()
            
            if not account:
                return None
            
            return self._to_dict(account)
    
    @ExceptionMiddleware.handle_exceptions("AccountMasterService")
    def update(self, account_id: int, account_data: dict):
        """Update an existing account master"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            username = session_manager.get_current_username()
            
            account = session.query(AccountMaster).filter(
                AccountMaster.id == account_id,
                AccountMaster.tenant_id == tenant_id,
                AccountMaster.is_deleted == False
            ).first()
            
            if not account:
                return None
            
            # Prevent modification of system accounts
            if account.is_system_account:
                raise ValueError("System accounts cannot be modified")
            
            # Check if code changed and is unique
            if 'code' in account_data and account_data['code'] != account.code:
                existing = session.query(AccountMaster).filter(
                    AccountMaster.tenant_id == tenant_id,
                    AccountMaster.code == account_data['code'],
                    AccountMaster.id != account_id,
                    AccountMaster.is_deleted == False
                ).first()
                
                if existing:
                    raise ValueError(f"Account code '{account_data['code']}' already exists")
            
            # Validate parent if changed
            if 'parent_id' in account_data and account_data['parent_id']:
                if account_data['parent_id'] == account_id:
                    raise ValueError("Account cannot be its own parent")
                
                parent = session.query(AccountMaster).filter(
                    AccountMaster.id == account_data['parent_id'],
                    AccountMaster.tenant_id == tenant_id,
                    AccountMaster.is_deleted == False
                ).first()
                
                if not parent:
                    raise ValueError(f"Parent account ID {account_data['parent_id']} not found")
                
                account_data['level'] = parent.level + 1
            
            # Update fields
            for field in ['parent_id', 'account_group_id', 'code', 'name', 'description',
                         'account_type', 'normal_balance', 'system_code', 'level', 'path',
                         'opening_balance', 'current_balance', 'is_reconciled', 'is_active']:
                if field in account_data:
                    setattr(account, field, account_data[field])
            
            account.updated_by = username
            
            session.commit()
            session.refresh(account)
            
            return self._to_dict(account)
    
    @ExceptionMiddleware.handle_exceptions("AccountMasterService")
    def delete(self, account_id: int):
        """Soft delete an account master"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            username = session_manager.get_current_username()
            
            account = session.query(AccountMaster).filter(
                AccountMaster.id == account_id,
                AccountMaster.tenant_id == tenant_id,
                AccountMaster.is_deleted == False
            ).first()
            
            if not account:
                return False
            
            # Prevent deletion of system accounts
            if account.is_system_account:
                raise ValueError("System accounts cannot be deleted")
            
            # Check if account has children
            children = session.query(AccountMaster).filter(
                AccountMaster.parent_id == account_id,
                AccountMaster.tenant_id == tenant_id,
                AccountMaster.is_deleted == False
            ).count()
            
            if children > 0:
                raise ValueError("Cannot delete account with child accounts")
            
            account.is_deleted = True
            account.is_active = False
            account.updated_by = username
            
            session.commit()
            return True
    
    @ExceptionMiddleware.handle_exceptions("AccountMasterService")
    def update_balance(self, account_id: int, amount: Decimal, transaction_type: str):
        """Update account balance based on transaction type (DEBIT/CREDIT)"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            username = session_manager.get_current_username()
            
            account = session.query(AccountMaster).filter(
                AccountMaster.id == account_id,
                AccountMaster.tenant_id == tenant_id,
                AccountMaster.is_deleted == False
            ).first()
            
            if not account:
                raise ValueError(f"Account ID {account_id} not found")
            
            # Update balance based on normal balance and transaction type
            if transaction_type == 'DEBIT':
                if account.normal_balance == 'D':
                    account.current_balance += amount
                else:
                    account.current_balance -= amount
            else:  # CREDIT
                if account.normal_balance == 'C':
                    account.current_balance += amount
                else:
                    account.current_balance -= amount
            
            account.updated_by = username
            
            session.commit()
            return self._to_dict(account)
    
    def _to_dict(self, account):
        """Convert account entity to dictionary"""
        return {
            'id': account.id,
            'tenant_id': account.tenant_id,
            'parent_id': account.parent_id,
            'account_group_id': account.account_group_id,
            'code': account.code,
            'name': account.name,
            'description': account.description,
            'account_type': account.account_type,
            'normal_balance': account.normal_balance,
            'is_system_account': account.is_system_account,
            'system_code': account.system_code,
            'level': account.level,
            'path': account.path,
            'opening_balance': account.opening_balance,
            'current_balance': account.current_balance,
            'is_reconciled': account.is_reconciled,
            'is_active': account.is_active,
            'is_deleted': account.is_deleted,
            'created_at': account.created_at,
            'created_by': account.created_by,
            'updated_at': account.updated_at,
            'updated_by': account.updated_by
        }
