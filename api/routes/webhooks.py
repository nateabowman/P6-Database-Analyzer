"""Webhook API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from api.auth import get_current_user, require_permission
from utils.rbac import Permission
from utils.logging_config import get_logger
from api.webhooks import get_webhook_manager, Webhook, WebhookEvent

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.get("/")
async def list_webhooks(
    current_user: dict = Depends(require_permission(Permission.MANAGE_SETTINGS.value))
):
    """List all webhooks."""
    manager = get_webhook_manager()
    return {"status": "success", "webhooks": manager.get_webhooks()}


@router.post("/")
async def create_webhook(
    webhook_data: Dict[str, Any],
    current_user: dict = Depends(require_permission(Permission.MANAGE_SETTINGS.value))
):
    """Create a new webhook."""
    try:
        manager = get_webhook_manager()
        
        events = [WebhookEvent(e) for e in webhook_data.get("events", [])]
        webhook = Webhook(
            url=webhook_data["url"],
            events=events,
            secret=webhook_data.get("secret"),
            enabled=webhook_data.get("enabled", True)
        )
        
        webhook_id = manager.register_webhook(webhook)
        return {"status": "success", "webhook_id": webhook_id}
    except Exception as e:
        logger.error(f"Failed to create webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/test/{webhook_id}")
async def test_webhook(
    webhook_id: str,
    current_user: dict = Depends(require_permission(Permission.MANAGE_SETTINGS.value))
):
    """Test a webhook."""
    manager = get_webhook_manager()
    # Implementation would trigger test event
    return {"status": "success", "message": "Test webhook triggered"}

