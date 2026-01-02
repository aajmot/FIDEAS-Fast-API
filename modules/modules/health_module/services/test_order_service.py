from core.database.connection import db_manager
from modules.diagnostic_module.models.entities import TestOrder, TestOrderItem
from core.shared.utils.logger import logger
from datetime import datetime

class TestOrderService:
    def __init__(self):
        self.logger_name = "TestOrderService"
    
    def create(self, data):
        try:
            with db_manager.get_session() as session:
                items = data.pop('items', [])
                order = TestOrder(**data)
                session.add(order)
                session.flush()
                
                for item in items:
                    item['test_order_id'] = order.id
                    item['tenant_id'] = data['tenant_id']
                    order_item = TestOrderItem(**item)
                    session.add(order_item)
                
                order_id = order.id
                logger.info(f"Test order created: {order.test_order_number}", self.logger_name)
                session.expunge(order)
                order.id = order_id
                return order
        except Exception as e:
            logger.error(f"Error creating test order: {str(e)}", self.logger_name)
            raise
    
    def get_all(self, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(TestOrder).filter(TestOrder.is_deleted == False)
                if tenant_id:
                    query = query.filter(TestOrder.tenant_id == tenant_id)
                orders = query.all()
                for order in orders:
                    session.expunge(order)
                return orders
        except Exception as e:
            logger.error(f"Error fetching test orders: {str(e)}", self.logger_name)
            return []
    
    def get_by_id(self, order_id, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(TestOrder).filter(TestOrder.id == order_id, TestOrder.is_deleted == False)
                if tenant_id:
                    query = query.filter(TestOrder.tenant_id == tenant_id)
                order = query.first()
                if order:
                    session.expunge(order)
                return order
        except Exception as e:
            logger.error(f"Error fetching test order: {str(e)}", self.logger_name)
            return None
    
    def update(self, order_id, data):
        try:
            with db_manager.get_session() as session:
                order = session.query(TestOrder).filter(TestOrder.id == order_id, TestOrder.is_deleted == False).first()
                if order:
                    items = data.pop('items', None)
                    for key, value in data.items():
                        if key not in ['id', 'created_at', 'created_by']:
                            setattr(order, key, value)
                    order.updated_at = datetime.utcnow()
                    
                    if items is not None:
                        session.query(TestOrderItem).filter(TestOrderItem.test_order_id == order_id).update({'is_deleted': True})
                        session.flush()
                        for item in items:
                            item.pop('id', None)
                            item['test_order_id'] = order_id
                            item['tenant_id'] = order.tenant_id
                            order_item = TestOrderItem(**item)
                            session.add(order_item)
                    
                    session.flush()
                    logger.info(f"Test order updated: {order.test_order_number}", self.logger_name)
                    session.expunge(order)
                    return order
                return None
        except Exception as e:
            logger.error(f"Error updating test order: {str(e)}", self.logger_name)
            raise
    
    def delete(self, order_id):
        try:
            with db_manager.get_session() as session:
                order = session.query(TestOrder).filter(TestOrder.id == order_id).first()
                if order:
                    order.is_deleted = True
                    order.updated_at = datetime.utcnow()
                    session.query(TestOrderItem).filter(TestOrderItem.test_order_id == order_id).update({'is_deleted': True})
                    logger.info(f"Test order deleted: {order.test_order_number}", self.logger_name)
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting test order: {str(e)}", self.logger_name)
            raise
    
    def get_items(self, order_id, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(TestOrderItem).filter(
                    TestOrderItem.test_order_id == order_id,
                    TestOrderItem.is_deleted == False
                )
                if tenant_id:
                    query = query.filter(TestOrderItem.tenant_id == tenant_id)
                items = query.all()
                for item in items:
                    session.expunge(item)
                return items
        except Exception as e:
            logger.error(f"Error fetching test order items: {str(e)}", self.logger_name)
            return []
