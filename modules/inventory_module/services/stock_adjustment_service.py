from core.database.connection import db_manager
from modules.inventory_module.models.stock_adjustment_entity import StockAdjustment, StockAdjustmentItem
from modules.inventory_module.models.entities import Product, Warehouse, Inventory
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware
from datetime import datetime
from decimal import Decimal


class StockAdjustmentService:
    
    @ExceptionMiddleware.handle_exceptions("StockAdjustmentService")
    def create(self, adjustment_data: dict):
        with db_manager.get_session() as session:
            try:
                tenant_id = session_manager.get_current_tenant_id()
                username = session_manager.get_current_username()
                
                # Extract items from adjustment_data
                items_data = adjustment_data.pop('items', [])
                if not items_data:
                    raise ValueError("At least one adjustment item is required")
                
                # Set header-level fields
                adjustment_data['tenant_id'] = tenant_id
                adjustment_data['created_by'] = username
                adjustment_data['updated_by'] = username
                
                # Set currency_id if not provided
                if not adjustment_data.get('currency_id'):
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
                        adjustment_data['currency_id'] = currency.id
                
                # Set exchange_rate to 1 for base currency
                if not adjustment_data.get('exchange_rate'):
                    adjustment_data['exchange_rate'] = 1.0
                
                # Initialize totals
                adjustment_data['total_items'] = 0
                adjustment_data['net_quantity_change'] = 0
                adjustment_data['total_cost_impact'] = 0
                
                # Create header record
                stock_adjustment = StockAdjustment(**adjustment_data)
                session.add(stock_adjustment)
                session.flush()  # Get the adjustment_id
                
                # Create line items and calculate totals
                for item_data in items_data:
                    item_data['tenant_id'] = tenant_id
                    item_data['adjustment_id'] = stock_adjustment.id
                    item_data['created_by'] = username
                    item_data['updated_by'] = username
                    
                    # Get current stock before adjustment
                    warehouse_id = adjustment_data['warehouse_id']
                    product_id = item_data['product_id']
                    batch_number = item_data.get('batch_number', '')
                    
                    # Get stock_before if not provided
                    if item_data.get('stock_before') is None:
                        current_stock = self._get_current_stock(session, warehouse_id, product_id, batch_number)
                        item_data['stock_before'] = current_stock
                    else:
                        current_stock = Decimal(str(item_data['stock_before']))
                    
                    # Calculate stock_after
                    adjustment_qty = Decimal(str(item_data['adjustment_qty']))
                    item_data['stock_after'] = current_stock + adjustment_qty
                    
                    # Calculate cost_impact (adjustment_qty * unit_cost_base)
                    unit_cost_base = Decimal(str(item_data['unit_cost_base']))
                    item_data['cost_impact'] = adjustment_qty * unit_cost_base
                    
                    # Set item currency from header if not specified
                    if not item_data.get('currency_id'):
                        item_data['currency_id'] = adjustment_data.get('currency_id')
                    if not item_data.get('exchange_rate'):
                        item_data['exchange_rate'] = adjustment_data.get('exchange_rate', 1.0)
                    
                    # Calculate foreign currency cost impact if provided
                    if item_data.get('unit_cost_foreign'):
                        unit_cost_foreign = Decimal(str(item_data['unit_cost_foreign']))
                        item_data['cost_impact_foreign'] = adjustment_qty * unit_cost_foreign
                    
                    # Create item
                    adjustment_item = StockAdjustmentItem(**item_data)
                    session.add(adjustment_item)
                    
                    # Update header totals
                    stock_adjustment.total_items += 1
                    stock_adjustment.net_quantity_change += adjustment_qty
                    stock_adjustment.total_cost_impact += item_data['cost_impact']
                    
                    # Record stock transaction for each item
                    try:
                        from modules.inventory_module.services.stock_service import StockService
                        stock_service = StockService()
                        stock_service.record_adjustment_transaction_in_session(
                            session, adjustment_item, stock_adjustment
                        )
                    except (ImportError, AttributeError) as e:
                        print(f"Stock service not available: {e}")
                
                session.flush()
                
                # Record accounting transaction (optional)
                try:
                    self._record_accounting_transaction_in_session(session, stock_adjustment)
                except (ImportError, AttributeError) as e:
                    print(f"Accounting service not available: {e}")
                
                session.commit()
                return stock_adjustment.id
                
            except Exception as e:
                session.rollback()
                raise e
    
    @ExceptionMiddleware.handle_exceptions("StockAdjustmentService")
    def get_all(self, page=1, page_size=100):
        with db_manager.get_session() as session:
            query = session.query(StockAdjustment)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(
                    StockAdjustment.tenant_id == tenant_id,
                    StockAdjustment.is_deleted == False
                )
            
            query = query.order_by(
                StockAdjustment.adjustment_date.desc(),
                StockAdjustment.created_at.desc()
            )
            
            offset = (page - 1) * page_size
            adjustments = query.offset(offset).limit(page_size).all()
            
            # Convert to simple objects with items
            result = []
            for adjustment in adjustments:
                warehouse_name = None
                if adjustment.warehouse_id:
                    warehouse = session.query(Warehouse).filter(
                        Warehouse.id == adjustment.warehouse_id
                    ).first()
                    if warehouse:
                        warehouse_name = warehouse.name
                
                # Get items for this adjustment
                items = []
                for item in adjustment.items:
                    if not item.is_deleted:
                        product = session.query(Product).filter(
                            Product.id == item.product_id
                        ).first()
                        items.append({
                            'id': item.id,
                            'line_no': item.line_no,
                            'product_id': item.product_id,
                            'product_name': product.name if product else None,
                            'batch_number': item.batch_number,
                            'adjustment_qty': item.adjustment_qty,
                            'uom': item.uom,
                            'stock_before': item.stock_before,
                            'stock_after': item.stock_after,
                            'unit_cost_base': item.unit_cost_base,
                            'cost_impact': item.cost_impact,
                            'currency_id': item.currency_id,
                            'unit_cost_foreign': item.unit_cost_foreign,
                            'cost_impact_foreign': item.cost_impact_foreign,
                            'exchange_rate': item.exchange_rate,
                            'reason': item.reason
                        })
                
                adjustment_dict = {
                    'id': adjustment.id,
                    'adjustment_number': adjustment.adjustment_number,
                    'warehouse_id': adjustment.warehouse_id,
                    'warehouse_name': warehouse_name,
                    'adjustment_date': adjustment.adjustment_date,
                    'adjustment_type': adjustment.adjustment_type,
                    'reason': adjustment.reason,
                    'total_items': adjustment.total_items,
                    'net_quantity_change': adjustment.net_quantity_change,
                    'total_cost_impact': adjustment.total_cost_impact,
                    'currency_id': adjustment.currency_id,
                    'exchange_rate': adjustment.exchange_rate,
                    'voucher_id': adjustment.voucher_id,
                    'is_active': adjustment.is_active,
                    'created_at': adjustment.created_at,
                    'created_by': adjustment.created_by,
                    'updated_at': adjustment.updated_at,
                    'updated_by': adjustment.updated_by,
                    'is_deleted': adjustment.is_deleted,
                    'items': items
                }
                result.append(type('StockAdjustment', (), adjustment_dict)())
            
            return result
    
    @ExceptionMiddleware.handle_exceptions("StockAdjustmentService")
    def get_by_id(self, adjustment_id: int):
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            adjustment = session.query(StockAdjustment).filter(
                StockAdjustment.id == adjustment_id,
                StockAdjustment.tenant_id == tenant_id,
                StockAdjustment.is_deleted == False
            ).first()
            
            if not adjustment:
                return None
            
            # Get warehouse name
            warehouse_name = None
            if adjustment.warehouse_id:
                warehouse = session.query(Warehouse).filter(
                    Warehouse.id == adjustment.warehouse_id
                ).first()
                if warehouse:
                    warehouse_name = warehouse.name
            
            # Get items
            items = []
            for item in adjustment.items:
                if not item.is_deleted:
                    product = session.query(Product).filter(
                        Product.id == item.product_id
                    ).first()
                    items.append({
                        'id': item.id,
                        'line_no': item.line_no,
                        'product_id': item.product_id,
                        'product_name': product.name if product else None,
                        'batch_number': item.batch_number,
                        'adjustment_qty': item.adjustment_qty,
                        'uom': item.uom,
                        'stock_before': item.stock_before,
                        'stock_after': item.stock_after,
                        'unit_cost_base': item.unit_cost_base,
                        'cost_impact': item.cost_impact,
                        'currency_id': item.currency_id,
                        'unit_cost_foreign': item.unit_cost_foreign,
                        'cost_impact_foreign': item.cost_impact_foreign,
                        'exchange_rate': item.exchange_rate,
                        'reason': item.reason
                    })
            
            adjustment_dict = {
                'id': adjustment.id,
                'adjustment_number': adjustment.adjustment_number,
                'warehouse_id': adjustment.warehouse_id,
                'warehouse_name': warehouse_name,
                'adjustment_date': adjustment.adjustment_date,
                'adjustment_type': adjustment.adjustment_type,
                'reason': adjustment.reason,
                'total_items': adjustment.total_items,
                'net_quantity_change': adjustment.net_quantity_change,
                'total_cost_impact': adjustment.total_cost_impact,
                'currency_id': adjustment.currency_id,
                'exchange_rate': adjustment.exchange_rate,
                'voucher_id': adjustment.voucher_id,
                'is_active': adjustment.is_active,
                'created_at': adjustment.created_at,
                'created_by': adjustment.created_by,
                'updated_at': adjustment.updated_at,
                'updated_by': adjustment.updated_by,
                'is_deleted': adjustment.is_deleted,
                'items': items
            }
            return type('StockAdjustment', (), adjustment_dict)()
    
    @ExceptionMiddleware.handle_exceptions("StockAdjustmentService")
    def get_total_count(self):
        with db_manager.get_session() as session:
            query = session.query(StockAdjustment)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(
                    StockAdjustment.tenant_id == tenant_id,
                    StockAdjustment.is_deleted == False
                )
            return query.count()
    
    def _get_current_stock(self, session, warehouse_id, product_id, batch_number):
        """Get current stock quantity for a product/batch in warehouse"""
        inventory = session.query(Inventory).filter(
            Inventory.warehouse_id == warehouse_id,
            Inventory.product_id == product_id,
            Inventory.batch_number == (batch_number or '')
        ).first()
        
        return Decimal(str(inventory.quantity)) if inventory else Decimal('0')
    
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
    
    def _record_accounting_transaction_in_session(self, session, stock_adjustment):
        """Record accounting transaction for stock adjustment (optional)"""
        try:
            from modules.account_module.services.payment_service import PaymentService
            payment_service = PaymentService()
            payment_service.record_adjustment_transaction_in_session(
                session,
                stock_adjustment.id,
                stock_adjustment.adjustment_number,
                float(stock_adjustment.total_cost_impact),
                stock_adjustment.adjustment_date
            )
        except ImportError:
            pass  # Account module not available
