"""Slack integration."""

from typing import Dict, Any, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from integrations.base import IntegrationBase
from utils.logging_config import get_logger

logger = get_logger(__name__)


class SlackIntegration(IntegrationBase):
    """Slack integration for notifications."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.webhook_url = config.get('webhook_url')
        self.channel = config.get('channel', '#general')
        self.client = None
        
        if self.webhook_url:
            # Use webhook
            pass
        elif config.get('token'):
            # Use Slack API
            self.client = WebClient(token=config['token'])
    
    def send_notification(self, message: str, details: Optional[Dict[str, Any]] = None) -> bool:
        """Send notification to Slack."""
        try:
            if self.webhook_url:
                import httpx
                payload = {
                    "text": message,
                    "channel": self.channel
                }
                if details:
                    payload["attachments"] = [{"text": str(details)}]
                
                response = httpx.post(self.webhook_url, json=payload)
                response.raise_for_status()
            elif self.client:
                self.client.chat_postMessage(
                    channel=self.channel,
                    text=message
                )
            
            logger.info(f"Slack notification sent: {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """Test Slack connection."""
        try:
            if self.client:
                self.client.auth_test()
            return True
        except Exception as e:
            logger.error(f"Slack connection test failed: {str(e)}")
            return False

