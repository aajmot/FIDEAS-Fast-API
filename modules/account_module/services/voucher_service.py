from core.database.connection import db_manager
from modules.account_module.models.entities import Voucher, VoucherType
from core.shared.utils.logger import logger
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware
from datetime import datetime

class VoucherService:
    def __init__(self):
        self.logger_name = "VoucherService"
    
    @ExceptionMiddleware.handle_exceptions("VoucherService")
    def create(self, voucher_data):
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            # Generate voucher number
            voucher_type = None
            if 'voucher_type_id' in voucher_data:
                voucher_type = session.query(VoucherType).filter(
                    VoucherType.id == voucher_data['voucher_type_id'],
                    VoucherType.tenant_id == tenant_id
                ).first()
            elif 'voucher_type' in voucher_data:
                voucher_type = session.query(VoucherType).filter(
                    VoucherType.name == voucher_data['voucher_type'],
                    VoucherType.tenant_id == tenant_id
                ).first()
            
            if not voucher_type:
                raise ValueError("Voucher type not found")
            
            prefix = voucher_type.prefix if voucher_type else "V"
            
            today = datetime.now().strftime("%Y%m%d")
            last_voucher = session.query(Voucher).filter(
                Voucher.voucher_number.like(f"{prefix}{today}%"),
                Voucher.tenant_id == tenant_id
            ).order_by(Voucher.id.desc()).first()
            
            if last_voucher:
                seq = int(last_voucher.voucher_number[-3:]) + 1
            else:
                seq = 1
            
            voucher_number = f"{prefix}{today}{seq:03d}"
            
            # Map frontend data to database fields
            voucher_data_mapped = {
                'voucher_type_id': voucher_type.id,
                'voucher_date': datetime.fromisoformat(voucher_data.get('date', datetime.now().isoformat())),
                'total_amount': voucher_data.get('amount', 0),
                'narration': voucher_data.get('description', ''),
                'tenant_id': tenant_id,
                'created_by': session_manager.get_current_username()
            }
            
            voucher = Voucher(
                voucher_number=voucher_number,
                **voucher_data_mapped
            )
            session.add(voucher)
            session.flush()
            voucher_id = voucher.id
            voucher_number = voucher.voucher_number
            session.commit()
            logger.info(f"Voucher created: {voucher_number}", self.logger_name)
            return type('VoucherResult', (), {'id': voucher_id, 'voucher_number': voucher_number})()
    
    @ExceptionMiddleware.handle_exceptions("VoucherService")
    def get_all(self):
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            return session.query(Voucher).filter(Voucher.tenant_id == tenant_id).order_by(Voucher.voucher_date.desc()).all()
    
    @ExceptionMiddleware.handle_exceptions("VoucherService")
    def get_by_id(self, voucher_id):
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            return session.query(Voucher).filter(
                Voucher.id == voucher_id,
                Voucher.tenant_id == tenant_id
            ).first()