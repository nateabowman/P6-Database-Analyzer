"""Redis-based distributed caching."""

import json
from typing import Any, Optional
from datetime import timedelta
import redis
from utils.logging_config import get_logger

logger = get_logger(__name__)


class RedisCache:
    """Redis-based distributed cache."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        decode_responses: bool = True
    ):
        """
        Initialize Redis cache.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            decode_responses: Whether to decode responses
        """
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=decode_responses
            )
            # Test connection
            self.client.ping()
            logger.info(f"Connected to Redis at {host}:{port}")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {str(e)}. Cache will be disabled.")
            self.client = None
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None
        """
        if not self.client:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Cache get failed for key {key}: {str(e)}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        if not self.client:
            return
        
        try:
            serialized = json.dumps(value, default=str)
            if ttl:
                self.client.setex(key, ttl, serialized)
            else:
                self.client.set(key, serialized)
        except Exception as e:
            logger.warning(f"Cache set failed for key {key}: {str(e)}")
    
    def delete(self, key: str):
        """Delete key from cache."""
        if not self.client:
            return
        
        try:
            self.client.delete(key)
        except Exception as e:
            logger.warning(f"Cache delete failed for key {key}: {str(e)}")
    
    def clear(self, pattern: str = "*"):
        """Clear cache entries matching pattern."""
        if not self.client:
            return
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries")
        except Exception as e:
            logger.warning(f"Cache clear failed: {str(e)}")
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.client:
            return False
        
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.warning(f"Cache exists check failed for key {key}: {str(e)}")
            return False


# Global Redis cache instance
_redis_cache: Optional[RedisCache] = None


def get_redis_cache() -> Optional[RedisCache]:
    """Get the global Redis cache instance."""
    global _redis_cache
    if _redis_cache is None:
        from config.config_manager import get_config
        config = get_config()
        # Would get Redis config from config
        _redis_cache = RedisCache()
    return _redis_cache

