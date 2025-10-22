"""
GST Calculation Service
"""
from decimal import Decimal, ROUND_HALF_UP

class GSTService:
    """Service for GST calculations"""
    
    @staticmethod
    def calculate_gst(subtotal: float, gst_rate: float, is_interstate: bool = False):
        """
        Calculate GST amounts
        
        Args:
            subtotal: Taxable amount
            gst_rate: Total GST rate (e.g., 18 for 18%)
            is_interstate: True for IGST, False for CGST+SGST
            
        Returns:
            dict: GST breakdown
        """
        subtotal_decimal = Decimal(str(subtotal))
        gst_rate_decimal = Decimal(str(gst_rate))
        
        if is_interstate:
            # Interstate - IGST only
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
            # Intrastate - CGST + SGST (split equally)
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
        """
        Calculate GST from total amount (reverse calculation)
        
        Args:
            total_with_gst: Total amount including GST
            gst_rate: Total GST rate
            is_interstate: True for IGST, False for CGST+SGST
            
        Returns:
            dict: GST breakdown
        """
        total_decimal = Decimal(str(total_with_gst))
        gst_rate_decimal = Decimal(str(gst_rate))
        
        # Subtotal = Total / (1 + GST%)
        subtotal = (total_decimal / (1 + gst_rate_decimal / 100)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return GSTService.calculate_gst(float(subtotal), gst_rate, is_interstate)
