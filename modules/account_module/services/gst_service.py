"""
GST Calculation and Reporting Service
"""
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from core.database.connection import db_manager
from core.shared.utils.session_manager import session_manager
from sqlalchemy import func, and_, or_

class GSTService:
    """Service for GST calculations and reporting"""
    
    @staticmethod
    def calculate_gst(subtotal: float, gst_rate: float, is_interstate: bool = False):
        """Calculate GST amounts"""
        subtotal_decimal = Decimal(str(subtotal))
        gst_rate_decimal = Decimal(str(gst_rate))
        
        if is_interstate:
            igst = (subtotal_decimal * gst_rate_decimal / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            return {
                'cgst_rate': 0,
                'sgst_rate': 0,
                'igst_rate': float(gst_rate_decimal),
                'cgst_amount': 0,
                'sgst_amount': 0,
                'igst_amount': float(igst),
                'total_gst': float(igst),
                'total_amount': float(subtotal_decimal + igst)
            }
        else:
            half_rate = gst_rate_decimal / 2
            cgst = (subtotal_decimal * half_rate / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            sgst = (subtotal_decimal * half_rate / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            total_gst = cgst + sgst
            
            return {
                'cgst_rate': float(half_rate),
                'sgst_rate': float(half_rate),
                'igst_rate': 0,
                'cgst_amount': float(cgst),
                'sgst_amount': float(sgst),
                'igst_amount': 0,
                'total_gst': float(total_gst),
                'total_amount': float(subtotal_decimal + total_gst)
            }
    
    @staticmethod
    def calculate_reverse_gst(total_with_gst: float, gst_rate: float, is_interstate: bool = False):
        """Calculate GST from total amount (reverse calculation)"""
        total_decimal = Decimal(str(total_with_gst))
        gst_rate_decimal = Decimal(str(gst_rate))
        subtotal = (total_decimal / (1 + gst_rate_decimal / 100)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return GSTService.calculate_gst(float(subtotal), gst_rate, is_interstate)
    
    @staticmethod
    def get_gstr1_data(month: int, year: int):
        """Generate GSTR-1 report from sales invoices"""
        from modules.inventory_module.models.sales_invoice_entity import SalesInvoice, SalesInvoiceItem
        from modules.inventory_module.models.customer_entity import Customer
        
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            start_date = datetime(year, month, 1)
            end_date = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
            
            # B2B invoices (with GSTIN)
            b2b_query = session.query(
                SalesInvoice.invoice_number,
                SalesInvoice.invoice_date,
                Customer.name.label('customer_name'),
                Customer.tax_id.label('gstin'),
                func.sum(SalesInvoiceItem.taxable_amount_base).label('taxable_value'),
                func.sum(SalesInvoiceItem.cgst_amount_base).label('cgst'),
                func.sum(SalesInvoiceItem.sgst_amount_base).label('sgst'),
                func.sum(SalesInvoiceItem.igst_amount_base).label('igst'),
                func.sum(SalesInvoiceItem.cess_amount_base).label('cess')
            ).join(SalesInvoiceItem).join(Customer).filter(
                SalesInvoice.tenant_id == tenant_id,
                SalesInvoice.invoice_date >= start_date,
                SalesInvoice.invoice_date < end_date,
                SalesInvoice.status.in_(['POSTED', 'PAID', 'PARTIALLY_PAID']),
                Customer.tax_id.isnot(None),
                SalesInvoice.is_deleted == False
            ).group_by(
                SalesInvoice.invoice_number,
                SalesInvoice.invoice_date,
                Customer.name,
                Customer.tax_id
            ).all()
            
            b2b_data = [{
                'invoice_number': row.invoice_number,
                'invoice_date': row.invoice_date.strftime('%d-%m-%Y'),
                'customer_name': row.customer_name,
                'gstin': row.gstin,
                'taxable_value': float(row.taxable_value or 0),
                'cgst': float(row.cgst or 0),
                'sgst': float(row.sgst or 0),
                'igst': float(row.igst or 0),
                'cess': float(row.cess or 0),
                'total_tax': float((row.cgst or 0) + (row.sgst or 0) + (row.igst or 0) + (row.cess or 0))
            } for row in b2b_query]
            
            # B2C Large (>2.5 lakh)
            b2c_large = session.query(
                func.sum(SalesInvoice.total_amount_base).label('invoice_value'),
                func.sum(SalesInvoice.subtotal_base).label('taxable_value'),
                func.sum(SalesInvoice.cgst_amount_base).label('cgst'),
                func.sum(SalesInvoice.sgst_amount_base).label('sgst'),
                func.sum(SalesInvoice.igst_amount_base).label('igst')
            ).join(Customer).filter(
                SalesInvoice.tenant_id == tenant_id,
                SalesInvoice.invoice_date >= start_date,
                SalesInvoice.invoice_date < end_date,
                SalesInvoice.status.in_(['POSTED', 'PAID', 'PARTIALLY_PAID']),
                Customer.tax_id.is_(None),
                SalesInvoice.total_amount_base > 250000,
                SalesInvoice.is_deleted == False
            ).first()
            
            # B2C Small
            b2c_small = session.query(
                func.sum(SalesInvoice.total_amount_base).label('invoice_value'),
                func.sum(SalesInvoice.subtotal_base).label('taxable_value'),
                func.sum(SalesInvoice.cgst_amount_base).label('cgst'),
                func.sum(SalesInvoice.sgst_amount_base).label('sgst'),
                func.sum(SalesInvoice.igst_amount_base).label('igst')
            ).join(Customer).filter(
                SalesInvoice.tenant_id == tenant_id,
                SalesInvoice.invoice_date >= start_date,
                SalesInvoice.invoice_date < end_date,
                SalesInvoice.status.in_(['POSTED', 'PAID', 'PARTIALLY_PAID']),
                Customer.tax_id.is_(None),
                SalesInvoice.total_amount_base <= 250000,
                SalesInvoice.is_deleted == False
            ).first()
            
            return {
                'period': f'{month:02d}-{year}',
                'b2b': b2b_data,
                'b2c_large': {
                    'invoice_value': float(b2c_large.invoice_value or 0),
                    'taxable_value': float(b2c_large.taxable_value or 0),
                    'cgst': float(b2c_large.cgst or 0),
                    'sgst': float(b2c_large.sgst or 0),
                    'igst': float(b2c_large.igst or 0)
                },
                'b2c_small': {
                    'invoice_value': float(b2c_small.invoice_value or 0),
                    'taxable_value': float(b2c_small.taxable_value or 0),
                    'cgst': float(b2c_small.cgst or 0),
                    'sgst': float(b2c_small.sgst or 0),
                    'igst': float(b2c_small.igst or 0)
                }
            }
    
    @staticmethod
    def get_gstr3b_data(month: int, year: int):
        """Generate GSTR-3B summary return"""
        from modules.inventory_module.models.sales_invoice_entity import SalesInvoice
        from modules.inventory_module.models.purchase_invoice_entity import PurchaseInvoice
        
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            start_date = datetime(year, month, 1)
            end_date = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
            
            # Outward supplies (Sales)
            outward = session.query(
                func.sum(SalesInvoice.subtotal_base).label('taxable_value'),
                func.sum(SalesInvoice.cgst_amount_base).label('cgst'),
                func.sum(SalesInvoice.sgst_amount_base).label('sgst'),
                func.sum(SalesInvoice.igst_amount_base).label('igst'),
                func.sum(SalesInvoice.cess_amount_base).label('cess')
            ).filter(
                SalesInvoice.tenant_id == tenant_id,
                SalesInvoice.invoice_date >= start_date,
                SalesInvoice.invoice_date < end_date,
                SalesInvoice.status.in_(['POSTED', 'PAID', 'PARTIALLY_PAID']),
                SalesInvoice.is_deleted == False
            ).first()
            
            # Inward supplies (Purchases) - ITC
            inward = session.query(
                func.sum(PurchaseInvoice.subtotal_base).label('taxable_value'),
                func.sum(PurchaseInvoice.cgst_amount_base).label('cgst'),
                func.sum(PurchaseInvoice.sgst_amount_base).label('sgst'),
                func.sum(PurchaseInvoice.igst_amount_base).label('igst'),
                func.sum(PurchaseInvoice.cess_amount_base).label('cess')
            ).filter(
                PurchaseInvoice.tenant_id == tenant_id,
                PurchaseInvoice.invoice_date >= start_date,
                PurchaseInvoice.invoice_date < end_date,
                PurchaseInvoice.status.in_(['POSTED', 'PAID', 'PARTIALLY_PAID']),
                PurchaseInvoice.is_deleted == False
            ).first()
            
            outward_cgst = float(outward.cgst or 0)
            outward_sgst = float(outward.sgst or 0)
            outward_igst = float(outward.igst or 0)
            outward_cess = float(outward.cess or 0)
            
            inward_cgst = float(inward.cgst or 0)
            inward_sgst = float(inward.sgst or 0)
            inward_igst = float(inward.igst or 0)
            inward_cess = float(inward.cess or 0)
            
            return {
                'period': f'{month:02d}-{year}',
                'outward_supplies': {
                    'taxable_value': float(outward.taxable_value or 0),
                    'cgst': outward_cgst,
                    'sgst': outward_sgst,
                    'igst': outward_igst,
                    'cess': outward_cess,
                    'total_tax': outward_cgst + outward_sgst + outward_igst + outward_cess
                },
                'itc_available': {
                    'cgst': inward_cgst,
                    'sgst': inward_sgst,
                    'igst': inward_igst,
                    'cess': inward_cess,
                    'total_itc': inward_cgst + inward_sgst + inward_igst + inward_cess
                },
                'net_liability': {
                    'cgst': outward_cgst - inward_cgst,
                    'sgst': outward_sgst - inward_sgst,
                    'igst': outward_igst - inward_igst,
                    'cess': outward_cess - inward_cess,
                    'total': (outward_cgst + outward_sgst + outward_igst + outward_cess) - (inward_cgst + inward_sgst + inward_igst + inward_cess)
                }
            }
