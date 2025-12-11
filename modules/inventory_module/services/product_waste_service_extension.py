from core.database.connection import db_manager
from modules.inventory_module.models.product_waste_entity import ProductWaste, ProductWasteItem
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware

class ProductWasteServiceExtension:
    """Extension methods for ProductWasteService"""
    
    def __init__(self, waste_service):
        self.waste_service = waste_service
    
    def create_waste_voucher(self, waste_id: int):
        """Create waste voucher using voucher service"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            username = session_manager.get_current_username()
            
            waste = session.query(ProductWaste).filter(
                ProductWaste.id == waste_id,
                ProductWaste.tenant_id == tenant_id,
                ProductWaste.is_deleted == False
            ).first()
            
            if not waste:
                raise ValueError(f"Product waste with ID {waste_id} not found")
            
            if waste.voucher_id:
                raise ValueError("Voucher already exists for this waste entry")
            
            # Get items
            items = session.query(ProductWasteItem).filter(
                ProductWasteItem.waste_id == waste_id,
                ProductWasteItem.is_deleted == False
            ).all()
            
            items_data = [self._item_to_dict(item) for item in items]
            
            # Create voucher
            voucher = self.waste_service._create_waste_voucher_in_session(
                session=session,
                tenant_id=tenant_id,
                username=username,
                waste=waste,
                items_data=items_data
            )
            
            # Link voucher to waste
            waste.voucher_id = voucher.id
            
            session.commit()
            return voucher.id
    
    @ExceptionMiddleware.handle_exceptions("ProductWasteService")
    def validate_waste_accounting(self, waste_id: int):
        """Validate that waste has proper voucher entries"""
        from modules.account_module.models.entities import Voucher
        
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            waste = session.query(ProductWaste).filter(
                ProductWaste.id == waste_id,
                ProductWaste.tenant_id == tenant_id,
                ProductWaste.is_deleted == False
            ).first()
            
            if not waste:
                return {'valid': False, 'errors': ['Waste entry not found']}
            
            errors = []
            
            # Check if voucher exists
            if not waste.voucher_id:
                errors.append('Waste voucher not created')
            else:
                voucher = session.query(Voucher).filter(
                    Voucher.id == waste.voucher_id,
                    Voucher.tenant_id == tenant_id
                ).first()
                
                if not voucher:
                    errors.append('Waste voucher not found')
                elif not voucher.is_posted:
                    errors.append('Waste voucher not posted')
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'waste_id': waste_id,
                'voucher_id': waste.voucher_id,
                'total_cost': float(waste.total_cost_base or 0)
            }
    
    def _item_to_dict(self, item):
        """Convert waste item entity to dictionary"""
        return {
            'id': item.id,
            'line_no': item.line_no,
            'product_id': item.product_id,
            'batch_number': item.batch_number,
            'quantity': item.quantity,
            'unit_cost_base': item.unit_cost_base,
            'total_cost_base': item.total_cost_base,
            'currency_id': item.currency_id,
            'unit_cost_foreign': item.unit_cost_foreign,
            'total_cost_foreign': item.total_cost_foreign,
            'exchange_rate': item.exchange_rate,
            'reason': item.reason
        }