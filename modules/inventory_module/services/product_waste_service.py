from core.database.connection import db_manager
from modules.inventory_module.models.product_waste_entity import ProductWaste, ProductWasteItem
from modules.inventory_module.models.entities import Product, Inventory
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware
from datetime import datetime
from decimal import Decimal

class ProductWasteService:
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
                
                # Record accounting transaction
                try:
                    self._record_accounting_transaction_in_session(session, product_waste)
                except (ImportError, AttributeError):
                    pass
                
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
    
    def _record_accounting_transaction_in_session(self, session, product_waste):
        try:
            from modules.account_module.services.payment_service import PaymentService
            payment_service = PaymentService()
            payment_service.record_waste_transaction_in_session(
                session,
                product_waste.id,
                product_waste.waste_number,
                float(product_waste.total_cost_base),  # Use base currency cost
                product_waste.waste_date
            )
        except ImportError:
            pass  # Account module not available