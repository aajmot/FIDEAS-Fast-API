from typing import List
from core.database.connection import db_manager
from modules.inventory_module.models.entities import PurchaseOrder, PurchaseOrderItem
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware
from datetime import datetime

class PurchaseOrderService:
    @ExceptionMiddleware.handle_exceptions("PurchaseOrderService")
    def create_with_items(self, order_data: dict, items_data: List[dict]):
        """Create a purchase order with its items"""
        with db_manager.get_session() as session:
            # Remove generated columns from order_data - these are calculated by the database
            generated_columns = ['total_tax_amount', 'net_amount_base']
            for col in generated_columns:
                order_data.pop(col, None)
            
            # Add tenant_id from session manager
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                order_data['tenant_id'] = tenant_id
            
            # Add audit fields
            username = session_manager.get_current_username()
            if username:
                order_data['created_by'] = username
                order_data['updated_by'] = username
            
            # Calculate order totals from items if not provided
            if 'subtotal_amount' not in order_data:
                subtotal = sum(float(item.get('taxable_amount', 0)) for item in items_data)
                order_data['subtotal_amount'] = subtotal
            
            if 'net_amount' not in order_data:
                # Calculate net amount: taxable + taxes - discount + roundoff
                discount = float(order_data.get('header_discount_amount', 0))
                roundoff = float(order_data.get('roundoff', 0))
                cgst = float(order_data.get('cgst_amount', 0))
                sgst = float(order_data.get('sgst_amount', 0))
                igst = float(order_data.get('igst_amount', 0))
                cess = float(order_data.get('cess_amount', 0))
                
                taxable = float(order_data.get('taxable_amount', 0))
                net = taxable + cgst + sgst + igst + cess - discount + roundoff
                order_data['net_amount'] = net
            
            # Create order
            order = PurchaseOrder(**order_data)
            session.add(order)
            session.flush()  # This will populate the order.id

            # Create items and collect ORM instances
            created_items = []
            for item_data in items_data:
                item_data['purchase_order_id'] = order.id
                item_data['tenant_id'] = tenant_id
                if username:
                    item_data['created_by'] = username
                    item_data['updated_by'] = username
                item = PurchaseOrderItem(**item_data)
                session.add(item)
                created_items.append(item)

            # Record stock transactions in the same DB session
            try:
                from modules.inventory_module.services.stock_service import StockService
                stock_service = StockService()
                # Use the in-session method to avoid opening a new session
                stock_service.record_purchase_transaction_in_session(session, order, created_items)
            except Exception:
                # If stock recording fails, rollback the session and re-raise
                session.rollback()
                raise

            session.commit()
            return order.id
    
    @ExceptionMiddleware.handle_exceptions("PurchaseOrderService")
    def get_all(self, page=1, page_size=100):
        from sqlalchemy.orm import joinedload
        from modules.inventory_module.models.entities import Supplier
        
        with db_manager.get_session() as session:
            query = session.query(PurchaseOrder).options(joinedload(PurchaseOrder.supplier))
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(PurchaseOrder.tenant_id == tenant_id)
            
            # Order by date desc (most recent first)
            query = query.order_by(PurchaseOrder.order_date.desc(), PurchaseOrder.created_at.desc())
            
            # Apply pagination
            offset = (page - 1) * page_size
            orders = query.offset(offset).limit(page_size).all()
            
            # Convert to dict to avoid DetachedInstanceError and include all fields
            result = []
            for order in orders:
                order_dict = {
                    'id': order.id,
                    'po_number': order.po_number,
                    'reference_number': order.reference_number,
                    'supplier_id': order.supplier_id,
                    'supplier_name': order.supplier.name if order.supplier else order.supplier_name or '',
                    'supplier_gstin': order.supplier_gstin,
                    'order_date': order.order_date,
                    'subtotal_amount': order.subtotal_amount,
                    'header_discount_percent': order.header_discount_percent,
                    'header_discount_amount': order.header_discount_amount,
                    'taxable_amount': order.taxable_amount,
                    'cgst_amount': order.cgst_amount,
                    'sgst_amount': order.sgst_amount,
                    'igst_amount': order.igst_amount,
                    'cess_amount': order.cess_amount,
                    'total_tax_amount': order.total_tax_amount,
                    'roundoff': order.roundoff,
                    'net_amount': order.net_amount,
                    'currency_id': order.currency_id,
                    'exchange_rate': order.exchange_rate,
                    'net_amount_base': order.net_amount_base,
                    'is_reverse_charge': order.is_reverse_charge,
                    'is_tax_inclusive': order.is_tax_inclusive,
                    'status': order.status,
                    'approval_status': order.approval_status,
                    'approval_request_id': order.approval_request_id,
                    'reversal_reason': order.reversal_reason,
                    'reversed_at': order.reversed_at,
                    'reversed_by': order.reversed_by,
                    'created_at': order.created_at,
                    'created_by': order.created_by,
                    'updated_at': order.updated_at,
                    'updated_by': order.updated_by,
                }
                result.append(type('PurchaseOrder', (), order_dict)())
            
            return result
    
    @ExceptionMiddleware.handle_exceptions("PurchaseOrderService")
    def get_total_count(self):
        with db_manager.get_session() as session:
            query = session.query(PurchaseOrder)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(PurchaseOrder.tenant_id == tenant_id)
            return query.count()
    
    @ExceptionMiddleware.handle_exceptions("PurchaseOrderService")
    def get_by_id(self, order_id: int):
        with db_manager.get_session() as session:
            return session.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    
    @ExceptionMiddleware.handle_exceptions("PurchaseOrderService")
    def update(self, order_id: int, order_data: dict):
        with db_manager.get_session() as session:
            order = session.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
            if order:
                order_data['updated_by'] = session_manager.get_current_username()
                
                for key, value in order_data.items():
                    if hasattr(order, key):
                        setattr(order, key, value)
                session.commit()
                return order
            return None
    
    @ExceptionMiddleware.handle_exceptions("PurchaseOrderService")
    def reverse_order(self, order_id: int, reason: str):
        """Reverse a purchase order - reverses stock and accounting transactions"""
        with db_manager.get_session() as session:
            try:
                order = session.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
                if not order:
                    raise ValueError("Order not found")
                
                if order.status == 'REVERSED':
                    raise ValueError("Order is already reversed")
                
                # Get order items
                items = session.query(PurchaseOrderItem).filter(PurchaseOrderItem.purchase_order_id == order_id).all()
                
                # Reverse stock transactions
                try:
                    from modules.inventory_module.services.stock_service import StockService
                    stock_service = StockService()
                    stock_service.reverse_purchase_transaction_in_session(session, order, items)
                except (ImportError, AttributeError):
                    pass  # Stock service not available
                
                # Reverse accounting transactions
                try:
                    from modules.account_module.services.payment_service import PaymentService
                    payment_service = PaymentService()
                    payment_service.reverse_purchase_transaction_in_session(
                        session, order.id, order.po_number, float(order.net_amount), order.order_date
                    )
                except (ImportError, AttributeError):
                    pass  # Payment service not available
                
                # Update order status and reason
                order.status = 'REVERSED'
                order.reversal_reason = reason
                order.reversed_at = datetime.now()
                order.reversed_by = session_manager.get_current_username()
                order.updated_by = session_manager.get_current_username()
                
                session.commit()
                return True
                
            except Exception as e:
                session.rollback()
                raise e
    
    @ExceptionMiddleware.handle_exceptions("PurchaseOrderService")
    def delete(self, order_id: int):
        with db_manager.get_session() as session:
            order = session.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
            if order:
                # Delete order items first
                session.query(PurchaseOrderItem).filter(PurchaseOrderItem.purchase_order_id == order_id).delete()
                # Delete order
                session.delete(order)
                session.commit()
                return True
            return False