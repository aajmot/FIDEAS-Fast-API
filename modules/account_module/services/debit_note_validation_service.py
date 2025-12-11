from typing import Dict, Any, List, Optional
from core.database.connection import db_manager
from modules.account_module.models.debit_note_entity import DebitNote
from modules.account_module.models.entities import Voucher, VoucherLine
from modules.account_module.models.account_configuration_entity import AccountConfiguration
from modules.account_module.models.account_configuration_key_entity import AccountConfigurationKey


class DebitNoteValidationService:
    """Validation service for debit note operations"""
    
    @staticmethod
    def validate_voucher_creation(note_id: int, tenant_id: int) -> Dict[str, Any]:
        """Validate voucher creation for debit note"""
        with db_manager.get_session() as session:
            try:
                # Get debit note
                debit_note = session.query(DebitNote).filter_by(
                    id=note_id, tenant_id=tenant_id, is_deleted=False
                ).first()
                
                if not debit_note:
                    return {
                        'valid': False,
                        'error': 'Debit note not found',
                        'voucher_exists': False
                    }
                
                # Check if voucher exists
                voucher_exists = debit_note.voucher_id is not None
                
                if not voucher_exists:
                    return {
                        'valid': True,
                        'voucher_exists': False,
                        'message': 'No voucher created yet'
                    }
                
                # Get voucher details
                voucher = session.query(Voucher).filter_by(
                    id=debit_note.voucher_id, tenant_id=tenant_id
                ).first()
                
                if not voucher:
                    return {
                        'valid': False,
                        'error': 'Voucher reference exists but voucher not found',
                        'voucher_exists': False
                    }
                
                # Get voucher lines
                voucher_lines = session.query(VoucherLine).filter_by(
                    voucher_id=voucher.id, tenant_id=tenant_id
                ).all()
                
                # Validate accounting balance
                total_debit = sum(line.debit_base or 0 for line in voucher_lines)
                total_credit = sum(line.credit_base or 0 for line in voucher_lines)
                
                accounting_validation = {
                    'balanced': abs(total_debit - total_credit) < 0.01,
                    'total_debit': total_debit,
                    'total_credit': total_credit,
                    'difference': total_debit - total_credit,
                    'line_count': len(voucher_lines)
                }
                
                return {
                    'valid': True,
                    'voucher_exists': True,
                    'voucher_id': voucher.id,
                    'voucher_number': voucher.voucher_number,
                    'accounting_validation': accounting_validation,
                    'voucher_lines': [{
                        'line_no': line.line_no,
                        'account_id': line.account_id,
                        'description': line.description,
                        'debit_base': line.debit_base,
                        'credit_base': line.credit_base
                    } for line in voucher_lines]
                }
                
            except Exception as e:
                return {
                    'valid': False,
                    'error': f'Validation error: {str(e)}',
                    'voucher_exists': False
                }
    
    @staticmethod
    def get_account_configurations(tenant_id: int) -> Dict[str, Any]:
        """Get account configurations for debit note"""
        with db_manager.get_session() as session:
            try:
                # Get relevant account configurations
                configs = session.query(
                    AccountConfigurationKey.code,
                    AccountConfigurationKey.name,
                    AccountConfiguration.account_id
                ).join(
                    AccountConfiguration, 
                    AccountConfiguration.config_key_id == AccountConfigurationKey.id
                ).filter(
                    AccountConfiguration.tenant_id == tenant_id,
                    AccountConfigurationKey.code.in_(['PURCHASES', 'ACCOUNTS_PAYABLE', 'GST_INPUT']),
                    AccountConfiguration.is_deleted == False,
                    AccountConfigurationKey.is_active == True
                ).all()
                
                return {
                    'configurations': [{
                        'code': config.code,
                        'name': config.name,
                        'account_id': config.account_id
                    } for config in configs],
                    'configured_accounts': {config.code: config.account_id for config in configs}
                }
                
            except Exception as e:
                return {
                    'error': f'Error retrieving account configurations: {str(e)}',
                    'configurations': [],
                    'configured_accounts': {}
                }
    
    @staticmethod
    def validate_debit_note_data(note_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate debit note data before creation"""
        errors = []
        warnings = []
        
        # Required fields validation
        required_fields = ['note_number', 'note_date', 'supplier_id', 'total_amount_base', 'items']
        for field in required_fields:
            if not note_data.get(field):
                errors.append(f'{field} is required')
        
        # Items validation
        if note_data.get('items'):
            if not isinstance(note_data['items'], list) or len(note_data['items']) == 0:
                errors.append('At least one item is required')
            else:
                for i, item in enumerate(note_data['items']):
                    item_errors = DebitNoteValidationService._validate_item_data(item, i + 1)
                    errors.extend(item_errors)
        
        # Amount validations
        if note_data.get('total_amount_base', 0) <= 0:
            errors.append('Total amount must be greater than zero')
        
        # Date validations
        if note_data.get('due_date') and note_data.get('note_date'):
            if note_data['due_date'] < note_data['note_date']:
                errors.append('Due date cannot be before note date')
        
        # Currency validations
        if note_data.get('foreign_currency_id'):
            if not note_data.get('exchange_rate') or note_data['exchange_rate'] <= 0:
                errors.append('Exchange rate is required and must be greater than zero for foreign currency')
            
            # Check if foreign currency amounts are provided
            foreign_fields = ['subtotal_foreign', 'tax_amount_foreign', 'total_amount_foreign']
            if not any(note_data.get(field) for field in foreign_fields):
                warnings.append('Foreign currency amounts not provided')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @staticmethod
    def _validate_item_data(item_data: Dict[str, Any], line_no: int) -> List[str]:
        """Validate individual item data"""
        errors = []
        
        # Required item fields
        required_fields = ['product_id', 'quantity', 'unit_price_base', 'taxable_amount_base', 'total_amount_base']
        for field in required_fields:
            if not item_data.get(field):
                errors.append(f'Item {line_no}: {field} is required')
        
        # Quantity validation
        if item_data.get('quantity', 0) <= 0:
            errors.append(f'Item {line_no}: Quantity must be greater than zero')
        
        # Price validation
        if item_data.get('unit_price_base', 0) < 0:
            errors.append(f'Item {line_no}: Unit price cannot be negative')
        
        # Amount validation
        if item_data.get('total_amount_base', 0) <= 0:
            errors.append(f'Item {line_no}: Total amount must be greater than zero')
        
        # GST validation
        gst_rates = ['cgst_rate', 'sgst_rate', 'igst_rate', 'ugst_rate', 'cess_rate']
        for rate_field in gst_rates:
            if item_data.get(rate_field, 0) < 0 or item_data.get(rate_field, 0) > 100:
                errors.append(f'Item {line_no}: {rate_field} must be between 0 and 100')
        
        return errors