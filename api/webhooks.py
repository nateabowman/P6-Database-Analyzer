"""Webhook system for event notifications."""

import httpx
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from utils.logging_config import get_logger
from utils.audit import get_audit_logger, AuditEventType

logger = get_logger(__name__)


class WebhookEvent(Enum):
    """Webhook event types."""
    ANALYSIS_COMPLETED = "analysis.completed"
    ANALYSIS_FAILED = "analysis.failed"
    CRITICAL_ISSUE_DETECTED = "issue.critical"
    PROFILE_CREATED = "profile.created"
    PROFILE_DELETED = "profile.deleted"
    USER_CREATED = "user.created"
    SECURITY_INCIDENT = "security.incident"


class Webhook:
    """Represents a webhook subscription."""
    
    def __init__(
        self,
        url: str,
        events: List[WebhookEvent],
        secret: Optional[str] = None,
        enabled: bool = True
    ):
        self.url = url
        self.events = events
        self.secret = secret
        self.enabled = enabled
        self.created_at = datetime.utcnow()
        self.last_triggered = None
        self.failure_count = 0


class WebhookManager:
    """Manages webhook subscriptions and delivery."""
    
    def __init__(self):
        self.webhooks: List[Webhook] = []
        self.audit_logger = get_audit_logger()
    
    def register_webhook(self, webhook: Webhook) -> str:
        """
        Register a webhook.
        
        Args:
            webhook: Webhook configuration
        
        Returns:
            Webhook ID
        """
        self.webhooks.append(webhook)
        webhook_id = f"wh_{len(self.webhooks)}"
        logger.info(f"Webhook registered: {webhook_id} -> {webhook.url}")
        return webhook_id
    
    async def trigger_webhook(self, event: WebhookEvent, data: Dict[str, Any]):
        """
        Trigger webhooks for an event.
        
        Args:
            event: Event type
            data: Event data
        """
        matching_webhooks = [
            wh for wh in self.webhooks
            if wh.enabled and event in wh.events
        ]
        
        if not matching_webhooks:
            return
        
        tasks = [
            self._deliver_webhook(webhook, event, data)
            for webhook in matching_webhooks
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _deliver_webhook(
        self,
        webhook: Webhook,
        event: WebhookEvent,
        data: Dict[str, Any]
    ):
        """Deliver webhook to a single endpoint."""
        payload = {
            "event": event.value,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "P6-Analyzer-Webhook/1.0"
        }
        
        if webhook.secret:
            # Add signature header
            import hmac
            import hashlib
            signature = hmac.new(
                webhook.secret.encode(),
                str(payload).encode(),
                hashlib.sha256
            ).hexdigest()
            headers["X-Webhook-Signature"] = signature
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(webhook.url, json=payload, headers=headers)
                response.raise_for_status()
                
                webhook.last_triggered = datetime.utcnow()
                webhook.failure_count = 0
                
                logger.info(f"Webhook delivered to {webhook.url}: {event.value}")
                
                # Audit log
                self.audit_logger.log_event(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action=f"Webhook delivered: {event.value}",
                    details={"url": webhook.url, "status": "success"}
                )
        
        except Exception as e:
            webhook.failure_count += 1
            logger.error(f"Webhook delivery failed to {webhook.url}: {str(e)}")
            
            # Audit log
            self.audit_logger.log_event(
                event_type=AuditEventType.SYSTEM_EVENT,
                action=f"Webhook delivery failed: {event.value}",
                status="failure",
                details={"url": webhook.url, "error": str(e)}
            )
    
    def get_webhooks(self) -> List[Dict[str, Any]]:
        """Get all registered webhooks."""
        return [
            {
                "url": wh.url,
                "events": [e.value for e in wh.events],
                "enabled": wh.enabled,
                "created_at": wh.created_at.isoformat(),
                "last_triggered": wh.last_triggered.isoformat() if wh.last_triggered else None,
                "failure_count": wh.failure_count
            }
            for wh in self.webhooks
        ]


# Global webhook manager
_webhook_manager: Optional[WebhookManager] = None


def get_webhook_manager() -> WebhookManager:
    """Get the global webhook manager instance."""
    global _webhook_manager
    if _webhook_manager is None:
        _webhook_manager = WebhookManager()
    return _webhook_manager

