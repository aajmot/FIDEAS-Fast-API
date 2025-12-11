from sqlalchemy.orm import joinedload
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import date
from core.database.connection import db_manager
from modules.account_module.models.debit_note_entity import DebitNote, DebitNoteItem
from modules.account_module.models.entities import VoucherType, Voucher, VoucherLine
from modules.account_module.models.account_configuration_entity import AccountConfiguration
from modules.account_module.models.account_configuration_key_entity import AccountConfigurationKey
from modules.admin_module.models.currency import Currency


class DebitNoteService:
    """Service layer for debit note operations"""
    
    @staticmethod
    def create_debit_note(note_data: Dict[str, Any], tenant_id: int, created_by: str) -> int:
        """Create a new debit note with items and accounting entries"""
        with db_manager.get_session() as session:
            try:
                # Get base currency if not provided
                if not note_data.get('base_currency_id'):
                    base_currency = session.query(Currency).filter_by(is_base=True).first()
                    note_data['base_currency_id'] = base_currency.id if base_currency else 1
                
                # Create debit note
                debit_note = DebitNote(
                    tenant_id=tenant_id,
                    created_by=created_by,
                    **{k: v for k, v in note_data.items() if k != 'items'}
                )
                session.add(debit_note)
                session.flush()  # Get the ID
                
                # Create items
                for item_data in note_data['items']:
                    item = DebitNoteItem(
                        debit_note_id=debit_note.id,
                        tenant_id=tenant_id,
                        created_by=created_by,
                        **item_data
                    )
                    session.add(item)
                
                # Create accounting entries if status is POSTED
                if note_data.get('status') == 'POSTED':
                    DebitNoteService._create_accounting_entries(
                        session, debit_note.id, note_data, tenant_id, created_by
                    )
                
                session.commit()
                return debit_note.id
                
            except Exception as e:
                session.rollback()
                raise e
    
    @staticmethod
    def _create_accounting_entries(session, note_id: int, note_data: Dict[str, Any], 
                                 tenant_id: int, created_by: str):
        """Create accounting entries for debit note"""
        # Get voucher type for debit note
        voucher_type = session.query(VoucherType).filter_by(
            code='DEBIT_NOTE', tenant_id=tenant_id
        ).first()
        
        if not voucher_type:
            return  # Skip if voucher type not configured
        
        # Create voucher
        voucher = Voucher(
            voucher_number=f"V-{note_data['note_number']}",
            voucher_type_id=voucher_type.id,
            voucher_date=note_data['note_date'],
            base_currency_id=note_data['base_currency_id'],
            reference_type='DEBIT_NOTE',
            reference_id=note_id,
            reference_number=note_data['note_number'],
            narration=note_data.get('reason', 'Debit note'),
            base_total_amount=note_data['total_amount_base'],
            base_total_debit=note_data['total_amount_base'],
            base_total_credit=note_data['total_amount_base'],
            tenant_id=tenant_id,
            created_by=created_by
        )
        session.add(voucher)
        session.flush()  # Get voucher ID
        
        # Get account configurations
        account_configs = session.query(
            AccountConfigurationKey.code, AccountConfiguration.account_id
        ).join(
            AccountConfiguration, AccountConfiguration.config_key_id == AccountConfigurationKey.id
        ).filter(
            AccountConfiguration.tenant_id == tenant_id,
            AccountConfigurationKey.code.in_(['PURCHASES', 'ACCOUNTS_PAYABLE', 'GST_INPUT']),
            AccountConfiguration.is_deleted == False,
            AccountConfigurationKey.is_active == True
        ).all()
        
        account_map = {code: account_id for code, account_id in account_configs}
        
        # Create voucher lines
        line_no = 1
        
        # Debit Purchases Account (Additional purchase cost)
        if 'PURCHASES' in account_map:
            purchase_line = VoucherLine(
                voucher_id=voucher.id,
                line_no=line_no,
                account_id=account_map['PURCHASES'],
                description=f"Purchase adjustment - {note_data['note_number']}",
                debit_base=note_data['subtotal_base'],
                credit_base=0,
                tenant_id=tenant_id,
                created_by=created_by
            )
            session.add(purchase_line)
            line_no += 1
        
        # Debit GST Input Account (Additional GST)
        if 'GST_INPUT' in account_map and note_data.get('tax_amount_base', 0) > 0:
            gst_line = VoucherLine(
                voucher_id=voucher.id,
                line_no=line_no,
                account_id=account_map['GST_INPUT'],
                description=f"GST input - {note_data['note_number']}",
                debit_base=note_data['tax_amount_base'],
                credit_base=0,
                tenant_id=tenant_id,
                created_by=created_by
            )
            session.add(gst_line)
            line_no += 1
        
        # Credit Accounts Payable
        if 'ACCOUNTS_PAYABLE' in account_map:
            ap_line = VoucherLine(
                voucher_id=voucher.id,
                line_no=line_no,
                account_id=account_map['ACCOUNTS_PAYABLE'],
                description=f"Supplier debit - {note_data['note_number']}",
                debit_base=0,
                credit_base=note_data['total_amount_base'],
                tenant_id=tenant_id,
                created_by=created_by
            )
            session.add(ap_line)
        
        # Update debit note with voucher_id
        debit_note = session.query(DebitNote).filter_by(id=note_id).first()
        if debit_note:
            debit_note.voucher_id = voucher.id
    
    @staticmethod
    def get_debit_note_by_id(note_id: int, tenant_id: int) -> Optional[Dict[str, Any]]:
        """Get debit note by ID with items"""
        with db_manager.get_session() as session:
            debit_note = session.query(DebitNote).options(
                joinedload(DebitNote.items),
                joinedload(DebitNote.supplier)
            ).filter_by(
                id=note_id, tenant_id=tenant_id, is_deleted=False
            ).first()
            
            if not debit_note:
                return None
            
            # Convert to dict
            note_dict = {
                'id': debit_note.id,
                'note_number': debit_note.note_number,
                'supplier_name': debit_note.supplier.name if debit_note.supplier else None,
                'note_date': debit_note.note_date,
                'total_amount_base': debit_note.total_amount_base,
                'status': debit_note.status,
                'reason': debit_note.reason,
                'voucher_id': debit_note.voucher_id,
                'items': [{
                    'id': item.id,
                    'line_no': item.line_no,
                    'product_id': item.product_id,
                    'quantity': item.quantity,
                    'unit_price_base': item.unit_price_base,
                    'total_amount_base': item.total_amount_base
                } for item in debit_note.items if not item.is_deleted]
            }
            
            return note_dict
    
    @staticmethod
    def get_debit_notes_list(tenant_id: int, page: int = 1, per_page: int = 20, 
                           filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get paginated list of debit notes"""
        with db_manager.get_session() as session:
            query = session.query(DebitNote).options(
                joinedload(DebitNote.supplier)
            ).filter_by(tenant_id=tenant_id, is_deleted=False)
            
            # Apply filters
            if filters:
                if filters.get('supplier_id'):
                    query = query.filter(DebitNote.supplier_id == filters['supplier_id'])
                if filters.get('status'):
                    query = query.filter(DebitNote.status == filters['status'])
                if filters.get('date_from'):
                    query = query.filter(DebitNote.note_date >= filters['date_from'])
                if filters.get('date_to'):
                    query = query.filter(DebitNote.note_date <= filters['date_to'])
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            offset = (page - 1) * per_page
            notes = query.order_by(DebitNote.note_date.desc(), DebitNote.id.desc()).offset(offset).limit(per_page).all()
            
            return {
                'data': [{
                    'id': note.id,
                    'note_number': note.note_number,
                    'note_date': note.note_date,
                    'total_amount_base': note.total_amount_base,
                    'status': note.status,
                    'reason': note.reason,
                    'supplier_name': note.supplier.name if note.supplier else None
                } for note in notes],
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
    
    @staticmethod
    def update_debit_note_status(note_id: int, status: str, tenant_id: int, 
                               updated_by: str) -> bool:
        """Update debit note status"""
        with db_manager.get_session() as session:
            try:
                debit_note = session.query(DebitNote).filter_by(
                    id=note_id, tenant_id=tenant_id, is_deleted=False
                ).first()
                
                if not debit_note:
                    return False
                
                debit_note.status = status
                debit_note.updated_by = updated_by
                
                # If posting, create accounting entries
                if status == 'POSTED' and not debit_note.voucher_id:
                    note_data = {
                        'note_number': debit_note.note_number,
                        'note_date': debit_note.note_date,
                        'base_currency_id': debit_note.base_currency_id,
                        'reason': debit_note.reason,
                        'subtotal_base': debit_note.subtotal_base,
                        'tax_amount_base': debit_note.tax_amount_base,
                        'total_amount_base': debit_note.total_amount_base
                    }
                    DebitNoteService._create_accounting_entries(
                        session, note_id, note_data, tenant_id, updated_by
                    )
                
                session.commit()
                return True
                
            except Exception as e:
                session.rollback()
                raise e