from cryptography.fernet import Fernet
import base64
import os
from typing import Optional


class CryptoUtils:
    """Utility for encrypting/decrypting sensitive data"""
    
    def __init__(self):
        # Get secret key from environment or generate one
        secret_key = os.getenv('SECRET_KEY', 'default_secret_key_change_in_production')
        # Ensure key is 32 bytes for Fernet
        key = base64.urlsafe_b64encode(secret_key.encode().ljust(32)[:32])
        self.cipher = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data and return base64 encoded string"""
        try:
            encrypted = self.cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            raise ValueError(f"Encryption failed: {str(e)}")
    
    def decrypt(self, encrypted_data: str) -> Optional[str]:
        """Decrypt base64 encoded encrypted string"""
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception:
            return None
    
    def generate_test_result_url(self, result_number: str) -> str:
        """Generate public URL for test result with encrypted result_number"""
        encrypted_result_no = self.encrypt(result_number)
        web_app_url = os.getenv('WEB_APP_URL', 'http://localhost:3000')
        return f"{web_app_url}/public/health/test-result/{encrypted_result_no}"

    def generate_appointment_invoice_url(self, number: str) -> str:
        """Generate public URL for appointment invoice with encrypted number"""
        encrypted_data = self.encrypt(number)
        web_app_url = os.getenv('WEB_APP_URL', 'http://localhost:3000')
        return f"{web_app_url}/public/health/appointment-invoice/{encrypted_data}"


# Singleton instance
crypto_utils = CryptoUtils()
