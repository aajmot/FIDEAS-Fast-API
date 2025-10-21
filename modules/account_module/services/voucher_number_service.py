"""
Centralized Voucher Number Generation Service
"""
from datetime import datetime

class VoucherNumberService:
    @staticmethod
    def generate_voucher_number(prefix: str, tenant_id: int) -> str:
        """
        Generate voucher number in format: Prefix[TenantId]ddmmyyyyhhmmssfff
        Example: JV-121102025133917602
        
        Args:
            prefix: Voucher type prefix (e.g., 'JV-', 'SAL-')
            tenant_id: Tenant ID
            
        Returns:
            Generated voucher number
        """
        now = datetime.now()
        timestamp = now.strftime('%d%m%Y%H%M%S') + f"{now.microsecond // 1000:03d}"
        return f"{prefix}{tenant_id}{timestamp}"
