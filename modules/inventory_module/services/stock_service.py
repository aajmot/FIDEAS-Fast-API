from core.database.connection import db_manager
from modules.inventory_module.models.stock_entity import StockTransaction, StockBalance
from modules.inventory_module.models.entities import Product
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware
from sqlalchemy import func
from decimal import Decimal

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
    
    def record_purchase_invoice_transaction_in_session(self, session, invoice, items):
        """Record stock IN transactions for purchase invoice within existing session"""
        for item in items:
            paid_qty = float(item.quantity)
            free_qty = float(getattr(item, 'free_quantity', 0) or 0)
            
            # Create separate stock transaction for paid quantity
            if paid_qty > 0:
                paid_transaction = StockTransaction(
                    product_id=item.product_id,
                    transaction_type='IN',
                    transaction_source='PURCHASE_INVOICE',
                    reference_id=invoice.id,
                    reference_number=invoice.invoice_number,
                    batch_number=getattr(item, 'batch_number', '') or '',
                    quantity=paid_qty,
                    unit_price=item.unit_price_base,
                    tenant_id=session_manager.get_current_tenant_id(),
                    created_by=session_manager.get_current_username()
                )
                session.add(paid_transaction)
                
                # Update stock balance for paid quantity
                self._update_stock_balance(session, item.product_id, 
                                         getattr(item, 'batch_number', '') or '', 
                                         paid_qty, float(item.unit_price_base), 'IN')
            
            # Create separate stock transaction for free quantity
            if free_qty > 0:
                free_transaction = StockTransaction(
                    product_id=item.product_id,
                    transaction_type='IN',
                    transaction_source='PURCHASE_INVOICE_FREE',
                    reference_id=invoice.id,
                    reference_number=f"{invoice.invoice_number}-FREE",
                    batch_number=getattr(item, 'batch_number', '') or '',
                    quantity=free_qty,
                    unit_price=item.unit_price_base,  # Free items valued at purchase price for inventory
                    tenant_id=session_manager.get_current_tenant_id(),
                    created_by=session_manager.get_current_username()
                )
                session.add(free_transaction)
                
                # Update stock balance for free quantity
                self._update_stock_balance(session, item.product_id, 
                                         getattr(item, 'batch_number', '') or '', 
                                         free_qty, float(item.unit_price_base), 'IN')
    
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
    
    def record_waste_transaction_in_session(self, session, waste_item, waste_header=None):
        """Record stock OUT transaction for product waste item within existing session"""
        # Create stock transaction (use base currency cost)
        transaction = StockTransaction(
            product_id=waste_item.product_id,
            transaction_type='OUT',
            transaction_source='WASTE',
            reference_id=waste_item.waste_id if hasattr(waste_item, 'waste_id') else waste_item.id,
            reference_number=waste_header.waste_number if waste_header else getattr(waste_item, 'waste_number', ''),
            batch_number=waste_item.batch_number or '',
            quantity=waste_item.quantity,
            unit_price=waste_item.unit_cost_base,  # Use base currency cost
            tenant_id=session_manager.get_current_tenant_id(),
            created_by=session_manager.get_current_username()
        )
        session.add(transaction)
        
        # Update stock balance
        self._update_stock_balance(session, waste_item.product_id, 
                                 waste_item.batch_number or '', 
                                 float(waste_item.quantity), 
                                 float(waste_item.unit_cost_base), 'OUT')  # Use base currency cost
    
    def record_adjustment_transaction_in_session(self, session, adjustment_item, adjustment_header=None):
        """Record stock transaction for adjustment item within existing session"""
        # Determine transaction type based on adjustment_qty (+ve = IN, -ve = OUT)
        adjustment_qty = float(adjustment_item.adjustment_qty)
        transaction_type = 'IN' if adjustment_qty > 0 else 'OUT'
        abs_quantity = abs(adjustment_qty)
        
        # Create stock transaction
        transaction = StockTransaction(
            product_id=adjustment_item.product_id,
            transaction_type=transaction_type,
            transaction_source='ADJUSTMENT',
            reference_id=adjustment_item.adjustment_id if hasattr(adjustment_item, 'adjustment_id') else adjustment_item.id,
            reference_number=adjustment_header.adjustment_number if adjustment_header else getattr(adjustment_item, 'adjustment_number', ''),
            batch_number=adjustment_item.batch_number or '',
            quantity=abs_quantity,
            unit_price=adjustment_item.unit_cost_base,
            tenant_id=session_manager.get_current_tenant_id(),
            created_by=session_manager.get_current_username()
        )
        session.add(transaction)
        
        # Update stock balance
        self._update_stock_balance(session, adjustment_item.product_id, 
                                 adjustment_item.batch_number or '', 
                                 abs_quantity, 
                                 float(adjustment_item.unit_cost_base), 
                                 transaction_type)
    
    def record_transfer_transaction_in_session(self, session, transfer_item, transfer_header=None):
        """Record stock transactions for transfer item within existing session"""
        # Create OUT transaction from source warehouse
        out_transaction = StockTransaction(
            product_id=transfer_item.product_id,
            transaction_type='OUT',
            transaction_source='TRANSFER_OUT',
            reference_id=transfer_item.transfer_id if hasattr(transfer_item, 'transfer_id') else transfer_item.id,
            reference_number=transfer_header.transfer_number if transfer_header else getattr(transfer_item, 'transfer_number', ''),
            batch_number=transfer_item.batch_number or '',
            quantity=transfer_item.quantity,
            unit_price=transfer_item.unit_cost_base,
            tenant_id=session_manager.get_current_tenant_id(),
            created_by=session_manager.get_current_username()
        )
        session.add(out_transaction)
        
        # Create IN transaction to destination warehouse
        in_transaction = StockTransaction(
            product_id=transfer_item.product_id,
            transaction_type='IN',
            transaction_source='TRANSFER_IN',
            reference_id=transfer_item.transfer_id if hasattr(transfer_item, 'transfer_id') else transfer_item.id,
            reference_number=transfer_header.transfer_number if transfer_header else getattr(transfer_item, 'transfer_number', ''),
            batch_number=transfer_item.batch_number or '',
            quantity=transfer_item.quantity,
            unit_price=transfer_item.unit_cost_base,
            tenant_id=session_manager.get_current_tenant_id(),
            created_by=session_manager.get_current_username()
        )
        session.add(in_transaction)
        
        # Update stock balances for both warehouses
        # Note: This would need warehouse context which should be passed from transfer service
        # For now, stock balance updates are handled in the transfer service
    
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
    
    def reverse_purchase_invoice_transaction_in_session(self, session, invoice, items):
        """Reverse stock IN transactions for purchase invoice within existing session"""
        for item in items:
            paid_qty = float(item.quantity)
            free_qty = float(getattr(item, 'free_quantity', 0) or 0)
            
            # Reverse paid quantity transaction
            if paid_qty > 0:
                paid_reversal = StockTransaction(
                    product_id=item.product_id,
                    transaction_type='OUT',
                    transaction_source='PURCHASE_INVOICE_REVERSAL',
                    reference_id=invoice.id,
                    reference_number=f"REV-{invoice.invoice_number}",
                    batch_number=getattr(item, 'batch_number', '') or '',
                    quantity=paid_qty,
                    unit_price=item.unit_price_base,
                    tenant_id=session_manager.get_current_tenant_id(),
                    created_by=session_manager.get_current_username()
                )
                session.add(paid_reversal)
                
                # Update stock balance (reverse IN with OUT)
                self._update_stock_balance(session, item.product_id, 
                                         getattr(item, 'batch_number', '') or '', 
                                         paid_qty, float(item.unit_price_base), 'OUT')
            
            # Reverse free quantity transaction
            if free_qty > 0:
                free_reversal = StockTransaction(
                    product_id=item.product_id,
                    transaction_type='OUT',
                    transaction_source='PURCHASE_INVOICE_FREE_REVERSAL',
                    reference_id=invoice.id,
                    reference_number=f"REV-{invoice.invoice_number}-FREE",
                    batch_number=getattr(item, 'batch_number', '') or '',
                    quantity=free_qty,
                    unit_price=item.unit_price_base,
                    tenant_id=session_manager.get_current_tenant_id(),
                    created_by=session_manager.get_current_username()
                )
                session.add(free_reversal)
                
                # Update stock balance for free quantity reversal
                self._update_stock_balance(session, item.product_id, 
                                         getattr(item, 'batch_number', '') or '', 
                                         free_qty, float(item.unit_price_base), 'OUT')
    
    def record_sales_invoice_transaction_in_session(self, session, tenant_id, invoice_id, invoice_number, invoice_date, items_data, username):
        """Record stock OUT transactions for sales invoice within existing session"""
        from modules.inventory_module.models.sales_invoice_entity import SalesInvoiceItem
        
        # Get invoice items
        items = session.query(SalesInvoiceItem).filter(
            SalesInvoiceItem.invoice_id == invoice_id,
            SalesInvoiceItem.tenant_id == tenant_id
        ).all()
        
        for item in items:
            paid_qty = float(item.quantity)
            free_qty = float(getattr(item, 'free_quantity', 0) or 0)
            
            # Create separate stock transaction for paid quantity
            if paid_qty > 0:
                paid_transaction = StockTransaction(
                    product_id=item.product_id,
                    transaction_type='OUT',
                    transaction_source='SALES_INVOICE',
                    reference_id=invoice_id,
                    reference_number=invoice_number,
                    batch_number=getattr(item, 'batch_number', '') or '',
                    quantity=paid_qty,
                    unit_price=item.unit_price_base,
                    tenant_id=tenant_id,
                    created_by=username
                )
                session.add(paid_transaction)
                
                # Update stock balance for paid quantity
                self._update_stock_balance(session, item.product_id, 
                                         getattr(item, 'batch_number', '') or '', 
                                         paid_qty, float(item.unit_price_base), 'OUT')
            
            # Create separate stock transaction for free quantity
            if free_qty > 0:
                free_transaction = StockTransaction(
                    product_id=item.product_id,
                    transaction_type='OUT',
                    transaction_source='SALES_INVOICE_FREE',
                    reference_id=invoice_id,
                    reference_number=f"{invoice_number}-FREE",
                    batch_number=getattr(item, 'batch_number', '') or '',
                    quantity=free_qty,
                    unit_price=Decimal('0.0000'),  # Free items have zero price
                    tenant_id=tenant_id,
                    created_by=username
                )
                session.add(free_transaction)
                
                # Update stock balance for free quantity (use average cost for valuation)
                avg_cost = self._get_average_cost(session, item.product_id, getattr(item, 'batch_number', '') or '')
                self._update_stock_balance(session, item.product_id, 
                                         getattr(item, 'batch_number', '') or '', 
                                         free_qty, avg_cost, 'OUT')
    
    def reverse_sales_invoice_transaction_in_session(self, session, tenant_id, invoice_id, username):
        """Reverse stock OUT transactions for sales invoice within existing session"""
        from modules.inventory_module.models.sales_invoice_entity import SalesInvoice, SalesInvoiceItem
        
        # Get invoice
        invoice = session.query(SalesInvoice).filter(
            SalesInvoice.id == invoice_id,
            SalesInvoice.tenant_id == tenant_id
        ).first()
        
        if not invoice:
            return
        
        # Get invoice items
        items = session.query(SalesInvoiceItem).filter(
            SalesInvoiceItem.invoice_id == invoice_id,
            SalesInvoiceItem.tenant_id == tenant_id
        ).all()
        
        for item in items:
            paid_qty = float(item.quantity)
            free_qty = float(getattr(item, 'free_quantity', 0) or 0)
            
            # Reverse paid quantity transaction
            if paid_qty > 0:
                paid_reversal = StockTransaction(
                    product_id=item.product_id,
                    transaction_type='IN',
                    transaction_source='SALES_INVOICE_REVERSAL',
                    reference_id=invoice_id,
                    reference_number=f"REV-{invoice.invoice_number}",
                    batch_number=getattr(item, 'batch_number', '') or '',
                    quantity=paid_qty,
                    unit_price=item.unit_price_base,
                    tenant_id=tenant_id,
                    created_by=username
                )
                session.add(paid_reversal)
                
                # Update stock balance (reverse OUT with IN)
                self._update_stock_balance(session, item.product_id, 
                                         getattr(item, 'batch_number', '') or '', 
                                         paid_qty, float(item.unit_price_base), 'IN')
            
            # Reverse free quantity transaction
            if free_qty > 0:
                free_reversal = StockTransaction(
                    product_id=item.product_id,
                    transaction_type='IN',
                    transaction_source='SALES_INVOICE_FREE_REVERSAL',
                    reference_id=invoice_id,
                    reference_number=f"REV-{invoice.invoice_number}-FREE",
                    batch_number=getattr(item, 'batch_number', '') or '',
                    quantity=free_qty,
                    unit_price=Decimal('0.0000'),
                    tenant_id=tenant_id,
                    created_by=username
                )
                session.add(free_reversal)
                
                # Update stock balance for free quantity reversal
                avg_cost = self._get_average_cost(session, item.product_id, getattr(item, 'batch_number', '') or '')
                self._update_stock_balance(session, item.product_id, 
                                         getattr(item, 'batch_number', '') or '', 
                                         free_qty, avg_cost, 'IN')
    
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
    
    def _get_average_cost(self, session, product_id, batch_number):
        """Get average cost for a product/batch for free item valuation"""
        balance = session.query(StockBalance).filter(
            StockBalance.product_id == product_id,
            StockBalance.batch_number == batch_number,
            StockBalance.tenant_id == session_manager.get_current_tenant_id()
        ).first()
        
        if balance and balance.average_cost:
            return float(balance.average_cost)
        
        # Fallback to zero if no balance found
        return 0.0