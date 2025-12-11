from sqlalchemy.orm import joinedload
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import date
from core.database.connection import db_manager
from modules.account_module.models.credit_note_entity import CreditNote, CreditNoteItem
from modules.account_module.models.entities import VoucherType, Voucher, VoucherLine
from modules.account_module.models.account_configuration_entity import AccountConfiguration
from modules.account_module.models.account_configuration_key_entity import AccountConfigurationKey
from modules.admin_module.models.currency import Currency


class CreditNoteService:
    """Service layer for credit note operations"""
    
    @staticmethod
    def create_credit_note(note_data: Dict[str, Any], tenant_id: int, created_by: str) -> int:
        """Create a new credit note with items and accounting entries"""
        with db_manager.get_session() as session:
            try:
                # Get base currency if not provided
                if not note_data.get('base_currency_id'):
                    base_currency = session.query(Currency).filter_by(is_base=True).first()
                    note_data['base_currency_id'] = base_currency.id if base_currency else 1
                
                # Create credit note
                credit_note = CreditNote(
                    tenant_id=tenant_id,
                    created_by=created_by,
                    **{k: v for k, v in note_data.items() if k != 'items'}
                )
                session.add(credit_note)
                session.flush()  # Get the ID
                
                # Create items
                for item_data in note_data['items']:
                    item = CreditNoteItem(
                        credit_note_id=credit_note.id,
                        tenant_id=tenant_id,
                        created_by=created_by,
                        **item_data
                    )
                    session.add(item)
                
                # Create accounting entries if status is POSTED
                if note_data.get('status') == 'POSTED':
                    CreditNoteService._create_accounting_entries(
                        session, credit_note.id, note_data, tenant_id, created_by
                    )
                
                session.commit()
                return credit_note.id
                
            except Exception as e:
                session.rollback()
                raise e
    
    @staticmethod
    def _create_accounting_entries(session, note_id: int, note_data: Dict[str, Any], 
                                 tenant_id: int, created_by: str):
        """Create accounting entries for credit note"""
        # Get voucher type for credit note
        voucher_type = session.query(VoucherType).filter_by(
            code='CREDIT_NOTE', tenant_id=tenant_id
        ).first()
        
        if not voucher_type:
            return  # Skip if voucher type not configured
        
        # Create voucher
        voucher = Voucher(
            voucher_number=f"V-{note_data['note_number']}",
            voucher_type_id=voucher_type.id,
            voucher_date=note_data['note_date'],
            base_currency_id=note_data['base_currency_id'],
            reference_type='CREDIT_NOTE',
            reference_id=note_id,
            reference_number=note_data['note_number'],
            narration=note_data.get('reason', 'Credit note'),
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
            AccountConfigurationKey.code.in_(['SALES', 'ACCOUNTS_RECEIVABLE', 'GST_OUTPUT']),
            AccountConfiguration.is_deleted == False,
            AccountConfigurationKey.is_active == True
        ).all()
        
        account_map = {code: account_id for code, account_id in account_configs}
        
        # Create voucher lines
        line_no = 1
        
        # Debit Sales Account (Reverse the sale)
        if 'SALES' in account_map:
            sales_line = VoucherLine(
                voucher_id=voucher.id,
                line_no=line_no,
                account_id=account_map['SALES'],
                description=f"Sales return - {note_data['note_number']}",
                debit_base=note_data['subtotal_base'],
                credit_base=0,
                tenant_id=tenant_id,
                created_by=created_by
            )
            session.add(sales_line)
            line_no += 1
        
        # Debit GST Output Account (Reverse GST)
        if 'GST_OUTPUT' in account_map and note_data.get('tax_amount_base', 0) > 0:
            gst_line = VoucherLine(
                voucher_id=voucher.id,
                line_no=line_no,
                account_id=account_map['GST_OUTPUT'],
                description=f"GST reversal - {note_data['note_number']}",
                debit_base=note_data['tax_amount_base'],
                credit_base=0,
                tenant_id=tenant_id,
                created_by=created_by
            )
            session.add(gst_line)
            line_no += 1
        
        # Credit Accounts Receivable
        if 'ACCOUNTS_RECEIVABLE' in account_map:
            ar_line = VoucherLine(
                voucher_id=voucher.id,
                line_no=line_no,
                account_id=account_map['ACCOUNTS_RECEIVABLE'],
                description=f"Customer credit - {note_data['note_number']}",
                debit_base=0,
                credit_base=note_data['total_amount_base'],
                tenant_id=tenant_id,
                created_by=created_by
            )
            session.add(ar_line)
        
        # Update credit note with voucher_id
        credit_note = session.query(CreditNote).filter_by(id=note_id).first()
        if credit_note:
            credit_note.voucher_id = voucher.id
    
    @staticmethod
    def get_credit_note_by_id(note_id: int, tenant_id: int) -> Optional[Dict[str, Any]]:
        """Get credit note by ID with items"""
        with db_manager.get_session() as session:
            credit_note = session.query(CreditNote).options(
                joinedload(CreditNote.items),
                joinedload(CreditNote.customer)
            ).filter_by(
                id=note_id, tenant_id=tenant_id, is_deleted=False
            ).first()
            
            if not credit_note:
                return None
            
            # Convert to dict
            note_dict = {
                'id': credit_note.id,
                'note_number': credit_note.note_number,
                'customer_name': credit_note.customer.name if credit_note.customer else None,
                'note_date': credit_note.note_date,
                'total_amount_base': credit_note.total_amount_base,
                'status': credit_note.status,
                'reason': credit_note.reason,
                'voucher_id': credit_note.voucher_id,
                'items': [{
                    'id': item.id,
                    'line_no': item.line_no,
                    'product_id': item.product_id,
                    'quantity': item.quantity,
                    'unit_price_base': item.unit_price_base,
                    'total_amount_base': item.total_amount_base
                } for item in credit_note.items if not item.is_deleted]
            }
            
            return note_dict
    
    @staticmethod
    def get_credit_notes_list(tenant_id: int, page: int = 1, per_page: int = 20, 
                            filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get paginated list of credit notes"""
        with db_manager.get_session() as session:
            query = session.query(CreditNote).options(
                joinedload(CreditNote.customer)
            ).filter_by(tenant_id=tenant_id, is_deleted=False)
            
            # Apply filters
            if filters:
                if filters.get('customer_id'):
                    query = query.filter(CreditNote.customer_id == filters['customer_id'])
                if filters.get('status'):
                    query = query.filter(CreditNote.status == filters['status'])
                if filters.get('date_from'):
                    query = query.filter(CreditNote.note_date >= filters['date_from'])
                if filters.get('date_to'):
                    query = query.filter(CreditNote.note_date <= filters['date_to'])
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            offset = (page - 1) * per_page
            notes = query.order_by(CreditNote.note_date.desc(), CreditNote.id.desc()).offset(offset).limit(per_page).all()
            
            return {
                'data': [{
                    'id': note.id,
                    'note_number': note.note_number,
                    'note_date': note.note_date,
                    'total_amount_base': note.total_amount_base,
                    'status': note.status,
                    'credit_note_type': note.credit_note_type,
                    'reason': note.reason,
                    'customer_name': note.customer.name if note.customer else None
                } for note in notes],
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
    
    @staticmethod
    def update_credit_note_status(note_id: int, status: str, tenant_id: int, 
                                updated_by: str) -> bool:
        """Update credit note status"""
        with db_manager.get_session() as session:
            try:
                credit_note = session.query(CreditNote).filter_by(
                    id=note_id, tenant_id=tenant_id, is_deleted=False
                ).first()
                
                if not credit_note:
                    return False
                
                credit_note.status = status
                credit_note.updated_by = updated_by
                
                # If posting, create accounting entries
                if status == 'POSTED' and not credit_note.voucher_id:
                    note_data = {
                        'note_number': credit_note.note_number,
                        'note_date': credit_note.note_date,
                        'base_currency_id': credit_note.base_currency_id,
                        'reason': credit_note.reason,
                        'subtotal_base': credit_note.subtotal_base,
                        'tax_amount_base': credit_note.tax_amount_base,
                        'total_amount_base': credit_note.total_amount_base
                    }
                    CreditNoteService._create_accounting_entries(
                        session, note_id, note_data, tenant_id, updated_by
                    )
                
                session.commit()
                return True
                
            except Exception as e:
                session.rollback()
                raise e