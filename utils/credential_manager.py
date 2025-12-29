"""Credential management for secure storage of database credentials."""

import keyring
import json
from typing import Dict, Any, Optional
from pathlib import Path
from utils.logging_config import get_logger
from utils.encryption import get_encryption_manager
from utils.exceptions import CredentialError

logger = get_logger(__name__)


class CredentialManager:
    """Manages secure storage and retrieval of credentials."""
    
    SERVICE_NAME = "p6_database_analyzer"
    
    def __init__(self, storage_type: str = "keyring"):
        """
        Initialize credential manager.
        
        Args:
            storage_type: Storage type ('keyring' or 'encrypted_file')
        """
        self.storage_type = storage_type
        self.encryption = get_encryption_manager()
        self.credentials_dir = Path.home() / ".p6_analyzer" / "credentials"
        
        if storage_type == "encrypted_file":
            self.credentials_dir.mkdir(parents=True, exist_ok=True)
    
    def save_connection_profile(
        self,
        profile_name: str,
        db_type: str,
        host: str,
        port: int,
        service: str,
        username: str,
        password: str,
        **kwargs
    ):
        """
        Save a connection profile.
        
        Args:
            profile_name: Name of the connection profile
            db_type: Database type ('oracle' or 'mssql')
            host: Host/server name
            port: Port number
            service: Service name (Oracle) or database name (MSSQL)
            username: Username
            password: Password
            **kwargs: Additional connection parameters
        """
        try:
            profile_data = {
                'db_type': db_type,
                'host': host,
                'port': port,
                'service': service,
                'username': username,
                'password': password,
                **kwargs
            }
            
            if self.storage_type == "keyring":
                # Store password separately in keyring, rest in encrypted file
                keyring.set_password(self.SERVICE_NAME, f"{profile_name}_password", password)
                
                # Store other data encrypted
                profile_data_no_password = {k: v for k, v in profile_data.items() if k != 'password'}
                encrypted_data = self.encryption.encrypt(json.dumps(profile_data_no_password))
                
                # Store in keyring as well (or use a config file)
                keyring.set_password(self.SERVICE_NAME, f"{profile_name}_data", encrypted_data)
            
            elif self.storage_type == "encrypted_file":
                # Encrypt the entire profile
                encrypted_data = self.encryption.encrypt(json.dumps(profile_data))
                
                profile_file = self.credentials_dir / f"{profile_name}.enc"
                profile_file.write_text(encrypted_data)
            
            logger.info(f"Connection profile '{profile_name}' saved")
        
        except Exception as e:
            logger.error(f"Failed to save connection profile: {str(e)}")
            raise CredentialError(f"Failed to save connection profile: {str(e)}")
    
    def load_connection_profile(self, profile_name: str) -> Dict[str, Any]:
        """
        Load a connection profile.
        
        Args:
            profile_name: Name of the connection profile
        
        Returns:
            Dictionary with connection parameters
        """
        try:
            if self.storage_type == "keyring":
                # Get password from keyring
                password = keyring.get_password(self.SERVICE_NAME, f"{profile_name}_password")
                
                # Get other data
                encrypted_data = keyring.get_password(self.SERVICE_NAME, f"{profile_name}_data")
                if encrypted_data:
                    decrypted_data = self.encryption.decrypt(encrypted_data)
                    profile_data = json.loads(decrypted_data)
                    profile_data['password'] = password
                else:
                    # Fallback: try to get from old format
                    profile_data = {'password': password}
            
            elif self.storage_type == "encrypted_file":
                profile_file = self.credentials_dir / f"{profile_name}.enc"
                if not profile_file.exists():
                    raise CredentialError(f"Profile '{profile_name}' not found")
                
                encrypted_data = profile_file.read_text()
                decrypted_data = self.encryption.decrypt(encrypted_data)
                profile_data = json.loads(decrypted_data)
            
            logger.info(f"Connection profile '{profile_name}' loaded")
            return profile_data
        
        except Exception as e:
            logger.error(f"Failed to load connection profile: {str(e)}")
            raise CredentialError(f"Failed to load connection profile: {str(e)}")
    
    def delete_connection_profile(self, profile_name: str):
        """
        Delete a connection profile.
        
        Args:
            profile_name: Name of the connection profile
        """
        try:
            if self.storage_type == "keyring":
                try:
                    keyring.delete_password(self.SERVICE_NAME, f"{profile_name}_password")
                    keyring.delete_password(self.SERVICE_NAME, f"{profile_name}_data")
                except keyring.errors.PasswordDeleteError:
                    pass  # Already deleted
            
            elif self.storage_type == "encrypted_file":
                profile_file = self.credentials_dir / f"{profile_name}.enc"
                if profile_file.exists():
                    profile_file.unlink()
            
            logger.info(f"Connection profile '{profile_name}' deleted")
        
        except Exception as e:
            logger.error(f"Failed to delete connection profile: {str(e)}")
            raise CredentialError(f"Failed to delete connection profile: {str(e)}")
    
    def list_profiles(self) -> list:
        """
        List all saved connection profiles.
        
        Returns:
            List of profile names
        """
        try:
            if self.storage_type == "keyring":
                # Keyring doesn't have a direct list method
                # This is a limitation - we'd need to maintain a separate index
                return []
            
            elif self.storage_type == "encrypted_file":
                profiles = []
                for file in self.credentials_dir.glob("*.enc"):
                    profiles.append(file.stem)
                return profiles
        
        except Exception as e:
            logger.error(f"Failed to list profiles: {str(e)}")
            return []


# Global credential manager instance
_credential_manager: Optional[CredentialManager] = None


def get_credential_manager() -> CredentialManager:
    """Get the global credential manager instance."""
    global _credential_manager
    if _credential_manager is None:
        from config.config_manager import get_config
        config = get_config()
        storage_type = config.get('security.credential_storage', 'keyring')
        _credential_manager = CredentialManager(storage_type=storage_type)
    return _credential_manager

