"""Caching utilities for analysis results."""

import hashlib
import json
import time
from typing import Any, Optional, Dict
from functools import wraps
from cachetools import TTLCache
from utils.logging_config import get_logger

logger = get_logger(__name__)


class AnalysisCache:
    """Cache for analysis results with TTL."""
    
    def __init__(self, max_size: int = 100, ttl: int = 3600):
        """
        Initialize analysis cache.
        
        Args:
            max_size: Maximum number of cached items
            ttl: Time-to-live in seconds
        """
        self.cache = TTLCache(maxsize=max_size, ttl=ttl)
        self.hits = 0
        self.misses = 0
    
    def _generate_key(self, analysis_type: str, params: Dict[str, Any]) -> str:
        """Generate cache key from analysis type and parameters."""
        # Create a hash of the parameters
        params_str = json.dumps(params, sort_keys=True)
        key_str = f"{analysis_type}:{params_str}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, analysis_type: str, params: Dict[str, Any]) -> Optional[Any]:
        """
        Get cached result.
        
        Args:
            analysis_type: Type of analysis
            params: Analysis parameters
        
        Returns:
            Cached result or None
        """
        key = self._generate_key(analysis_type, params)
        try:
            result = self.cache[key]
            self.hits += 1
            logger.debug(f"Cache hit for {analysis_type}")
            return result
        except KeyError:
            self.misses += 1
            logger.debug(f"Cache miss for {analysis_type}")
            return None
    
    def set(self, analysis_type: str, params: Dict[str, Any], result: Any):
        """
        Cache a result.
        
        Args:
            analysis_type: Type of analysis
            params: Analysis parameters
            result: Result to cache
        """
        key = self._generate_key(analysis_type, params)
        self.cache[key] = result
        logger.debug(f"Cached result for {analysis_type}")
    
    def clear(self):
        """Clear all cached results."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self.cache),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate
        }


# Global cache instance
_analysis_cache: Optional[AnalysisCache] = None


def get_cache() -> AnalysisCache:
    """Get the global analysis cache."""
    global _analysis_cache
    if _analysis_cache is None:
        from config.config_manager import get_config
        config = get_config()
        ttl = config.get('analysis.cache_ttl', 3600)
        _analysis_cache = AnalysisCache(ttl=ttl)
    return _analysis_cache


def cached(analysis_type: str):
    """
    Decorator to cache analysis results.
    
    Args:
        analysis_type: Type of analysis for cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Create cache key from function arguments
            # Skip 'self' if it's a method
            if args and hasattr(args[0], '__class__'):
                cache_params = {'args': str(args[1:]), 'kwargs': kwargs}
            else:
                cache_params = {'args': str(args), 'kwargs': kwargs}
            
            # Try to get from cache
            cached_result = cache.get(analysis_type, cache_params)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(analysis_type, cache_params, result)
            
            return result
        return wrapper
    return decorator

