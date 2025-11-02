from core.database.connection import db_manager
from modules.inventory_module.models.stock_entity import StockTransaction, StockBalance
from modules.inventory_module.models.entities import Product
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware
from sqlalchemy import func

class StockService:
    @ExceptionMiddleware.handle_exceptions("StockService")
    def record_purchase_transaction(self, purchase_order, items):
        """Record stock IN transactions for purchase order"""
        with db_manager.get_session() as session:
            self.record_purchase_transaction_in_session(session, purchase_order, items)
            session.commit()
    
    def record_purchase_transaction_in_session(self, session, purchase_order, items):
        """Record stock IN transactions for purchase order within existing session"""
        for item in items:
            # Create stock transaction
            transaction = StockTransaction(
                product_id=item.product_id,
                transaction_type='IN',
                transaction_source='PURCHASE',
                reference_id=purchase_order.id,
                reference_number=purchase_order.po_number,
                batch_number=getattr(item, 'batch_number', ''),
                quantity=item.quantity,
                unit_price=item.unit_price,
                tenant_id=session_manager.get_current_tenant_id(),
                created_by=session_manager.get_current_username()
            )
            session.add(transaction)
            
            # Update stock balance
            self._update_stock_balance(session, item.product_id, 
                                     getattr(item, 'batch_number', ''), 
                                     float(item.quantity), float(item.unit_price), 'IN')
    
    @ExceptionMiddleware.handle_exceptions("StockService")
    def record_sales_transaction(self, sales_order, items):
        """Record stock OUT transactions for sales order"""
        with db_manager.get_session() as session:
            self.record_sales_transaction_in_session(session, sales_order, items)
            session.commit()
    
    def record_sales_transaction_in_session(self, session, sales_order, items):
        """Record stock OUT transactions for sales order within existing session"""
        for item in items:
            # Create stock transaction
            transaction = StockTransaction(
                product_id=item.product_id,
                transaction_type='OUT',
                transaction_source='SALES',
                reference_id=sales_order.id,
                reference_number=sales_order.order_number,
                batch_number=getattr(item, 'batch_number', ''),
                quantity=item.quantity,
                unit_price=item.unit_price,
                tenant_id=session_manager.get_current_tenant_id(),
                created_by=session_manager.get_current_username()
            )
            session.add(transaction)
            
            # Update stock balance
            self._update_stock_balance(session, item.product_id, 
                                     getattr(item, 'batch_number', ''), 
                                     float(item.quantity), float(item.unit_price), 'OUT')
    
    def _update_stock_balance(self, session, product_id, batch_number, quantity, unit_price, transaction_type):
        """Update stock balance for a product"""
        # Find existing balance
        balance = session.query(StockBalance).filter(
            StockBalance.product_id == product_id,
            StockBalance.batch_number == batch_number,
            StockBalance.tenant_id == session_manager.get_current_tenant_id()
        ).first()
        
        if not balance:
            # Create new balance record
            balance = StockBalance(
                product_id=product_id,
                batch_number=batch_number,
                tenant_id=session_manager.get_current_tenant_id()
            )
            session.add(balance)
        
        # Update quantities
        if transaction_type == 'IN':
            # Calculate new average cost
            current_total_qty = float(balance.total_quantity or 0)
            current_avg_cost = float(balance.average_cost or 0)
            current_available_qty = float(balance.available_quantity or 0)
            
            current_value = current_total_qty * current_avg_cost
            new_value = quantity * unit_price
            new_total_qty = current_total_qty + quantity
            
            if new_total_qty > 0:
                balance.average_cost = (current_value + new_value) / new_total_qty
            
            balance.total_quantity = new_total_qty
            balance.available_quantity = current_available_qty + quantity
        
        elif transaction_type == 'OUT':
            current_total_qty = float(balance.total_quantity or 0)
            current_available_qty = float(balance.available_quantity or 0)
            
            balance.total_quantity = current_total_qty - quantity
            balance.available_quantity = current_available_qty - quantity
        
        balance.last_updated = func.now()
    
    @ExceptionMiddleware.handle_exceptions("StockService")
    def get_stock_transactions(self, product_id=None, limit=100):
        """Get stock transactions with optional product filter"""
        with db_manager.get_session() as session:
            query = session.query(StockTransaction).join(Product)
            
            if product_id:
                query = query.filter(StockTransaction.product_id == product_id)
            
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(StockTransaction.tenant_id == tenant_id)
            
            return query.order_by(StockTransaction.created_at.desc()).limit(limit).all()
    
    @ExceptionMiddleware.handle_exceptions("StockService")
    def get_stock_balances(self, product_id=None):
        """Get current stock balances"""
        from sqlalchemy.orm import joinedload
        
        with db_manager.get_session() as session:
            query = session.query(StockBalance).options(joinedload(StockBalance.product)).join(Product)
            
            if product_id:
                query = query.filter(StockBalance.product_id == product_id)
            
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(StockBalance.tenant_id == tenant_id)
            
            return query.filter(StockBalance.total_quantity > 0).all()
    
    @ExceptionMiddleware.handle_exceptions("StockService")
    def record_waste_transaction(self, product_waste):
        """Record stock OUT transaction for product waste"""
        with db_manager.get_session() as session:
            self.record_waste_transaction_in_session(session, product_waste)
            session.commit()
    
    def record_waste_transaction_in_session(self, session, product_waste):
        """Record stock OUT transaction for product waste within existing session"""
        # Create stock transaction
        transaction = StockTransaction(
            product_id=product_waste.product_id,
            transaction_type='OUT',
            transaction_source='WASTE',
            reference_id=product_waste.id,
            reference_number=product_waste.waste_number,
            batch_number=product_waste.batch_number or '',
            quantity=product_waste.quantity,
            unit_price=product_waste.unit_cost,
            tenant_id=session_manager.get_current_tenant_id(),
            created_by=session_manager.get_current_username()
        )
        session.add(transaction)
        
        # Update stock balance
        self._update_stock_balance(session, product_waste.product_id, 
                                 product_waste.batch_number or '', 
                                 float(product_waste.quantity), 
                                 float(product_waste.unit_cost), 'OUT')
    
    def reverse_sales_transaction_in_session(self, session, sales_order, items):
        """Reverse stock OUT transactions for sales order within existing session"""
        for item in items:
            # Create reverse stock transaction (IN to reverse OUT)
            transaction = StockTransaction(
                product_id=item.product_id,
                transaction_type='IN',
                transaction_source='SALES_REVERSAL',
                reference_id=sales_order.id,
                reference_number=f"REV-{sales_order.order_number}",
                batch_number=getattr(item, 'batch_number', ''),
                quantity=item.quantity,
                unit_price=item.unit_price,
                tenant_id=session_manager.get_current_tenant_id(),
                created_by=session_manager.get_current_username()
            )
            session.add(transaction)
            
            # Update stock balance (reverse OUT with IN)
            self._update_stock_balance(session, item.product_id, 
                                     getattr(item, 'batch_number', ''), 
                                     float(item.quantity), float(item.unit_price), 'IN')
    
    def reverse_purchase_transaction_in_session(self, session, purchase_order, items):
        """Reverse stock IN transactions for purchase order within existing session"""
        for item in items:
            # Create reverse stock transaction (OUT to reverse IN)
            transaction = StockTransaction(
                product_id=item.product_id,
                transaction_type='OUT',
                transaction_source='PURCHASE_REVERSAL',
                reference_id=purchase_order.id,
                reference_number=f"REV-{purchase_order.po_number}",
                batch_number=getattr(item, 'batch_number', ''),
                quantity=item.quantity,
                unit_price=item.unit_price,
                tenant_id=session_manager.get_current_tenant_id(),
                created_by=session_manager.get_current_username()
            )
            session.add(transaction)
            
            # Update stock balance (reverse IN with OUT)
            self._update_stock_balance(session, item.product_id, 
                                     getattr(item, 'batch_number', ''), 
                                     float(item.quantity), float(item.unit_price), 'OUT')
    
    @ExceptionMiddleware.handle_exceptions("StockService")
    def get_product_stock_summary(self):
        """Get stock summary by product"""
        with db_manager.get_session() as session:
            query = session.query(
                Product.id,
                Product.name,
                func.sum(StockBalance.total_quantity).label('total_stock'),
                func.sum(StockBalance.available_quantity).label('available_stock'),
                func.avg(StockBalance.average_cost).label('avg_cost')
            ).join(StockBalance).filter(
                StockBalance.tenant_id == session_manager.get_current_tenant_id()
            ).group_by(Product.id, Product.name)
            
            return query.all()