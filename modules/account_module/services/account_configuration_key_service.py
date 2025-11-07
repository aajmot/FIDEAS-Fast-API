from core.database.connection import db_manager
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware
from modules.account_module.models.account_configuration_key_entity import AccountConfigurationKey
from modules.account_module.models.entities import AccountMaster
from sqlalchemy import func, or_
import math


class AccountConfigurationKeyService:
    """Service layer for account configuration keys management"""
    
    @ExceptionMiddleware.handle_exceptions("AccountConfigurationKeyService")
    def create(self, key_data: dict):
        """Create a new account configuration key"""
        with db_manager.get_session() as session:
            username = session_manager.get_current_username()
            
            # Check if code already exists
            existing = session.query(AccountConfigurationKey).filter(
                AccountConfigurationKey.code == key_data.get('code'),
                AccountConfigurationKey.is_deleted == False
            ).first()
            
            if existing:
                raise ValueError(f"Configuration key code '{key_data.get('code')}' already exists")
            
            # Validate default account if provided
            if key_data.get('default_account_id'):
                account = session.query(AccountMaster).filter(
                    AccountMaster.id == key_data['default_account_id'],
                    AccountMaster.is_deleted == False
                ).first()
                
                if not account:
                    raise ValueError(f"Default account ID {key_data['default_account_id']} not found")
            
            # Create configuration key
            config_key = AccountConfigurationKey(
                code=key_data.get('code'),
                name=key_data.get('name'),
                description=key_data.get('description'),
                default_account_id=key_data.get('default_account_id'),
                is_active=key_data.get('is_active', True)
            )
            
            session.add(config_key)
            session.commit()
            session.refresh(config_key)
            
            return {
                "id": config_key.id,
                "code": config_key.code,
                "name": config_key.name,
                "description": config_key.description,
                "default_account_id": config_key.default_account_id,
                "is_active": config_key.is_active,
                "created_at": config_key.created_at.isoformat() if config_key.created_at else None
            }
    
    @ExceptionMiddleware.handle_exceptions("AccountConfigurationKeyService")
    def get_by_id(self, key_id: int):
        """Get configuration key by ID"""
        with db_manager.get_session() as session:
            config_key = session.query(AccountConfigurationKey).filter(
                AccountConfigurationKey.id == key_id,
                AccountConfigurationKey.is_deleted == False
            ).first()
            
            if not config_key:
                raise ValueError(f"Configuration key ID {key_id} not found")
            
            return self._format_key(config_key)
    
    @ExceptionMiddleware.handle_exceptions("AccountConfigurationKeyService")
    def get_by_code(self, code: str):
        """Get configuration key by code"""
        with db_manager.get_session() as session:
            config_key = session.query(AccountConfigurationKey).filter(
                AccountConfigurationKey.code == code,
                AccountConfigurationKey.is_deleted == False
            ).first()
            
            if not config_key:
                raise ValueError(f"Configuration key code '{code}' not found")
            
            return self._format_key(config_key)
    
    @ExceptionMiddleware.handle_exceptions("AccountConfigurationKeyService")
    def get_all(self, 
                page: int = 1, 
                limit: int = 50,
                search: str = None,
                is_active: bool = None,
                sort_by: str = 'code',
                sort_order: str = 'asc'):
        """Get all configuration keys with pagination and filtering"""
        with db_manager.get_session() as session:
            # Base query
            query = session.query(AccountConfigurationKey).filter(
                AccountConfigurationKey.is_deleted == False
            )
            
            # Apply filters
            if search:
                search_filter = f"%{search}%"
                query = query.filter(
                    or_(
                        AccountConfigurationKey.code.ilike(search_filter),
                        AccountConfigurationKey.name.ilike(search_filter),
                        AccountConfigurationKey.description.ilike(search_filter)
                    )
                )
            
            if is_active is not None:
                query = query.filter(AccountConfigurationKey.is_active == is_active)
            
            # Get total count
            total_count = query.count()
            
            # Apply sorting
            if sort_order.lower() == 'desc':
                query = query.order_by(getattr(AccountConfigurationKey, sort_by).desc())
            else:
                query = query.order_by(getattr(AccountConfigurationKey, sort_by).asc())
            
            # Apply pagination
            offset = (page - 1) * limit
            keys = query.offset(offset).limit(limit).all()
            
            return {
                "items": [self._format_key(key) for key in keys],
                "pagination": {
                    "total": total_count,
                    "page": page,
                    "limit": limit,
                    "total_pages": math.ceil(total_count / limit) if limit > 0 else 0
                }
            }
    
    @ExceptionMiddleware.handle_exceptions("AccountConfigurationKeyService")
    def update(self, key_id: int, key_data: dict):
        """Update configuration key"""
        with db_manager.get_session() as session:
            config_key = session.query(AccountConfigurationKey).filter(
                AccountConfigurationKey.id == key_id,
                AccountConfigurationKey.is_deleted == False
            ).first()
            
            if not config_key:
                raise ValueError(f"Configuration key ID {key_id} not found")
            
            # Check if updating code to existing one
            if 'code' in key_data and key_data['code'] != config_key.code:
                existing = session.query(AccountConfigurationKey).filter(
                    AccountConfigurationKey.code == key_data['code'],
                    AccountConfigurationKey.id != key_id,
                    AccountConfigurationKey.is_deleted == False
                ).first()
                
                if existing:
                    raise ValueError(f"Configuration key code '{key_data['code']}' already exists")
            
            # Validate default account if provided
            if 'default_account_id' in key_data and key_data['default_account_id']:
                account = session.query(AccountMaster).filter(
                    AccountMaster.id == key_data['default_account_id'],
                    AccountMaster.is_deleted == False
                ).first()
                
                if not account:
                    raise ValueError(f"Default account ID {key_data['default_account_id']} not found")
            
            # Update fields
            if 'code' in key_data:
                config_key.code = key_data['code']
            if 'name' in key_data:
                config_key.name = key_data['name']
            if 'description' in key_data:
                config_key.description = key_data['description']
            if 'default_account_id' in key_data:
                config_key.default_account_id = key_data['default_account_id']
            if 'is_active' in key_data:
                config_key.is_active = key_data['is_active']
            
            session.commit()
            session.refresh(config_key)
            
            return self._format_key(config_key)
    
    @ExceptionMiddleware.handle_exceptions("AccountConfigurationKeyService")
    def delete(self, key_id: int):
        """Soft delete configuration key"""
        with db_manager.get_session() as session:
            config_key = session.query(AccountConfigurationKey).filter(
                AccountConfigurationKey.id == key_id,
                AccountConfigurationKey.is_deleted == False
            ).first()
            
            if not config_key:
                raise ValueError(f"Configuration key ID {key_id} not found")
            
            # Soft delete
            config_key.is_deleted = True
            session.commit()
            
            return {"message": f"Configuration key '{config_key.code}' deleted successfully"}
    
    def _format_key(self, config_key):
        """Format configuration key for response"""
        result = {
            "id": config_key.id,
            "code": config_key.code,
            "name": config_key.name,
            "description": config_key.description,
            "default_account_id": config_key.default_account_id,
            "is_active": config_key.is_active,
            "created_at": config_key.created_at.isoformat() if config_key.created_at else None
        }
        
        # Include default account details if present
        if config_key.default_account:
            result["default_account"] = {
                "id": config_key.default_account.id,
                "code": config_key.default_account.code,
                "name": config_key.default_account.name,
                "account_type": config_key.default_account.account_type
            }
        
        return result
