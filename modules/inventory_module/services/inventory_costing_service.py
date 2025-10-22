from decimal import Decimal
from typing import List, Tuple
from datetime import datetime

class InventoryCostingService:
    """Service for inventory costing calculations"""
    
    @staticmethod
    def calculate_fifo_cost(transactions: List[dict]) -> Tuple[Decimal, List[dict]]:
        """Calculate cost using FIFO method"""
        queue = []
        total_cost = Decimal('0')
        
        for txn in sorted(transactions, key=lambda x: x['date']):
            if txn['type'] == 'IN':
                queue.append({'qty': txn['qty'], 'cost': txn['unit_cost']})
            else:  # OUT
                remaining = txn['qty']
                while remaining > 0 and queue:
                    batch = queue[0]
                    if batch['qty'] <= remaining:
                        total_cost += batch['qty'] * batch['cost']
                        remaining -= batch['qty']
                        queue.pop(0)
                    else:
                        total_cost += remaining * batch['cost']
                        batch['qty'] -= remaining
                        remaining = 0
        
        return total_cost, queue
    
    @staticmethod
    def calculate_weighted_average_cost(transactions: List[dict]) -> Decimal:
        """Calculate cost using weighted average method"""
        total_qty = Decimal('0')
        total_value = Decimal('0')
        
        for txn in sorted(transactions, key=lambda x: x['date']):
            if txn['type'] == 'IN':
                total_qty += txn['qty']
                total_value += txn['qty'] * txn['unit_cost']
            else:  # OUT
                if total_qty > 0:
                    avg_cost = total_value / total_qty
                    total_value -= txn['qty'] * avg_cost
                    total_qty -= txn['qty']
        
        return total_value / total_qty if total_qty > 0 else Decimal('0')
    
    @staticmethod
    def calculate_cogs(product_id: int, quantity: Decimal, method: str = 'FIFO') -> Decimal:
        """Calculate Cost of Goods Sold"""
        from core.database.connection import db_manager
        from modules.inventory_module.models.stock_entities import StockTransaction
        
        with db_manager.get_session() as session:
            txns = session.query(StockTransaction).filter(
                StockTransaction.product_id == product_id
            ).order_by(StockTransaction.transaction_date).all()
            
            transactions = [{
                'date': t.transaction_date,
                'type': t.transaction_type,
                'qty': Decimal(str(t.quantity)),
                'unit_cost': Decimal(str(t.unit_price or 0))
            } for t in txns]
            
            if method == 'FIFO':
                cost, _ = InventoryCostingService.calculate_fifo_cost(transactions)
                return cost
            else:  # Weighted Average
                return InventoryCostingService.calculate_weighted_average_cost(transactions)
