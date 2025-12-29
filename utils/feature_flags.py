"""Feature flag system for gradual rollouts."""

from typing import Dict, Optional
from utils.logging_config import get_logger

logger = get_logger(__name__)


class FeatureFlags:
    """Manages feature flags."""
    
    def __init__(self):
        self.flags: Dict[str, bool] = {
            'ai_recommendations': False,
            'ml_anomaly_detection': False,
            'advanced_analytics': True,
            'webhooks': True
        }
    
    def is_enabled(self, feature: str) -> bool:
        """Check if feature is enabled."""
        return self.flags.get(feature, False)
    
    def enable(self, feature: str):
        """Enable a feature."""
        self.flags[feature] = True
        logger.info(f"Feature enabled: {feature}")
    
    def disable(self, feature: str):
        """Disable a feature."""
        self.flags[feature] = False
        logger.info(f"Feature disabled: {feature}")


_flags: Optional[FeatureFlags] = None


def get_feature_flags() -> FeatureFlags:
    """Get feature flags instance."""
    global _flags
    if _flags is None:
        _flags = FeatureFlags()
    return _flags

