"""Audit logging system for compliance and security."""

from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import json
from pathlib import Path
from utils.logging_config import get_logger
from storage.models import Base
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON

logger = get_logger(__name__)


class AuditEventType(Enum):
    """Types of audit events."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_EVENT = "security_event"
    SYSTEM_EVENT = "system_event"


class AuditLog(Base):
    """SQLAlchemy model for audit logs."""
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    event_type = Column(String(50), nullable=False)
    user_id = Column(String(255))
    username = Column(String(255))
    action = Column(String(100), nullable=False)
    resource = Column(String(255))
    resource_id = Column(String(255))
    ip_address = Column(String(45))  # IPv6 support
    user_agent = Column(String(500))
    status = Column(String(20))  # success, failure, error
    details = Column(JSON)
    metadata = Column(JSON)


class AuditLogger:
    """Manages audit logging for compliance."""
    
    def __init__(self, storage_type: str = "database"):
        """
        Initialize audit logger.
        
        Args:
            storage_type: Storage type ('database' or 'file')
        """
        self.storage_type = storage_type
        self.audit_dir = Path.home() / ".p6_analyzer" / "audit"
        if storage_type == "file":
            self.audit_dir.mkdir(parents=True, exist_ok=True)
    
    def log_event(
        self,
        event_type: AuditEventType,
        action: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        resource: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log an audit event.
        
        Args:
            event_type: Type of audit event
            action: Action performed
            user_id: User ID
            username: Username
            resource: Resource accessed/modified
            resource_id: Resource identifier
            ip_address: IP address of request
            user_agent: User agent string
            status: Event status (success, failure, error)
            details: Additional details
            metadata: Additional metadata
        """
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type.value,
            'user_id': user_id,
            'username': username,
            'action': action,
            'resource': resource,
            'resource_id': resource_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'status': status,
            'details': details or {},
            'metadata': metadata or {}
        }
        
        if self.storage_type == "file":
            self._log_to_file(audit_entry)
        else:
            self._log_to_database(audit_entry)
        
        logger.info(f"Audit event: {event_type.value} - {action} by {username}")
    
    def _log_to_file(self, entry: Dict[str, Any]):
        """Log audit entry to file."""
        try:
            date_str = datetime.utcnow().strftime("%Y-%m-%d")
            audit_file = self.audit_dir / f"audit_{date_str}.jsonl"
            
            with open(audit_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, default=str) + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit log: {str(e)}")
    
    def _log_to_database(self, entry: Dict[str, Any]):
        """Log audit entry to database."""
        try:
            from storage.database import SessionLocal
            db = SessionLocal()
            try:
                audit_log = AuditLog(
                    timestamp=datetime.fromisoformat(entry['timestamp']),
                    event_type=entry['event_type'],
                    user_id=entry.get('user_id'),
                    username=entry.get('username'),
                    action=entry['action'],
                    resource=entry.get('resource'),
                    resource_id=entry.get('resource_id'),
                    ip_address=entry.get('ip_address'),
                    user_agent=entry.get('user_agent'),
                    status=entry['status'],
                    details=entry.get('details'),
                    metadata=entry.get('metadata')
                )
                db.add(audit_log)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to write audit log to database: {str(e)}")
    
    def query_audit_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Query audit logs with filters.
        
        Args:
            start_date: Start date filter
            end_date: End date filter
            event_type: Event type filter
            user_id: User ID filter
            resource: Resource filter
            limit: Maximum number of results
        
        Returns:
            List of audit log entries
        """
        # Implementation would query database or files
        # This is a placeholder
        return []


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger

