from core.database.connection import db_manager
from modules.inventory_module.models.stock_transfer_entity import StockTransfer, StockTransferItem
from modules.inventory_module.models.entities import Product, Warehouse, Inventory
from core.shared.middleware.exception_handler import ExceptionMiddleware
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any


class StockTransferService:
    
    @ExceptionMiddleware.handle_exceptions("StockTransferService")
    def create(self, transfer_data, tenant_id: int, username: str) -> int:
        """Create stock transfer with proper validation and inventory updates"""
        with db_manager.get_session() as session:
            try:
                # Convert to dict if it's a Pydantic model
                if hasattr(transfer_data, 'dict'):
                    transfer_dict = transfer_data.dict()
                else:
                    transfer_dict = transfer_data
                
                # Extract items from transfer_data
                items_data = transfer_dict.pop('items', [])
                if not items_data:
                    raise ValueError("At least one transfer item is required")
                
                # Validate warehouses exist and are different
                self._validate_warehouses(session, transfer_dict['from_warehouse_id'], 
                                        transfer_dict['to_warehouse_id'], tenant_id)
                
                # Generate transfer number if not provided
                if not transfer_dict.get('transfer_number'):
                    transfer_dict['transfer_number'] = self._generate_transfer_number(session, tenant_id)
                
                # Set defaults
                transfer_dict['tenant_id'] = tenant_id
                transfer_dict['created_by'] = username
                transfer_dict['updated_by'] = username
                transfer_dict['transfer_date'] = transfer_dict.get('transfer_date') or datetime.utcnow()
                transfer_dict['exchange_rate'] = transfer_dict.get('exchange_rate', 1.0)
                
                # Initialize totals
                transfer_dict['total_items'] = len(items_data)
                transfer_dict['total_quantity'] = 0
                transfer_dict['total_cost_base'] = 0
                
                # Create header record
                stock_transfer = StockTransfer(**transfer_dict)
                session.add(stock_transfer)
                session.flush()  # Get the transfer_id
                
                # Process line items
                for idx, item_data in enumerate(items_data):
                    # Set item defaults
                    item_data['tenant_id'] = tenant_id
                    item_data['transfer_id'] = stock_transfer.id
                    item_data['created_by'] = username
                    item_data['updated_by'] = username
                    item_data['line_no'] = item_data.get('line_no', idx + 1)
                    
                    # Validate product exists
                    product = session.query(Product).filter(
                        Product.id == item_data['product_id'],
                        Product.tenant_id == tenant_id,
                        Product.is_deleted == False
                    ).first()
                    if not product:
                        raise ValueError(f"Product with ID {item_data['product_id']} not found")
                    
                    # Get current stock levels
                    from_stock = self._get_current_stock(session, transfer_dict['from_warehouse_id'], 
                                                       item_data['product_id'], item_data.get('batch_number'))
                    to_stock = self._get_current_stock(session, transfer_dict['to_warehouse_id'], 
                                                     item_data['product_id'], item_data.get('batch_number'))
                    
                    quantity = Decimal(str(item_data['quantity']))
                    
                    # Set stock before/after
                    item_data['from_stock_before'] = from_stock
                    item_data['from_stock_after'] = from_stock - quantity
                    item_data['to_stock_before'] = to_stock
                    item_data['to_stock_after'] = to_stock + quantity
                    
                    # Validate sufficient stock
                    if item_data['from_stock_after'] < 0:
                        raise ValueError(f"Insufficient stock for {product.name}. Available: {from_stock}, Requested: {quantity}")
                    
                    # Calculate costs
                    unit_cost_base = Decimal(str(item_data['unit_cost_base']))
                    item_data['total_cost_base'] = quantity * unit_cost_base
                    
                    if item_data.get('unit_cost_foreign'):
                        unit_cost_foreign = Decimal(str(item_data['unit_cost_foreign']))
                        item_data['total_cost_foreign'] = quantity * unit_cost_foreign
                    
                    # Create item
                    transfer_item = StockTransferItem(**item_data)
                    session.add(transfer_item)
                    
                    # Update header totals
                    stock_transfer.total_quantity += quantity
                    stock_transfer.total_cost_base += item_data['total_cost_base']
                    
                    # Update inventory if status is APPROVED or COMPLETED
                    if transfer_dict.get('status') in ['APPROVED', 'COMPLETED']:
                        self._update_inventory(session, transfer_item, stock_transfer, tenant_id)
                
                session.commit()
                return stock_transfer.id
                
            except Exception as e:
                session.rollback()
                raise e
    
    @ExceptionMiddleware.handle_exceptions("StockTransferService")
    def get_all(self, tenant_id: int, page: int = 1, page_size: int = 100, status: str = None) -> Dict[str, Any]:
        with db_manager.get_session() as session:
            query = session.query(StockTransfer).filter(
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
    def get_by_id(self, transfer_id: int, tenant_id: int):
        with db_manager.get_session() as session:
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
    def get_total_count(self, tenant_id: int, status: str = None) -> int:
        with db_manager.get_session() as session:
            query = session.query(StockTransfer).filter(
                StockTransfer.tenant_id == tenant_id,
                StockTransfer.is_deleted == False
            )
            if status:
                query = query.filter(StockTransfer.status == status)
            return query.count()
    
    def _validate_warehouses(self, session, from_warehouse_id: int, to_warehouse_id: int, tenant_id: int):
        """Validate warehouses exist and are different"""
        if from_warehouse_id == to_warehouse_id:
            raise ValueError("Source and destination warehouses must be different")
        
        from_warehouse = session.query(Warehouse).filter(
            Warehouse.id == from_warehouse_id,
            Warehouse.tenant_id == tenant_id,
            Warehouse.is_active == True
        ).first()
        
        to_warehouse = session.query(Warehouse).filter(
            Warehouse.id == to_warehouse_id,
            Warehouse.tenant_id == tenant_id,
            Warehouse.is_active == True
        ).first()
        
        if not from_warehouse:
            raise ValueError(f"Source warehouse with ID {from_warehouse_id} not found")
        if not to_warehouse:
            raise ValueError(f"Destination warehouse with ID {to_warehouse_id} not found")
    
    def _generate_transfer_number(self, session, tenant_id: int) -> str:
        """Generate unique transfer number"""
        now = datetime.now()
        prefix = f"ST-{tenant_id}-{now.strftime('%Y%m%d')}"
        
        # Get last transfer number for today
        last_transfer = session.query(StockTransfer).filter(
            StockTransfer.transfer_number.like(f"{prefix}%"),
            StockTransfer.tenant_id == tenant_id
        ).order_by(StockTransfer.id.desc()).first()
        
        if last_transfer:
            try:
                seq = int(last_transfer.transfer_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        
        return f"{prefix}-{seq:04d}"
    
    def _get_current_stock(self, session, warehouse_id: int, product_id: int, batch_number: str = None) -> Decimal:
        """Get current stock quantity for a product/batch in warehouse"""
        from modules.inventory_module.models.warehouse_entity import StockByLocation
        
        stock = session.query(StockByLocation).filter(
            StockByLocation.warehouse_id == warehouse_id,
            StockByLocation.product_id == product_id
        ).first()
        
        return Decimal(str(stock.quantity)) if stock else Decimal('0')
    
    def _update_inventory(self, session, transfer_item: StockTransferItem, stock_transfer: StockTransfer, tenant_id: int):
        """Update inventory for approved/completed transfers"""
        from modules.inventory_module.models.warehouse_entity import StockByLocation
        
        # Update source warehouse inventory (decrease)
        from_stock = session.query(StockByLocation).filter(
            StockByLocation.warehouse_id == stock_transfer.from_warehouse_id,
            StockByLocation.product_id == transfer_item.product_id,
            StockByLocation.tenant_id == tenant_id
        ).first()
        
        if from_stock:
            from_stock.quantity -= transfer_item.quantity
            from_stock.available_quantity -= transfer_item.quantity
            from_stock.updated_at = datetime.utcnow()
        
        # Update destination warehouse inventory (increase)
        to_stock = session.query(StockByLocation).filter(
            StockByLocation.warehouse_id == stock_transfer.to_warehouse_id,
            StockByLocation.product_id == transfer_item.product_id,
            StockByLocation.tenant_id == tenant_id
        ).first()
        
        if to_stock:
            to_stock.quantity += transfer_item.quantity
            to_stock.available_quantity += transfer_item.quantity
            to_stock.updated_at = datetime.utcnow()
        else:
            # Create new stock record for destination
            to_stock = StockByLocation(
                tenant_id=tenant_id,
                warehouse_id=stock_transfer.to_warehouse_id,
                product_id=transfer_item.product_id,
                quantity=transfer_item.quantity,
                available_quantity=transfer_item.quantity
            )
            session.add(to_stock)
