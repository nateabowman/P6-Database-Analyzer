"""Metrics collection for P6 Database Analyzer."""

import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from collections import defaultdict
from threading import Lock
from utils.logging_config import get_logger

logger = get_logger(__name__)


class MetricsCollector:
    """Collects and tracks application metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = defaultdict(list)
        self.counters: Dict[str, int] = defaultdict(int)
        self.timers: Dict[str, float] = {}
        self.lock = Lock()
        self.start_time = datetime.now()
    
    def increment(self, metric_name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """
        Increment a counter metric.
        
        Args:
            metric_name: Name of the metric
            value: Value to increment by
            tags: Optional tags for the metric
        """
        with self.lock:
            key = self._build_key(metric_name, tags)
            self.counters[key] += value
            logger.debug(f"Metric incremented: {key} = {self.counters[key]}")
    
    def record(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Record a value metric.
        
        Args:
            metric_name: Name of the metric
            value: Value to record
            tags: Optional tags for the metric
        """
        with self.lock:
            key = self._build_key(metric_name, tags)
            self.metrics[key].append({
                'value': value,
                'timestamp': datetime.now().isoformat()
            })
            logger.debug(f"Metric recorded: {key} = {value}")
    
    def start_timer(self, metric_name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """
        Start a timer and return a timer ID.
        
        Args:
            metric_name: Name of the metric
            tags: Optional tags for the metric
        
        Returns:
            Timer ID for stopping the timer
        """
        timer_id = self._build_key(metric_name, tags)
        with self.lock:
            self.timers[timer_id] = time.time()
        return timer_id
    
    def stop_timer(self, timer_id: str) -> Optional[float]:
        """
        Stop a timer and record the duration.
        
        Args:
            timer_id: Timer ID returned from start_timer
        
        Returns:
            Duration in seconds, or None if timer not found
        """
        with self.lock:
            if timer_id not in self.timers:
                logger.warning(f"Timer {timer_id} not found")
                return None
            
            start_time = self.timers.pop(timer_id)
            duration = time.time() - start_time
            
            # Record the duration
            self.metrics[timer_id].append({
                'value': duration,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.debug(f"Timer stopped: {timer_id} = {duration:.2f}s")
            return duration
    
    def get_counter(self, metric_name: str, tags: Optional[Dict[str, str]] = None) -> int:
        """Get current counter value."""
        key = self._build_key(metric_name, tags)
        return self.counters.get(key, 0)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get summary of all metrics.
        
        Returns:
            Dictionary with metrics summary
        """
        with self.lock:
            summary = {
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
                'counters': dict(self.counters),
                'metrics': {
                    key: {
                        'count': len(values),
                        'min': min(v['value'] for v in values) if values else None,
                        'max': max(v['value'] for v in values) if values else None,
                        'avg': sum(v['value'] for v in values) / len(values) if values else None,
                        'latest': values[-1]['value'] if values else None
                    }
                    for key, values in self.metrics.items()
                }
            }
            return summary
    
    def reset(self):
        """Reset all metrics."""
        with self.lock:
            self.metrics.clear()
            self.counters.clear()
            self.timers.clear()
            self.start_time = datetime.now()
            logger.info("Metrics reset")
    
    def _build_key(self, metric_name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """Build a key for metric storage."""
        if tags:
            tag_str = ','.join(f"{k}={v}" for k, v in sorted(tags.items()))
            return f"{metric_name}[{tag_str}]"
        return metric_name


# Global metrics collector instance
_metrics_collector = MetricsCollector()


def get_metrics() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return _metrics_collector


def track_operation(operation_name: str, tags: Optional[Dict[str, str]] = None):
    """
    Decorator to track operation metrics.
    
    Args:
        operation_name: Name of the operation
        tags: Optional tags for the metric
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            timer_id = _metrics_collector.start_timer(operation_name, tags)
            _metrics_collector.increment(f"{operation_name}.started", tags=tags)
            
            try:
                result = func(*args, **kwargs)
                _metrics_collector.increment(f"{operation_name}.success", tags=tags)
                return result
            except Exception as e:
                _metrics_collector.increment(f"{operation_name}.error", tags=tags)
                logger.error(f"Operation {operation_name} failed: {str(e)}")
                raise
            finally:
                _metrics_collector.stop_timer(timer_id)
        
        return wrapper
    return decorator

