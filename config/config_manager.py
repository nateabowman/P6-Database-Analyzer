"""Configuration manager for P6 Database Analyzer."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from utils.logging_config import get_logger
from utils.exceptions import ConfigurationError

logger = get_logger(__name__)


class ConfigManager:
    """Manages application configuration from files and environment variables."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file (default: config/settings.yaml)
        """
        if config_file is None:
            config_file = os.path.join(
                Path(__file__).parent.parent,
                'config',
                'settings.yaml'
            )
        
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from file and environment variables."""
        # Load from file if it exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f) or {}
                logger.info(f"Configuration loaded from {self.config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file {self.config_file}: {str(e)}")
                self.config = {}
        else:
            logger.info(f"Config file not found at {self.config_file}, using defaults")
            self.config = {}
        
        # Override with environment variables
        self._load_from_env()
        
        # Set defaults
        self._set_defaults()
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        # Database connection settings
        if os.getenv('DB_TYPE'):
            self.config['database'] = self.config.get('database', {})
            self.config['database']['type'] = os.getenv('DB_TYPE')
        
        if os.getenv('DB_HOST'):
            self.config['database'] = self.config.get('database', {})
            self.config['database']['host'] = os.getenv('DB_HOST')
        
        if os.getenv('DB_PORT'):
            self.config['database'] = self.config.get('database', {})
            self.config['database']['port'] = int(os.getenv('DB_PORT'))
        
        # Logging settings
        if os.getenv('LOG_LEVEL'):
            self.config['logging'] = self.config.get('logging', {})
            self.config['logging']['level'] = os.getenv('LOG_LEVEL')
        
        if os.getenv('LOG_JSON'):
            self.config['logging'] = self.config.get('logging', {})
            self.config['logging']['json'] = os.getenv('LOG_JSON').lower() == 'true'
        
        # Analysis settings
        if os.getenv('ANALYSIS_TIMEOUT'):
            self.config['analysis'] = self.config.get('analysis', {})
            self.config['analysis']['timeout'] = int(os.getenv('ANALYSIS_TIMEOUT'))
    
    def _set_defaults(self):
        """Set default configuration values."""
        defaults = {
            'logging': {
                'level': 'INFO',
                'json': False,
                'log_dir': 'logs',
                'max_bytes': 10 * 1024 * 1024,  # 10MB
                'backup_count': 5
            },
            'database': {
                'connection_timeout': 30,
                'query_timeout': 300,
                'retry_attempts': 3,
                'retry_delay': 1
            },
            'analysis': {
                'timeout': 3600,  # 1 hour
                'parallel': False,
                'cache_enabled': True,
                'cache_ttl': 3600  # 1 hour
            },
            'security': {
                'credential_storage': 'keyring',
                'tls_enabled': False,
                'tls_verify': True
            }
        }
        
        for section, values in defaults.items():
            if section not in self.config:
                self.config[section] = values
            else:
                for key, value in values.items():
                    if key not in self.config[section]:
                        self.config[section][key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'database.host')
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """
        Set configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'database.host')
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        logger.debug(f"Configuration set: {key} = {value}")
    
    def save_config(self, file_path: Optional[str] = None):
        """
        Save configuration to file.
        
        Args:
            file_path: Path to save config (default: original config file)
        """
        if file_path is None:
            file_path = self.config_file
        
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Configuration saved to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {str(e)}")
            raise ConfigurationError(f"Failed to save configuration: {str(e)}")
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return self.config.get('database', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.config.get('logging', {})
    
    def get_analysis_config(self) -> Dict[str, Any]:
        """Get analysis configuration."""
        return self.config.get('analysis', {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        return self.config.get('security', {})


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

