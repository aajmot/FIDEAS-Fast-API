import io
import base64
import barcode
from barcode.writer import ImageWriter
import qrcode
from typing import Optional, Literal

class BarcodeGenerator:
    """Utility for generating barcodes and QR codes as base64 strings"""
    
    
    @staticmethod
    def generate_barcode(
        data: str,
        barcode_type: Literal['code128', 'code39', 'ean13', 'ean8'] = 'code128',
        add_checksum: bool = False
    ) -> str:
        """
        Generate barcode and return as base64 data URI
        
        Args:
            data: Data to encode (alphanumeric for code128/code39, numeric for ean)
            barcode_type: Type of barcode (code128 recommended for alphanumeric)
            add_checksum: Add checksum for EAN barcodes
            
        Returns:
            Base64 data URI string (data:image/png;base64,...)
        """
        try:
            barcode_class = barcode.get_barcode_class(barcode_type)
            buffer = io.BytesIO()
            
            barcode_instance = barcode_class(data, writer=ImageWriter(), add_checksum=add_checksum)
            barcode_instance.write(buffer, options={
                'module_width': 0.2,
                'module_height': 10,
                'quiet_zone': 2,
                'font_size': 8,
                'text_distance': 3
            })
            
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            return f"data:image/png;base64,{img_base64}"
        except Exception as e:
            raise ValueError(f"Barcode generation failed: {str(e)}")
    
    @staticmethod
    def generate_qr_code(
        data: str,
        box_size: int = 10,
        border: int = 2,
        error_correction: Literal['L', 'M', 'Q', 'H'] = 'M'
    ) -> str:
        """
        Generate QR code and return as base64 data URI
        
        Args:
            data: Data to encode (can be URL, JSON, text, etc.)
            box_size: Size of each box in pixels
            border: Border size in boxes
            error_correction: L=7%, M=15%, Q=25%, H=30% error correction
            
        Returns:
            Base64 data URI string (data:image/png;base64,...)
        """
        try:
            error_levels = {
                'L': qrcode.constants.ERROR_CORRECT_L,
                'M': qrcode.constants.ERROR_CORRECT_M,
                'Q': qrcode.constants.ERROR_CORRECT_Q,
                'H': qrcode.constants.ERROR_CORRECT_H
            }
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=error_levels[error_correction],
                box_size=box_size,
                border=border
            )
            qr.add_data("http://localhost:8000/public"+data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            return f"data:image/png;base64,{img_base64}"
        except Exception as e:
            raise ValueError(f"QR code generation failed: {str(e)}")
    
    @staticmethod
    def generate_product_barcode(product_code: str) -> str:
        """Generate barcode for product code (uses Code128)"""
        return BarcodeGenerator.generate_barcode(product_code, 'code128')
    
    @staticmethod
    def generate_order_qr(order_number: str, order_id: int, base_url: Optional[str] = None) -> str:
        """Generate QR code for order with URL or order number"""
        data = f"{base_url}/orders/{order_id}" if base_url else f"ORDER:{order_number}"
        return BarcodeGenerator.generate_qr_code(data)

