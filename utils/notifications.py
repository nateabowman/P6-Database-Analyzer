"""Notification system for alerts and critical issues."""

from typing import List, Dict, Any, Optional
from utils.logging_config import get_logger

logger = get_logger(__name__)


class NotificationManager:
    """Manages notifications for critical issues."""
    
    def __init__(self):
        self.notifications: List[Dict[str, Any]] = []
    
    def send_notification(self, level: str, message: str, details: Optional[Dict] = None):
        """
        Send a notification.
        
        Args:
            level: Notification level (info, warning, error, critical)
            message: Notification message
            details: Additional details
        """
        notification = {
            'level': level,
            'message': message,
            'details': details or {},
            'timestamp': None  # Will be set by handler
        }
        
        self.notifications.append(notification)
        logger.info(f"Notification [{level}]: {message}")
    
    def get_notifications(self, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get notifications.
        
        Args:
            level: Filter by level (optional)
        
        Returns:
            List of notifications
        """
        if level:
            return [n for n in self.notifications if n['level'] == level]
        return self.notifications


# Global notification manager
_notification_manager: Optional[NotificationManager] = None


def get_notification_manager() -> NotificationManager:
    """Get the global notification manager."""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager

