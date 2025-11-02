from core.database.connection import db_manager
from modules.inventory_module.models.stock_entity import StockBalance
from modules.inventory_module.models.entities import Product
from sqlalchemy import func, case, or_
from core.shared.utils.session_manager import session_manager

class StockSummaryService:
    
    @staticmethod
    def calculate_stock_status(current_stock, danger_level=None, reorder_level=None, max_stock=None):
        """Calculate stock status using priority-based logic matching frontend"""
        danger = danger_level or 5
        reorder = reorder_level or 10
        max_val = max_stock or 100
        
        if current_stock <= danger:
            return 'danger'
        elif current_stock <= reorder:
            return 'reorder'
        elif current_stock >= max_val:
            return 'overstock'
        else:
            return 'normal'
    
    def get_stock_meter_summary(self, product_id=None):
        """Get stock meter summary using centralized status calculation"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            query = session.query(StockBalance, Product).join(Product)
            
            if tenant_id:
                query = query.filter(Product.tenant_id == tenant_id)
            
            if product_id:
                query = query.filter(StockBalance.product_id == product_id)
            
            query = query.filter(StockBalance.total_quantity > 0)
            
            balances = query.all()
            
            counts = {
                'total_products': 0,
                'danger_level_count': 0,
                'reorder_level_count': 0,
                'normal_count': 0,
                'overstock_count': 0
            }
            
            for balance, product in balances:
                counts['total_products'] += 1
                
                status = self.calculate_stock_status(
                    float(balance.total_quantity or 0),
                    getattr(product, 'danger_level', None) or 5,
                    getattr(product, 'reorder_level', None) or 10,
                    getattr(product, 'max_stock', None) or 100
                )
                
                if status == 'danger':
                    counts['danger_level_count'] += 1
                elif status == 'reorder':
                    counts['reorder_level_count'] += 1
                elif status == 'overstock':
                    counts['overstock_count'] += 1
                else:
                    counts['normal_count'] += 1
            
            return counts
    
    def get_stock_summary(self, product_id=None):
        """Get stock summary with efficient single DB query"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            query = session.query(
                func.count().label('total_products'),
                func.sum(StockBalance.total_quantity * StockBalance.average_cost).label('total_inventory_value')
            ).select_from(
                StockBalance
            ).join(Product)
            
            if tenant_id:
                query = query.filter(Product.tenant_id == tenant_id)
            
            if product_id:
                query = query.filter(StockBalance.product_id == product_id)
            
            query = query.filter(StockBalance.total_quantity > 0)
            
            result = query.first()
            
            return {
                'total_products': int(result.total_products or 0),
                'total_inventory_value': float(result.total_inventory_value or 0)
            }
    
    def get_stock_details_with_status(self, product_id=None, page=1, per_page=10, search=None):
        """Get stock details with calculated status using centralized logic"""
        with db_manager.get_session() as session:
            from sqlalchemy.orm import joinedload
            
            tenant_id = session_manager.get_current_tenant_id()
            
            query = session.query(StockBalance).options(joinedload(StockBalance.product)).join(Product)
            
            if tenant_id:
                query = query.filter(Product.tenant_id == tenant_id)
            
            if product_id:
                query = query.filter(StockBalance.product_id == product_id)
            
            if search:
                query = query.filter(Product.name.ilike(f"%{search}%"))
            
            query = query.filter(StockBalance.total_quantity > 0)
            
            total = query.count()
            offset = (page - 1) * per_page
            balances = query.offset(offset).limit(per_page).all()
            
            stock_data = []
            for balance in balances:
                danger_level = getattr(balance.product, 'danger_level', None) or 5
                reorder_level = getattr(balance.product, 'reorder_level', None) or 10
                max_stock = getattr(balance.product, 'max_stock', None) or 100
                
                stock_data.append({
                    "id": balance.id,
                    "product_id": balance.product_id,
                    "product_name": balance.product.name,
                    "batch_number": balance.batch_number or "-",
                    "total_quantity": float(balance.total_quantity or 0),
                    "available_quantity": float(balance.available_quantity or 0),
                    "reserved_quantity": float(balance.reserved_quantity or 0),
                    "average_cost": float(balance.average_cost or 0),
                    "total_value": float(balance.total_quantity or 0) * float(balance.average_cost or 0),
                    "last_updated": balance.last_updated.isoformat() if balance.last_updated else None,
                    "danger_level": float(danger_level),
                    "reorder_level": float(reorder_level),
                    "max_stock": float(max_stock),
                    "min_stock": float(getattr(balance.product, 'min_stock', None) or 0),
                    "stock_status": self.calculate_stock_status(
                        float(balance.total_quantity or 0),
                        danger_level,
                        reorder_level,
                        max_stock
                    )
                })
            
            return stock_data, total
    
    def get_stock_tracking_summary(self, product_id=None, movement_type=None, reference_type=None, from_date=None, to_date=None):
        """Get stock tracking summary with efficient calculation"""
        with db_manager.get_session() as session:
            from modules.inventory_module.models.stock_entity import StockTransaction
            from datetime import datetime
            
            tenant_id = session_manager.get_current_tenant_id()
            
            query = session.query(StockTransaction).join(Product)
            
            if tenant_id:
                query = query.filter(StockTransaction.tenant_id == tenant_id)
            
            if product_id:
                query = query.filter(StockTransaction.product_id == product_id)
            
            if movement_type:
                if movement_type == 'in':
                    query = query.filter(StockTransaction.transaction_type == 'IN')
                elif movement_type == 'out':
                    query = query.filter(StockTransaction.transaction_type == 'OUT')
            
            if reference_type:
                source_mapping = {
                    'Purchase Order': 'PURCHASE',
                    'Sales Order': 'SALES',
                    'Product Waste': 'WASTE',
                    'Stock Adjustment': 'ADJUSTMENT'
                }
                if reference_type in source_mapping:
                    query = query.filter(StockTransaction.transaction_source == source_mapping[reference_type])
            
            if from_date:
                try:
                    from_dt = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
                    query = query.filter(StockTransaction.transaction_date >= from_dt)
                except ValueError:
                    pass
            
            if to_date:
                try:
                    to_dt = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
                    query = query.filter(StockTransaction.transaction_date <= to_dt)
                except ValueError:
                    pass
            
            transactions = query.all()
            
            total_movements = len(transactions)
            total_in = sum(t.quantity for t in transactions if t.transaction_type == 'IN')
            total_out = sum(t.quantity for t in transactions if t.transaction_type == 'OUT')
            net_movement = total_in - total_out
            
            return {
                'total_movements': total_movements,
                'total_in': float(total_in),
                'total_out': float(total_out),
                'net_movement': float(net_movement)
            }