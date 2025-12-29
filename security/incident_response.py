"""Security incident response system."""

from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
from utils.logging_config import get_logger
from utils.audit import get_audit_logger, AuditEventType

logger = get_logger(__name__)


class IncidentSeverity(Enum):
    """Incident severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentType(Enum):
    """Types of security incidents."""
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    BRUTE_FORCE = "brute_force"
    SQL_INJECTION_ATTEMPT = "sql_injection"
    XSS_ATTEMPT = "xss"
    DATA_BREACH = "data_breach"
    MALWARE = "malware"
    DDoS = "ddos"
    PRIVILEGE_ESCALATION = "privilege_escalation"


class SecurityIncident:
    """Represents a security incident."""
    
    def __init__(
        self,
        incident_type: IncidentType,
        severity: IncidentSeverity,
        description: str,
        source_ip: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.incident_type = incident_type
        self.severity = severity
        self.description = description
        self.source_ip = source_ip
        self.user_id = user_id
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        self.status = "open"
        self.resolution = None


class IncidentResponseManager:
    """Manages security incident response."""
    
    def __init__(self):
        self.incidents: List[SecurityIncident] = []
        self.audit_logger = get_audit_logger()
    
    def report_incident(
        self,
        incident_type: IncidentType,
        severity: IncidentSeverity,
        description: str,
        source_ip: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> SecurityIncident:
        """
        Report a security incident.
        
        Args:
            incident_type: Type of incident
            severity: Severity level
            description: Incident description
            source_ip: Source IP address
            user_id: User ID if applicable
            details: Additional details
        
        Returns:
            Created incident
        """
        incident = SecurityIncident(
            incident_type, severity, description, source_ip, user_id, details
        )
        
        self.incidents.append(incident)
        
        # Log to audit trail
        self.audit_logger.log_event(
            event_type=AuditEventType.SECURITY_EVENT,
            action=f"Security incident: {incident_type.value}",
            user_id=user_id,
            ip_address=source_ip,
            status="failure",
            details={
                'incident_type': incident_type.value,
                'severity': severity.value,
                'description': description
            }
        )
        
        logger.critical(
            f"Security incident reported: {incident_type.value} - {severity.value} - {description}"
        )
        
        # Auto-response based on severity
        if severity == IncidentSeverity.CRITICAL:
            self._handle_critical_incident(incident)
        elif severity == IncidentSeverity.HIGH:
            self._handle_high_incident(incident)
        
        return incident
    
    def _handle_critical_incident(self, incident: SecurityIncident):
        """Handle critical security incidents."""
        logger.critical(f"CRITICAL incident detected: {incident.description}")
        # Implement automatic response actions:
        # - Block IP address
        # - Disable user account
        # - Send alerts
        # - Escalate to security team
    
    def _handle_high_incident(self, incident: SecurityIncident):
        """Handle high severity security incidents."""
        logger.warning(f"HIGH severity incident: {incident.description}")
        # Implement response actions
    
    def get_incidents(
        self,
        severity: Optional[IncidentSeverity] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[SecurityIncident]:
        """
        Get incidents with filters.
        
        Args:
            severity: Filter by severity
            status: Filter by status
            limit: Maximum number of results
        
        Returns:
            List of incidents
        """
        filtered = self.incidents
        
        if severity:
            filtered = [i for i in filtered if i.severity == severity]
        
        if status:
            filtered = [i for i in filtered if i.status == status]
        
        return filtered[:limit]
    
    def resolve_incident(self, incident_id: int, resolution: str):
        """
        Resolve a security incident.
        
        Args:
            incident_id: Incident ID
            resolution: Resolution description
        """
        if 0 <= incident_id < len(self.incidents):
            incident = self.incidents[incident_id]
            incident.status = "resolved"
            incident.resolution = resolution
            logger.info(f"Incident {incident_id} resolved: {resolution}")


# Global incident response manager
_incident_manager: Optional[IncidentResponseManager] = None


def get_incident_manager() -> IncidentResponseManager:
    """Get the global incident response manager."""
    global _incident_manager
    if _incident_manager is None:
        _incident_manager = IncidentResponseManager()
    return _incident_manager

