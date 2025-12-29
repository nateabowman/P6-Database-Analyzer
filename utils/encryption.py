"""Encryption utilities for sensitive data."""

import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Optional
import os
from utils.logging_config import get_logger

logger = get_logger(__name__)


class EncryptionManager:
    """Manages encryption and decryption of sensitive data."""
    
    def __init__(self, key: Optional[bytes] = None):
        """
        Initialize encryption manager.
        
        Args:
            key: Encryption key (if None, will be generated or loaded from env)
        """
        if key is None:
            key = self._get_or_generate_key()
        
        self.key = key
        self.cipher = Fernet(key)
    
    def _get_or_generate_key(self) -> bytes:
        """
        Get encryption key from environment or generate a new one.
        
        Returns:
            Encryption key bytes
        """
        # Try to get from environment
        key_env = os.getenv('P6_ENCRYPTION_KEY')
        if key_env:
            try:
                return base64.urlsafe_b64decode(key_env.encode())
            except Exception as e:
                logger.warning(f"Failed to decode encryption key from env: {str(e)}")
        
        # Generate from password if available
        password = os.getenv('P6_ENCRYPTION_PASSWORD', 'default_change_in_production')
        salt = os.getenv('P6_ENCRYPTION_SALT', 'default_salt_change_in_production').encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt a string.
        
        Args:
            data: String to encrypt
        
        Returns:
            Encrypted string (base64 encoded)
        """
        try:
            encrypted = self.cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt a string.
        
        Args:
            encrypted_data: Encrypted string (base64 encoded)
        
        Returns:
            Decrypted string
        """
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise
    
    def encrypt_dict(self, data: Dict[str, Any], keys_to_encrypt: list) -> Dict[str, Any]:
        """
        Encrypt specific keys in a dictionary.
        
        Args:
            data: Dictionary to encrypt
            keys_to_encrypt: List of keys to encrypt
        
        Returns:
            Dictionary with encrypted values
        """
        encrypted = data.copy()
        for key in keys_to_encrypt:
            if key in encrypted and encrypted[key]:
                encrypted[key] = self.encrypt(str(encrypted[key]))
        return encrypted
    
    def decrypt_dict(self, data: Dict[str, Any], keys_to_decrypt: list) -> Dict[str, Any]:
        """
        Decrypt specific keys in a dictionary.
        
        Args:
            data: Dictionary to decrypt
            keys_to_decrypt: List of keys to decrypt
        
        Returns:
            Dictionary with decrypted values
        """
        decrypted = data.copy()
        for key in keys_to_decrypt:
            if key in decrypted and decrypted[key]:
                try:
                    decrypted[key] = self.decrypt(str(decrypted[key]))
                except Exception as e:
                    logger.warning(f"Failed to decrypt {key}: {str(e)}")
        return decrypted


# Global encryption manager instance
_encryption_manager: Optional[EncryptionManager] = None


def get_encryption_manager() -> EncryptionManager:
    """Get the global encryption manager instance."""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager

