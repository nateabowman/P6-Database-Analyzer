"""Alerting system for monitoring."""

from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from datetime import datetime
from utils.logging_config import get_logger
from utils.notifications import get_notification_manager

logger = get_logger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertRule:
    """Defines an alert rule."""
    
    def __init__(
        self,
        name: str,
        condition: Callable[[Dict[str, Any]], bool],
        severity: AlertSeverity,
        message: str,
        notification_channels: List[str] = None
    ):
        self.name = name
        self.condition = condition
        self.severity = severity
        self.message = message
        self.notification_channels = notification_channels or []
        self.enabled = True


class AlertManager:
    """Manages alerts and notifications."""
    
    def __init__(self):
        self.rules: List[AlertRule] = []
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
        self.notification_manager = get_notification_manager()
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Set up default alert rules."""
        # High error rate
        self.add_rule(AlertRule(
            name="high_error_rate",
            condition=lambda metrics: metrics.get("error_rate", 0) > 0.1,
            severity=AlertSeverity.ERROR,
            message="Error rate exceeds 10%"
        ))
        
        # High response time
        self.add_rule(AlertRule(
            name="high_response_time",
            condition=lambda metrics: metrics.get("avg_response_time", 0) > 5.0,
            severity=AlertSeverity.WARNING,
            message="Average response time exceeds 5 seconds"
        ))
        
        # Database connection issues
        self.add_rule(AlertRule(
            name="database_connection_issues",
            condition=lambda metrics: metrics.get("db_connection_failures", 0) > 5,
            severity=AlertSeverity.CRITICAL,
            message="Multiple database connection failures detected"
        ))
    
    def add_rule(self, rule: AlertRule):
        """Add an alert rule."""
        self.rules.append(rule)
        logger.info(f"Alert rule added: {rule.name}")
    
    def evaluate_metrics(self, metrics: Dict[str, Any]):
        """
        Evaluate metrics against alert rules.
        
        Args:
            metrics: Current metrics dictionary
        """
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            try:
                if rule.condition(metrics):
                    self._trigger_alert(rule, metrics)
            except Exception as e:
                logger.error(f"Error evaluating alert rule {rule.name}: {str(e)}")
    
    def _trigger_alert(self, rule: AlertRule, metrics: Dict[str, Any]):
        """Trigger an alert."""
        alert_id = f"{rule.name}_{datetime.utcnow().timestamp()}"
        
        alert = {
            "id": alert_id,
            "rule_name": rule.name,
            "severity": rule.severity.value,
            "message": rule.message,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics
        }
        
        self.active_alerts[alert_id] = alert
        
        # Send notification
        self.notification_manager.send_notification(
            level=rule.severity.value,
            message=rule.message,
            details=alert
        )
        
        logger.warning(f"Alert triggered: {rule.name} - {rule.message}")
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Dict[str, Any]]:
        """Get active alerts, optionally filtered by severity."""
        alerts = list(self.active_alerts.values())
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity.value]
        return alerts
    
    def resolve_alert(self, alert_id: str):
        """Resolve an alert."""
        if alert_id in self.active_alerts:
            del self.active_alerts[alert_id]
            logger.info(f"Alert resolved: {alert_id}")


# Global alert manager
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get the global alert manager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager

