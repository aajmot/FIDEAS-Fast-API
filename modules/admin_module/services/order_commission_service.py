from core.database.connection import db_manager
from modules.admin_module.models.order_commission import OrderCommission, OrderCommissionItem
from core.shared.utils.logger import logger
from datetime import datetime

class OrderCommissionService:
    def __init__(self):
        self.logger_name = "OrderCommissionService"
    
    def create(self, data, items_data=None):
        try:
            # Validate order_type
            order_type = data.get('order_type')
            if not order_type or order_type not in ['Products', 'Tests']:
                raise ValueError("order_type must be 'Products' or 'Tests'")
            
            with db_manager.get_session() as session:
                # Create order commission
                order_commission = OrderCommission(**data)
                session.add(order_commission)
                session.flush()
                order_commission_id = order_commission.id
                
                # Create items if provided
                if items_data:
                    for item_data in items_data:
                        # Validate item_type
                        item_type = item_data.get('item_type')
                        if not item_type or item_type not in ['Products', 'Tests']:
                            raise ValueError("item_type must be 'Products' or 'Tests'")
                        
                        item_data['order_commission_id'] = order_commission_id
                        item_data['tenant_id'] = data['tenant_id']
                        item = OrderCommissionItem(**item_data)
                        session.add(item)
                
                logger.info(f"Order commission created: {order_commission_id}", self.logger_name)
                session.expunge(order_commission)
                order_commission.id = order_commission_id
                return order_commission
        except Exception as e:
            logger.error(f"Error creating order commission: {str(e)}", self.logger_name)
            raise
    
    def get_all(self, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(OrderCommission).filter(OrderCommission.is_deleted == False)
                if tenant_id:
                    query = query.filter(OrderCommission.tenant_id == tenant_id)
                commissions = query.all()
                for commission in commissions:
                    session.expunge(commission)
                return commissions
        except Exception as e:
            logger.error(f"Error fetching order commissions: {str(e)}", self.logger_name)
            return []
    
    def get_by_id(self, commission_id, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(OrderCommission).filter(
                    OrderCommission.id == commission_id,
                    OrderCommission.is_deleted == False
                )
                if tenant_id:
                    query = query.filter(OrderCommission.tenant_id == tenant_id)
                commission = query.first()
                if commission:
                    session.expunge(commission)
                return commission
        except Exception as e:
            logger.error(f"Error fetching order commission: {str(e)}", self.logger_name)
            return None
    
    def get_items_by_commission_id(self, commission_id, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(OrderCommissionItem).filter(
                    OrderCommissionItem.order_commission_id == commission_id,
                    OrderCommissionItem.is_deleted == False
                )
                if tenant_id:
                    query = query.filter(OrderCommissionItem.tenant_id == tenant_id)
                items = query.all()
                for item in items:
                    session.expunge(item)
                return items
        except Exception as e:
            logger.error(f"Error fetching order commission items: {str(e)}", self.logger_name)
            return []
    
    def update(self, commission_id, data, items_data=None):
        try:
            # Validate order_type
            order_type = data.get('order_type')
            if order_type and order_type not in ['Products', 'Tests']:
                raise ValueError("order_type must be 'Products' or 'Tests'")
            
            with db_manager.get_session() as session:
                commission = session.query(OrderCommission).filter(
                    OrderCommission.id == commission_id,
                    OrderCommission.is_deleted == False
                ).first()
                
                if commission:
                    # Update commission
                    for key, value in data.items():
                        if key not in ['id', 'created_at', 'created_by']:
                            setattr(commission, key, value)
                    commission.updated_at = datetime.utcnow()
                    
                    # Update items if provided
                    if items_data is not None:
                        # Delete existing items
                        session.query(OrderCommissionItem).filter(
                            OrderCommissionItem.order_commission_id == commission_id
                        ).update({'is_deleted': True})
                        
                        # Add new items
                        for item_data in items_data:
                            item_type = item_data.get('item_type')
                            if not item_type or item_type not in ['Products', 'Tests']:
                                raise ValueError("item_type must be 'Products' or 'Tests'")
                            
                            item_data['order_commission_id'] = commission_id
                            item_data['tenant_id'] = commission.tenant_id
                            item = OrderCommissionItem(**item_data)
                            session.add(item)
                    
                    session.flush()
                    logger.info(f"Order commission updated: {commission_id}", self.logger_name)
                    session.expunge(commission)
                    return commission
                return None
        except Exception as e:
            logger.error(f"Error updating order commission: {str(e)}", self.logger_name)
            raise
    
    def delete(self, commission_id):
        try:
            with db_manager.get_session() as session:
                commission = session.query(OrderCommission).filter(
                    OrderCommission.id == commission_id
                ).first()
                if commission:
                    commission.is_deleted = True
                    commission.updated_at = datetime.utcnow()
                    
                    # Also delete items
                    session.query(OrderCommissionItem).filter(
                        OrderCommissionItem.order_commission_id == commission_id
                    ).update({'is_deleted': True, 'updated_at': datetime.utcnow()})
                    
                    logger.info(f"Order commission deleted: {commission_id}", self.logger_name)
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting order commission: {str(e)}", self.logger_name)
            raise