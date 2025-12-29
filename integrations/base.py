"""Base class for integrations."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from utils.logging_config import get_logger

logger = get_logger(__name__)


class IntegrationBase(ABC):
    """Base class for all integrations."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize integration.
        
        Args:
            config: Integration configuration
        """
        self.config = config
        self.enabled = config.get('enabled', True)
    
    @abstractmethod
    def send_notification(self, message: str, details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send a notification.
        
        Args:
            message: Notification message
            details: Additional details
        
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test integration connection.
        
        Returns:
            True if connection successful
        """
        pass

