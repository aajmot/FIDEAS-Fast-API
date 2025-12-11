from core.database.connection import db_manager
from modules.inventory_module.models.product_waste_entity import ProductWaste, ProductWasteItem
from modules.inventory_module.models.entities import Product, Inventory
from modules.account_module.services.voucher_service import VoucherService
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware
from datetime import datetime
from decimal import Decimal

class ProductWasteService:
    
    def __init__(self):
        self.voucher_service = VoucherService()
    @ExceptionMiddleware.handle_exceptions("ProductWasteService")
    def create(self, waste_data: dict):
        with db_manager.get_session() as session:
            try:
                tenant_id = session_manager.get_current_tenant_id()
                username = session_manager.get_current_username()
                
                # Extract items from waste_data
                items_data = waste_data.pop('items', [])
                if not items_data:
                    raise ValueError("At least one waste item is required")
                
                # Set header-level fields
                waste_data['tenant_id'] = tenant_id
                waste_data['created_by'] = username
                waste_data['updated_by'] = username
                
                # Set currency_id if not provided
                if not waste_data.get('currency_id'):
                    base_currency_code = self._get_tenant_base_currency(session, tenant_id)
                    from modules.admin_module.models.currency import Currency
                    currency = session.query(Currency).filter(
                        Currency.code == base_currency_code,
                        Currency.is_active == True
                    ).first()
                    
                    if not currency:
                        currency = session.query(Currency).filter(
                            Currency.is_base == True,
                            Currency.is_active == True
                        ).first()
                    
                    if currency:
                        waste_data['currency_id'] = currency.id
                
                # Set exchange_rate to 1 for base currency
                if not waste_data.get('exchange_rate'):
                    waste_data['exchange_rate'] = 1.0
                
                # Initialize totals
                waste_data['total_quantity'] = 0
                waste_data['total_cost_base'] = 0
                waste_data['total_cost_foreign'] = 0
                
                # Create header record
                product_waste = ProductWaste(**waste_data)
                session.add(product_waste)
                session.flush()  # Get the waste_id
                
                # Create line items and calculate totals
                for item_data in items_data:
                    item_data['tenant_id'] = tenant_id
                    item_data['waste_id'] = product_waste.id
                    item_data['created_by'] = username
                    item_data['updated_by'] = username
                    
                    # Calculate item totals
                    quantity = Decimal(str(item_data['quantity']))
                    unit_cost_base = Decimal(str(item_data['unit_cost_base']))
                    item_data['total_cost_base'] = quantity * unit_cost_base
                    
                    # Set item currency from header if not specified
                    if not item_data.get('currency_id'):
                        item_data['currency_id'] = waste_data.get('currency_id')
                    if not item_data.get('exchange_rate'):
                        item_data['exchange_rate'] = waste_data.get('exchange_rate', 1.0)
                    
                    # Calculate foreign currency total if provided
                    if item_data.get('unit_cost_foreign'):
                        unit_cost_foreign = Decimal(str(item_data['unit_cost_foreign']))
                        item_data['total_cost_foreign'] = quantity * unit_cost_foreign
                    
                    # Create item
                    waste_item = ProductWasteItem(**item_data)
                    session.add(waste_item)
                    
                    # Update header totals
                    product_waste.total_quantity += quantity
                    product_waste.total_cost_base += item_data['total_cost_base']
                    if item_data.get('total_cost_foreign'):
                        product_waste.total_cost_foreign = (product_waste.total_cost_foreign or 0) + item_data['total_cost_foreign']
                    
                    # Record stock transaction for each item
                    try:
                        from modules.inventory_module.services.stock_service import StockService
                        stock_service = StockService()
                        stock_service.record_waste_transaction_in_session(session, waste_item, product_waste)
                    except (ImportError, AttributeError):
                        pass
                
                session.flush()
                
                # Create accounting voucher for waste
                voucher = self._create_waste_voucher_in_session(session, tenant_id, username, product_waste, items_data)
                product_waste.voucher_id = voucher.id
                
                session.commit()
                return product_waste.id
                
            except Exception as e:
                session.rollback()
                raise e
    
    @ExceptionMiddleware.handle_exceptions("ProductWasteService")
    def get_all(self, page=1, page_size=100):
        from modules.inventory_module.models.entities import Warehouse
        
        with db_manager.get_session() as session:
            query = session.query(ProductWaste)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(ProductWaste.tenant_id == tenant_id, ProductWaste.is_deleted == False)
            
            query = query.order_by(ProductWaste.waste_date.desc(), ProductWaste.created_at.desc())
            
            offset = (page - 1) * page_size
            wastes = query.offset(offset).limit(page_size).all()
            
            # Convert to simple objects with items
            result = []
            for waste in wastes:
                warehouse_name = None
                if waste.warehouse_id:
                    warehouse = session.query(Warehouse).filter(Warehouse.id == waste.warehouse_id).first()
                    if warehouse:
                        warehouse_name = warehouse.name
                
                # Get items for this waste
                items = []
                for item in waste.items:
                    if not item.is_deleted:
                        product = session.query(Product).filter(Product.id == item.product_id).first()
                        items.append({
                            'id': item.id,
                            'line_no': item.line_no,
                            'product_id': item.product_id,
                            'product_name': product.name if product else None,
                            'batch_number': item.batch_number,
                            'quantity': item.quantity,
                            'unit_cost_base': item.unit_cost_base,
                            'total_cost_base': item.total_cost_base,
                            'currency_id': item.currency_id,
                            'unit_cost_foreign': item.unit_cost_foreign,
                            'total_cost_foreign': item.total_cost_foreign,
                            'exchange_rate': item.exchange_rate,
                            'reason': item.reason
                        })
                
                waste_dict = {
                    'id': waste.id,
                    'waste_number': waste.waste_number,
                    'warehouse_id': waste.warehouse_id,
                    'warehouse_name': warehouse_name,
                    'waste_date': waste.waste_date,
                    'reason': waste.reason,
                    'total_quantity': waste.total_quantity,
                    'total_cost_base': waste.total_cost_base,
                    'total_cost_foreign': waste.total_cost_foreign,
                    'currency_id': waste.currency_id,
                    'exchange_rate': waste.exchange_rate,
                    'voucher_id': waste.voucher_id,
                    'is_active': waste.is_active,
                    'created_at': waste.created_at,
                    'created_by': waste.created_by,
                    'updated_at': waste.updated_at,
                    'updated_by': waste.updated_by,
                    'is_deleted': waste.is_deleted,
                    'items': items
                }
                result.append(type('ProductWaste', (), waste_dict)())
            
            return result
    
    @ExceptionMiddleware.handle_exceptions("ProductWasteService")
    def get_total_count(self):
        with db_manager.get_session() as session:
            query = session.query(ProductWaste)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(ProductWaste.tenant_id == tenant_id, ProductWaste.is_deleted == False)
            return query.count()
    

    def _get_tenant_base_currency(self, session, tenant_id):
        """Get tenant's base currency code from tenant_settings"""
        from modules.admin_module.models.entities import TenantSetting
        
        setting = session.query(TenantSetting).filter(
            TenantSetting.tenant_id == tenant_id,
            TenantSetting.setting == 'base_currency'
        ).first()
        
        if setting and setting.value:
            return setting.value
        
        # Default to INR if not found
        return 'INR'
    
    def _create_waste_voucher_in_session(self, session, tenant_id, username, waste, items_data):
        """Create accounting voucher for product waste"""
        from modules.account_module.models.entities import Voucher, VoucherLine, VoucherType
        from modules.account_module.models.account_configuration_entity import AccountConfiguration
        from modules.account_module.models.account_configuration_key_entity import AccountConfigurationKey
        from modules.account_module.models.entities import AccountMaster, AccountGroup
        from decimal import Decimal
        
        # Get JOURNAL voucher type
        voucher_type = session.query(VoucherType).filter(
            VoucherType.tenant_id == tenant_id,
            VoucherType.code == 'JOURNAL',
            VoucherType.is_active == True,
            VoucherType.is_deleted == False
        ).first()
        
        if not voucher_type:
            raise ValueError("Journal voucher type not configured. Please configure 'JOURNAL' voucher type.")
        
        # Generate voucher number
        voucher_number = f"JV-WASTE-{waste.waste_number}"
        
        # Convert total cost to Decimal with 2 decimal places for consistency
        total_cost = Decimal(str(waste.total_cost_base)).quantize(Decimal('0.01')) if waste.total_cost_base else Decimal('0.00')
        
        # Create voucher
        voucher = Voucher(
            tenant_id=tenant_id,
            voucher_number=voucher_number,
            voucher_type_id=voucher_type.id,
            voucher_date=waste.waste_date if hasattr(waste.waste_date, 'hour') else datetime.combine(waste.waste_date, datetime.min.time()),
            base_currency_id=waste.currency_id,
            foreign_currency_id=None,
            exchange_rate=Decimal('1.00'),
            base_total_amount=total_cost,
            base_total_debit=total_cost,
            base_total_credit=total_cost,
            foreign_total_amount=None,
            foreign_total_debit=None,
            foreign_total_credit=None,
            reference_type='PRODUCT_WASTE',
            reference_id=waste.id,
            reference_number=waste.waste_number,
            narration=f"Product waste {waste.waste_number} - {waste.reason or 'Waste recorded'}",
            is_posted=True,
            created_by=username,
            updated_by=username
        )
        
        session.add(voucher)
        session.flush()
        
        # Get configured waste expense account
        waste_expense_account_id = self._get_configured_account(session, tenant_id, 'WASTE_EXPENSE')
        
        # Get inventory account
        inventory_account_id = self._get_configured_account(session, tenant_id, 'INVENTORY')
        
        line_no = 1
        
        # Debit: Waste Expense Account (expense increases)
        waste_expense_line = VoucherLine(
            tenant_id=tenant_id,
            voucher_id=voucher.id,
            line_no=line_no,
            account_id=waste_expense_account_id,
            description=f"Waste expense - {waste.reason or 'Product waste recorded'}",
            debit_base=total_cost,
            credit_base=Decimal('0.00'),
            debit_foreign=None,
            credit_foreign=None,
            reference_type='PRODUCT_WASTE',
            reference_id=waste.id,
            created_by=username,
            updated_by=username
        )
        session.add(waste_expense_line)
        line_no += 1
        
        # Credit: Inventory Account (asset decreases)
        inventory_line = VoucherLine(
            tenant_id=tenant_id,
            voucher_id=voucher.id,
            line_no=line_no,
            account_id=inventory_account_id,
            description=f"Inventory reduction due to waste - {waste.waste_number}",
            debit_base=Decimal('0.00'),
            credit_base=total_cost,
            debit_foreign=None,
            credit_foreign=None,
            reference_type='PRODUCT_WASTE',
            reference_id=waste.id,
            created_by=username,
            updated_by=username
        )
        session.add(inventory_line)
        
        return voucher
    
    def _get_configured_account(self, session, tenant_id, key_code):
        """Get configured account ID from account configuration"""
        from modules.account_module.models.account_configuration_entity import AccountConfiguration
        from modules.account_module.models.account_configuration_key_entity import AccountConfigurationKey
        from modules.account_module.models.entities import AccountMaster, AccountGroup
        
        # Get configuration key
        config_key = session.query(AccountConfigurationKey).filter(
            AccountConfigurationKey.code == key_code,
            AccountConfigurationKey.is_active == True
        ).first()
        
        if not config_key:
            raise ValueError(f"Account configuration key '{key_code}' not found")
        
        # Get account configuration for tenant
        config = session.query(AccountConfiguration).filter(
            AccountConfiguration.tenant_id == tenant_id,
            AccountConfiguration.config_key_id == config_key.id,
            AccountConfiguration.is_deleted == False
        ).first()
        
        if config and config.account_id:
            return config.account_id
        
        # Fallback: Try to find account by system code or name pattern
        if key_code == 'WASTE_EXPENSE':
            # Look for expense account with "waste" in name or system code
            account = session.query(AccountMaster).filter(
                AccountMaster.tenant_id == tenant_id,
                AccountMaster.account_type == 'EXPENSE',
                AccountMaster.is_deleted == False
            ).filter(
                (AccountMaster.name.ilike('%waste%')) | 
                (AccountMaster.system_code.ilike('%waste%'))
            ).first()
            
            if account:
                return account.id
            
            # Create default waste expense account
            return self._create_default_waste_account(session, tenant_id, 'EXPENSE')
        
        elif key_code == 'INVENTORY':
            # Look for inventory asset account
            account = session.query(AccountMaster).filter(
                AccountMaster.tenant_id == tenant_id,
                AccountMaster.account_type == 'ASSET',
                AccountMaster.is_deleted == False
            ).filter(
                (AccountMaster.name.ilike('%inventory%')) | 
                (AccountMaster.system_code.ilike('%inventory%')) |
                (AccountMaster.name.ilike('%stock%'))
            ).first()
            
            if account:
                return account.id
            
            # Create default inventory account
            return self._create_default_inventory_account(session, tenant_id)
        
        raise ValueError(f"No account configured for '{key_code}' and no suitable fallback found")
    
    def _create_default_waste_account(self, session, tenant_id, account_type):
        """Create default waste expense account"""
        from modules.account_module.models.entities import AccountMaster, AccountGroup
        
        username = session_manager.get_current_username()
        
        # Find or create expense group
        expense_group = session.query(AccountGroup).filter(
            AccountGroup.tenant_id == tenant_id,
            AccountGroup.account_type == 'EXPENSE',
            AccountGroup.is_deleted == False
        ).first()
        
        if not expense_group:
            expense_group = AccountGroup(
                tenant_id=tenant_id,
                name='Expenses',
                code='EXP',
                account_type='EXPENSE',
                normal_balance='DEBIT',
                is_active=True,
                created_by=username,
                updated_by=username
            )
            session.add(expense_group)
            session.flush()
        
        # Create waste expense account
        account = AccountMaster(
            tenant_id=tenant_id,
            name='Waste & Spoilage Expense',
            code='WASTE-EXP-001',
            system_code='WASTE_EXPENSE',
            account_type='EXPENSE',
            account_group_id=expense_group.id,
            normal_balance='DEBIT',
            is_active=True,
            is_sub_ledger=False,
            created_by=username,
            updated_by=username
        )
        session.add(account)
        session.flush()
        
        return account.id
    
    def _create_default_inventory_account(self, session, tenant_id):
        """Create default inventory account"""
        from modules.account_module.models.entities import AccountMaster, AccountGroup
        
        username = session_manager.get_current_username()
        
        # Find or create asset group
        asset_group = session.query(AccountGroup).filter(
            AccountGroup.tenant_id == tenant_id,
            AccountGroup.account_type == 'ASSET',
            AccountGroup.is_deleted == False
        ).first()
        
        if not asset_group:
            asset_group = AccountGroup(
                tenant_id=tenant_id,
                name='Assets',
                code='AST',
                account_type='ASSET',
                normal_balance='DEBIT',
                is_active=True,
                created_by=username,
                updated_by=username
            )
            session.add(asset_group)
            session.flush()
        
        # Create inventory account
        account = AccountMaster(
            tenant_id=tenant_id,
            name='Inventory',
            code='INV-001',
            system_code='INVENTORY',
            account_type='ASSET',
            account_group_id=asset_group.id,
            normal_balance='DEBIT',
            is_active=True,
            is_sub_ledger=False,
            created_by=username,
            updated_by=username
        )
        session.add(account)
        session.flush()
        
        return account.id