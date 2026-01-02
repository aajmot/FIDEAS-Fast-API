from modules.inventory_module.models.entities import Product, HsnCode
from modules.admin_module.services.base_service import BaseService
from core.database.connection import db_manager
from core.shared.utils.session_manager import session_manager
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from decimal import Decimal, InvalidOperation


class ProductService(BaseService):
    def __init__(self):
        super().__init__(Product)

    def _normalize_commission_type(self, commission_type):
        if commission_type is None:
            return None
        if isinstance(commission_type, str):
            ct = commission_type.strip().upper()
            if ct == 'PERCENTAGE':
                return 'PERCENTAGE'
            if ct == 'FIXED':
                return 'FIXED'
        return commission_type

    def get_by_id(self, entity_id: int, include_barcode: bool = False):
        product = super().get_by_id(entity_id)
        if product and include_barcode:
            from core.shared.utils.barcode_utils import BarcodeGenerator
            from core.shared.utils.logger import logger
            try:
                product_dict = product.__dict__.copy()
                product_dict.pop('_sa_instance_state', None)
                if product.product_code:
                    product_dict['barcode'] = BarcodeGenerator.generate_barcode(product.product_code)
                    qr_data = f"PRODUCT:{product.product_code}|NAME:{product.product_name}"
                    product_dict['qr_code'] = BarcodeGenerator.generate_qr_code(qr_data)
                else:
                    product_dict['barcode'] = None
                    product_dict['qr_code'] = None
                return product_dict
            except Exception as e:
                logger.error(f"Barcode generation failed: {str(e)}", self.module_name)
        return product

    def _normalize_commission_type(self, commission_type):
        if commission_type is None:
            return None
        if isinstance(commission_type, str):
            ct = commission_type.strip().upper()
            if ct == 'PERCENTAGE':
                return 'PERCENTAGE'
            if ct == 'FIXED':
                return 'FIXED'
        return commission_type

    def create(self, data):
        # Normalize/validate commission_type to match DB enum values (FIXED/PERCENTAGE)
        commission_type = data.get('commission_type')
        if commission_type:
            ct = self._normalize_commission_type(commission_type)
            if ct not in ['FIXED', 'PERCENTAGE']:
                raise ValueError("commission_type must be 'FIXED' or 'PERCENTAGE'")
            data['commission_type'] = ct

        # Accept legacy 'price' / 'gst_percentage' fields by mapping them to new names if present
        if 'price' in data and 'selling_price' not in data:
            data['selling_price'] = data.pop('price')
        if 'gst_percentage' in data and 'gst_rate' not in data:
            data['gst_rate'] = data.pop('gst_percentage')

        # Remove computed columns if present (DB computes them)
        data.pop('cgst_rate', None)
        data.pop('sgst_rate', None)

        # Convert numeric-like fields safely
        def _to_decimal(val, default=None):
            if val is None or val == '':
                return default
            try:
                return Decimal(str(val))
            except (InvalidOperation, ValueError, TypeError):
                return default

        for nfield in ('mrp_price', 'selling_price', 'cost_price', 'gst_rate', 'igst_rate', 'cess_rate', 'commission_value', 'reorder_level', 'danger_level', 'min_stock', 'max_stock'):
            if nfield in data:
                data[nfield] = _to_decimal(data.get(nfield), data.get(nfield))

        # Map hsn_code -> hsn_id if provided
        tenant_id = session_manager.get_current_tenant_id()
        if 'hsn_code' in data and not data.get('hsn_id'):
            code_val = (data.get('hsn_code') or '').strip()
            if code_val:
                with db_manager.get_session() as session:
                    hsn = session.query(HsnCode).filter(HsnCode.code == code_val, HsnCode.tenant_id == tenant_id).first()
                    if hsn:
                        data['hsn_id'] = hsn.id
                    else:
                        hsn = HsnCode(tenant_id=tenant_id, code=code_val)
                        session.add(hsn)
                        try:
                            session.flush()
                            data['hsn_id'] = hsn.id
                        except IntegrityError:
                            # Another process likely inserted the same HSN concurrently.
                            # Roll back this transaction's pending changes and re-query.
                            session.rollback()
                            existing = session.query(HsnCode).filter(HsnCode.code == code_val, HsnCode.tenant_id == tenant_id).first()
                            if existing:
                                data['hsn_id'] = existing.id

        # Ensure tenant_id is set for created product
        if tenant_id and not data.get('tenant_id'):
            data['tenant_id'] = tenant_id

        return super().create(data)

    def update(self, entity_id, data):
        commission_type = data.get('commission_type')
        if commission_type:
            ct = self._normalize_commission_type(commission_type)
            if ct not in ['FIXED', 'PERCENTAGE']:
                raise ValueError("commission_type must be 'FIXED' or 'PERCENTAGE'")
            data['commission_type'] = ct

        # Map legacy fields when updating
        if 'price' in data and 'selling_price' not in data:
            data['selling_price'] = data.pop('price')
        if 'gst_percentage' in data and 'gst_rate' not in data:
            data['gst_rate'] = data.pop('gst_percentage')

        # Remove computed columns if present
        data.pop('cgst_rate', None)
        data.pop('sgst_rate', None)

        # Convert numeric-like fields safely
        def _to_decimal(val, default=None):
            if val is None or val == '':
                return default
            try:
                return Decimal(str(val))
            except (InvalidOperation, ValueError, TypeError):
                return default

        for nfield in ('mrp_price', 'selling_price', 'cost_price', 'gst_rate', 'igst_rate', 'cess_rate', 'commission_value', 'reorder_level', 'danger_level', 'min_stock', 'max_stock'):
            if nfield in data:
                data[nfield] = _to_decimal(data.get(nfield), data.get(nfield))

        # Map hsn_code -> hsn_id if provided
        tenant_id = session_manager.get_current_tenant_id()
        if 'hsn_code' in data and not data.get('hsn_id'):
            code_val = (data.get('hsn_code') or '').strip()
            if code_val:
                with db_manager.get_session() as session:
                    hsn = session.query(HsnCode).filter(HsnCode.code == code_val, HsnCode.tenant_id == tenant_id).first()
                    if hsn:
                        data['hsn_id'] = hsn.id
                    else:
                        hsn = HsnCode(tenant_id=tenant_id, code=code_val)
                        session.add(hsn)
                        try:
                            session.flush()
                            data['hsn_id'] = hsn.id
                        except IntegrityError:
                            session.rollback()
                            existing = session.query(HsnCode).filter(HsnCode.code == code_val, HsnCode.tenant_id == tenant_id).first()
                            if existing:
                                data['hsn_id'] = existing.id

        return super().update(entity_id, data)