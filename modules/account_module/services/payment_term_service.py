from core.database.connection import db_manager
from core.shared.utils.session_manager import session_manager
from core.shared.middleware.exception_handler import ExceptionMiddleware
from modules.account_module.models.payment_term_entity import PaymentTerm
from sqlalchemy import func
import math


class PaymentTermService:
    """Service layer for payment terms management"""
    
    @ExceptionMiddleware.handle_exceptions("PaymentTermService")
    def create(self, payment_term_data: dict):
        """Create a new payment term"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            username = session_manager.get_current_username()
            
            # Check if code already exists for this tenant
            existing = session.query(PaymentTerm).filter(
                PaymentTerm.tenant_id == tenant_id,
                PaymentTerm.code == payment_term_data.get('code'),
                PaymentTerm.is_deleted == False
            ).first()
            
            if existing:
                raise ValueError(f"Payment term with code '{payment_term_data.get('code')}' already exists")
            
            # If setting as default, unset other defaults first
            if payment_term_data.get('is_default', False):
                session.query(PaymentTerm).filter(
                    PaymentTerm.tenant_id == tenant_id,
                    PaymentTerm.is_default == True,
                    PaymentTerm.is_deleted == False
                ).update({'is_default': False, 'updated_by': username})
            
            # Create payment term
            payment_term = PaymentTerm(
                tenant_id=tenant_id,
                code=payment_term_data.get('code'),
                name=payment_term_data.get('name'),
                days=payment_term_data.get('days'),
                description=payment_term_data.get('description'),
                is_default=payment_term_data.get('is_default', False),
                is_active=payment_term_data.get('is_active', True),
                created_by=username,
                updated_by=username
            )
            
            session.add(payment_term)
            session.commit()
            session.refresh(payment_term)
            
            return self._to_dict(payment_term)
    
    @ExceptionMiddleware.handle_exceptions("PaymentTermService")
    def get_all(self, page=1, page_size=100, search=None, is_active=None):
        """Get all payment terms with pagination"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            query = session.query(PaymentTerm).filter(
                PaymentTerm.tenant_id == tenant_id,
                PaymentTerm.is_deleted == False
            )
            
            # Apply filters
            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    (PaymentTerm.code.ilike(search_pattern)) |
                    (PaymentTerm.name.ilike(search_pattern))
                )
            
            if is_active is not None:
                query = query.filter(PaymentTerm.is_active == is_active)
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            query = query.order_by(PaymentTerm.name)
            offset = (page - 1) * page_size
            payment_terms = query.offset(offset).limit(page_size).all()
            
            return {
                'total': total,
                'page': page,
                'per_page': page_size,
                'total_pages': math.ceil(total / page_size) if total > 0 else 0,
                'data': [self._to_dict(pt) for pt in payment_terms]
            }
    
    @ExceptionMiddleware.handle_exceptions("PaymentTermService")
    def get_by_id(self, payment_term_id: int):
        """Get a specific payment term by ID"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            payment_term = session.query(PaymentTerm).filter(
                PaymentTerm.id == payment_term_id,
                PaymentTerm.tenant_id == tenant_id,
                PaymentTerm.is_deleted == False
            ).first()
            
            if not payment_term:
                return None
            
            return self._to_dict(payment_term)
    
    @ExceptionMiddleware.handle_exceptions("PaymentTermService")
    def update(self, payment_term_id: int, payment_term_data: dict):
        """Update an existing payment term"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            username = session_manager.get_current_username()
            
            payment_term = session.query(PaymentTerm).filter(
                PaymentTerm.id == payment_term_id,
                PaymentTerm.tenant_id == tenant_id,
                PaymentTerm.is_deleted == False
            ).first()
            
            if not payment_term:
                return None
            
            # Check if code already exists (excluding current record)
            if 'code' in payment_term_data:
                existing = session.query(PaymentTerm).filter(
                    PaymentTerm.tenant_id == tenant_id,
                    PaymentTerm.code == payment_term_data.get('code'),
                    PaymentTerm.id != payment_term_id,
                    PaymentTerm.is_deleted == False
                ).first()
                
                if existing:
                    raise ValueError(f"Payment term with code '{payment_term_data.get('code')}' already exists")
            
            # If setting as default, unset other defaults first
            if payment_term_data.get('is_default', False) and not payment_term.is_default:
                session.query(PaymentTerm).filter(
                    PaymentTerm.tenant_id == tenant_id,
                    PaymentTerm.is_default == True,
                    PaymentTerm.id != payment_term_id,
                    PaymentTerm.is_deleted == False
                ).update({'is_default': False, 'updated_by': username})
            
            # Update fields
            if 'code' in payment_term_data:
                payment_term.code = payment_term_data['code']
            if 'name' in payment_term_data:
                payment_term.name = payment_term_data['name']
            if 'days' in payment_term_data:
                payment_term.days = payment_term_data['days']
            if 'description' in payment_term_data:
                payment_term.description = payment_term_data['description']
            if 'is_default' in payment_term_data:
                payment_term.is_default = payment_term_data['is_default']
            if 'is_active' in payment_term_data:
                payment_term.is_active = payment_term_data['is_active']
            
            payment_term.updated_by = username
            
            session.commit()
            session.refresh(payment_term)
            
            return self._to_dict(payment_term)
    
    @ExceptionMiddleware.handle_exceptions("PaymentTermService")
    def delete(self, payment_term_id: int):
        """Soft delete a payment term"""
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            username = session_manager.get_current_username()
            
            payment_term = session.query(PaymentTerm).filter(
                PaymentTerm.id == payment_term_id,
                PaymentTerm.tenant_id == tenant_id,
                PaymentTerm.is_deleted == False
            ).first()
            
            if not payment_term:
                return False
            
            payment_term.is_deleted = True
            payment_term.is_active = False
            payment_term.updated_by = username
            
            session.commit()
            return True
    
    def _to_dict(self, payment_term):
        """Convert payment term entity to dictionary"""
        return {
            'id': payment_term.id,
            'code': payment_term.code,
            'name': payment_term.name,
            'days': payment_term.days,
            'description': payment_term.description,
            'is_default': payment_term.is_default,
            'is_active': payment_term.is_active,
            'is_deleted': payment_term.is_deleted,
            'created_at': payment_term.created_at,
            'created_by': payment_term.created_by,
            'updated_at': payment_term.updated_at,
            'updated_by': payment_term.updated_by
        }
