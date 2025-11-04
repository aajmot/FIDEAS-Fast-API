from core.database.connection import db_manager
from modules.inventory_module.models.stock_transfer_entity import StockTransfer, StockTransferItem
from modules.inventory_module.models.entities import Product, Warehouse, Inventory
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware
from datetime import datetime
from decimal import Decimal


class StockTransferService:
    
    @ExceptionMiddleware.handle_exceptions("StockTransferService")
    def create(self, transfer_data: dict):
        with db_manager.get_session() as session:
            try:
                tenant_id = session_manager.get_current_tenant_id()
                username = session_manager.get_current_username()
                
                # Extract items from transfer_data
                items_data = transfer_data.pop('items', [])
                if not items_data:
                    raise ValueError("At least one transfer item is required")
                
                # Validate warehouses are different
                if transfer_data['from_warehouse_id'] == transfer_data['to_warehouse_id']:
                    raise ValueError("Source and destination warehouses must be different")
                
                # Set header-level fields
                transfer_data['tenant_id'] = tenant_id
                transfer_data['created_by'] = username
                transfer_data['updated_by'] = username
                
                # Set currency_id if not provided
                if not transfer_data.get('currency_id'):
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
                        transfer_data['currency_id'] = currency.id
                
                # Set exchange_rate to 1 for base currency
                if not transfer_data.get('exchange_rate'):
                    transfer_data['exchange_rate'] = 1.0
                
                # Initialize totals
                transfer_data['total_items'] = 0
                transfer_data['total_quantity'] = 0
                transfer_data['total_cost_base'] = 0
                
                # Create header record
                stock_transfer = StockTransfer(**transfer_data)
                session.add(stock_transfer)
                session.flush()  # Get the transfer_id
                
                # Create line items and calculate totals
                for item_data in items_data:
                    item_data['tenant_id'] = tenant_id
                    item_data['transfer_id'] = stock_transfer.id
                    item_data['created_by'] = username
                    item_data['updated_by'] = username
                    
                    from_warehouse_id = transfer_data['from_warehouse_id']
                    to_warehouse_id = transfer_data['to_warehouse_id']
                    product_id = item_data['product_id']
                    batch_number = item_data.get('batch_number', '')
                    
                    # Get from_stock_before if not provided
                    if item_data.get('from_stock_before') is None:
                        from_stock = self._get_current_stock(session, from_warehouse_id, product_id, batch_number)
                        item_data['from_stock_before'] = from_stock
                    else:
                        from_stock = Decimal(str(item_data['from_stock_before']))
                    
                    # Get to_stock_before if not provided
                    if item_data.get('to_stock_before') is None:
                        to_stock = self._get_current_stock(session, to_warehouse_id, product_id, batch_number)
                        item_data['to_stock_before'] = to_stock
                    else:
                        to_stock = Decimal(str(item_data['to_stock_before']))
                    
                    # Calculate stock_after
                    quantity = Decimal(str(item_data['quantity']))
                    item_data['from_stock_after'] = from_stock - quantity
                    item_data['to_stock_after'] = to_stock + quantity
                    
                    # Validate sufficient stock in source warehouse
                    if item_data['from_stock_after'] < 0:
                        product = session.query(Product).filter(Product.id == product_id).first()
                        product_name = product.name if product else f"Product ID {product_id}"
                        raise ValueError(f"Insufficient stock for {product_name}. Available: {from_stock}, Requested: {quantity}")
                    
                    # Calculate total_cost_base (quantity * unit_cost_base)
                    unit_cost_base = Decimal(str(item_data['unit_cost_base']))
                    item_data['total_cost_base'] = quantity * unit_cost_base
                    
                    # Set item currency from header if not specified
                    if not item_data.get('currency_id'):
                        item_data['currency_id'] = transfer_data.get('currency_id')
                    if not item_data.get('exchange_rate'):
                        item_data['exchange_rate'] = transfer_data.get('exchange_rate', 1.0)
                    
                    # Calculate foreign currency total if provided
                    if item_data.get('unit_cost_foreign'):
                        unit_cost_foreign = Decimal(str(item_data['unit_cost_foreign']))
                        item_data['total_cost_foreign'] = quantity * unit_cost_foreign
                    
                    # Create item
                    transfer_item = StockTransferItem(**item_data)
                    session.add(transfer_item)
                    
                    # Update header totals
                    stock_transfer.total_items += 1
                    stock_transfer.total_quantity += quantity
                    stock_transfer.total_cost_base += item_data['total_cost_base']
                    
                    # Record stock transactions only if status is APPROVED or COMPLETED
                    if transfer_data.get('status') in ['APPROVED', 'COMPLETED']:
                        try:
                            from modules.inventory_module.services.stock_service import StockService
                            stock_service = StockService()
                            stock_service.record_transfer_transaction_in_session(
                                session, transfer_item, stock_transfer
                            )
                        except (ImportError, AttributeError) as e:
                            print(f"Stock service not available: {e}")
                
                session.flush()
                
                # Record accounting transactions (optional)
                try:
                    self._record_accounting_transaction_in_session(session, stock_transfer)
                except (ImportError, AttributeError) as e:
                    print(f"Accounting service not available: {e}")
                
                session.commit()
                return stock_transfer.id
                
            except Exception as e:
                session.rollback()
                raise e
    
    @ExceptionMiddleware.handle_exceptions("StockTransferService")
    def get_all(self, page=1, page_size=100, status=None):
        with db_manager.get_session() as session:
            query = session.query(StockTransfer)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(
                    StockTransfer.tenant_id == tenant_id,
                    StockTransfer.is_deleted == False
                )
            
            # Filter by status if provided
            if status:
                query = query.filter(StockTransfer.status == status)
            
            query = query.order_by(
                StockTransfer.transfer_date.desc(),
                StockTransfer.created_at.desc()
            )
            
            offset = (page - 1) * page_size
            transfers = query.offset(offset).limit(page_size).all()
            
            # Convert to simple objects with items
            result = []
            for transfer in transfers:
                from_warehouse_name = None
                to_warehouse_name = None
                
                if transfer.from_warehouse_id:
                    from_wh = session.query(Warehouse).filter(
                        Warehouse.id == transfer.from_warehouse_id
                    ).first()
                    if from_wh:
                        from_warehouse_name = from_wh.name
                
                if transfer.to_warehouse_id:
                    to_wh = session.query(Warehouse).filter(
                        Warehouse.id == transfer.to_warehouse_id
                    ).first()
                    if to_wh:
                        to_warehouse_name = to_wh.name
                
                # Get items for this transfer
                items = []
                for item in transfer.items:
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
                            'quantity': item.quantity,
                            'uom': item.uom,
                            'from_stock_before': item.from_stock_before,
                            'from_stock_after': item.from_stock_after,
                            'to_stock_before': item.to_stock_before,
                            'to_stock_after': item.to_stock_after,
                            'unit_cost_base': item.unit_cost_base,
                            'total_cost_base': item.total_cost_base,
                            'currency_id': item.currency_id,
                            'unit_cost_foreign': item.unit_cost_foreign,
                            'total_cost_foreign': item.total_cost_foreign,
                            'exchange_rate': item.exchange_rate,
                            'reason': item.reason
                        })
                
                transfer_dict = {
                    'id': transfer.id,
                    'transfer_number': transfer.transfer_number,
                    'from_warehouse_id': transfer.from_warehouse_id,
                    'from_warehouse_name': from_warehouse_name,
                    'to_warehouse_id': transfer.to_warehouse_id,
                    'to_warehouse_name': to_warehouse_name,
                    'transfer_date': transfer.transfer_date,
                    'transfer_type': transfer.transfer_type,
                    'reason': transfer.reason,
                    'total_items': transfer.total_items,
                    'total_quantity': transfer.total_quantity,
                    'total_cost_base': transfer.total_cost_base,
                    'currency_id': transfer.currency_id,
                    'exchange_rate': transfer.exchange_rate,
                    'status': transfer.status,
                    'approval_request_id': transfer.approval_request_id,
                    'approved_by': transfer.approved_by,
                    'approved_at': transfer.approved_at,
                    'from_voucher_id': transfer.from_voucher_id,
                    'to_voucher_id': transfer.to_voucher_id,
                    'is_active': transfer.is_active,
                    'created_at': transfer.created_at,
                    'created_by': transfer.created_by,
                    'updated_at': transfer.updated_at,
                    'updated_by': transfer.updated_by,
                    'is_deleted': transfer.is_deleted,
                    'items': items
                }
                result.append(type('StockTransfer', (), transfer_dict)())
            
            # Get total count for pagination
            total_count = query.count()
            
            return {
                'total': total_count,
                'skip': offset,
                'limit': page_size,
                'data': result
            }
    
    @ExceptionMiddleware.handle_exceptions("StockTransferService")
    def get_by_id(self, transfer_id: int):
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            transfer = session.query(StockTransfer).filter(
                StockTransfer.id == transfer_id,
                StockTransfer.tenant_id == tenant_id,
                StockTransfer.is_deleted == False
            ).first()
            
            if not transfer:
                return None
            
            # Get warehouse names
            from_warehouse_name = None
            to_warehouse_name = None
            
            if transfer.from_warehouse_id:
                from_wh = session.query(Warehouse).filter(
                    Warehouse.id == transfer.from_warehouse_id
                ).first()
                if from_wh:
                    from_warehouse_name = from_wh.name
            
            if transfer.to_warehouse_id:
                to_wh = session.query(Warehouse).filter(
                    Warehouse.id == transfer.to_warehouse_id
                ).first()
                if to_wh:
                    to_warehouse_name = to_wh.name
            
            # Get items
            items = []
            for item in transfer.items:
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
                        'quantity': item.quantity,
                        'uom': item.uom,
                        'from_stock_before': item.from_stock_before,
                        'from_stock_after': item.from_stock_after,
                        'to_stock_before': item.to_stock_before,
                        'to_stock_after': item.to_stock_after,
                        'unit_cost_base': item.unit_cost_base,
                        'total_cost_base': item.total_cost_base,
                        'currency_id': item.currency_id,
                        'unit_cost_foreign': item.unit_cost_foreign,
                        'total_cost_foreign': item.total_cost_foreign,
                        'exchange_rate': item.exchange_rate,
                        'reason': item.reason
                    })
            
            transfer_dict = {
                'id': transfer.id,
                'transfer_number': transfer.transfer_number,
                'from_warehouse_id': transfer.from_warehouse_id,
                'from_warehouse_name': from_warehouse_name,
                'to_warehouse_id': transfer.to_warehouse_id,
                'to_warehouse_name': to_warehouse_name,
                'transfer_date': transfer.transfer_date,
                'transfer_type': transfer.transfer_type,
                'reason': transfer.reason,
                'total_items': transfer.total_items,
                'total_quantity': transfer.total_quantity,
                'total_cost_base': transfer.total_cost_base,
                'currency_id': transfer.currency_id,
                'exchange_rate': transfer.exchange_rate,
                'status': transfer.status,
                'approval_request_id': transfer.approval_request_id,
                'approved_by': transfer.approved_by,
                'approved_at': transfer.approved_at,
                'from_voucher_id': transfer.from_voucher_id,
                'to_voucher_id': transfer.to_voucher_id,
                'is_active': transfer.is_active,
                'created_at': transfer.created_at,
                'created_by': transfer.created_by,
                'updated_at': transfer.updated_at,
                'updated_by': transfer.updated_by,
                'is_deleted': transfer.is_deleted,
                'items': items
            }
            return type('StockTransfer', (), transfer_dict)()
    
    @ExceptionMiddleware.handle_exceptions("StockTransferService")
    def get_total_count(self, status=None):
        with db_manager.get_session() as session:
            query = session.query(StockTransfer)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(
                    StockTransfer.tenant_id == tenant_id,
                    StockTransfer.is_deleted == False
                )
            if status:
                query = query.filter(StockTransfer.status == status)
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
    
    def _record_accounting_transaction_in_session(self, session, stock_transfer):
        """Record accounting transaction for stock transfer (optional)"""
        try:
            from modules.account_module.services.payment_service import PaymentService
            payment_service = PaymentService()
            payment_service.record_transfer_transaction_in_session(
                session,
                stock_transfer.id,
                stock_transfer.transfer_number,
                float(stock_transfer.total_cost_base),
                stock_transfer.transfer_date
            )
        except ImportError:
            pass  # Account module not available
