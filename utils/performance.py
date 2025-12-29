"""Performance profiling and optimization utilities."""

import time
import cProfile
import pstats
import io
from contextlib import contextmanager
from typing import Dict, Any, Optional
from utils.logging_config import get_logger

logger = get_logger(__name__)


class PerformanceProfiler:
    """Profiles code execution performance."""
    
    def __init__(self):
        self.profiles: Dict[str, pstats.Stats] = {}
    
    @contextmanager
    def profile(self, name: str):
        """
        Context manager for profiling code execution.
        
        Args:
            name: Name of the profile
        """
        profiler = cProfile.Profile()
        profiler.enable()
        
        try:
            yield profiler
        finally:
            profiler.disable()
            stats = pstats.Stats(profiler)
            self.profiles[name] = stats
            logger.debug(f"Profile '{name}' completed")
    
    def get_profile_summary(self, name: str, lines: int = 20) -> str:
        """
        Get profile summary as string.
        
        Args:
            name: Profile name
            lines: Number of lines to include
        
        Returns:
            Profile summary string
        """
        if name not in self.profiles:
            return f"Profile '{name}' not found"
        
        stats = self.profiles[name]
        stream = io.StringIO()
        stats.sort_stats('cumulative')
        stats.print_stats(lines, stream=stream)
        return stream.getvalue()
    
    def save_profile(self, name: str, filename: str):
        """
        Save profile to file.
        
        Args:
            name: Profile name
            filename: Output filename
        """
        if name not in self.profiles:
            logger.warning(f"Profile '{name}' not found")
            return
        
        stats = self.profiles[name]
        stats.dump_stats(filename)
        logger.info(f"Profile '{name}' saved to {filename}")


@contextmanager
def time_execution(operation_name: str):
    """
    Context manager to time code execution.
    
    Args:
        operation_name: Name of the operation
    
    Yields:
        None
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.info(f"Operation '{operation_name}' took {duration:.2f} seconds")


def measure_execution_time(func):
    """
    Decorator to measure function execution time.
    
    Args:
        func: Function to measure
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            logger.debug(f"Function '{func.__name__}' took {duration:.2f} seconds")
    return wrapper


class QueryOptimizer:
    """Utilities for query optimization."""
    
    @staticmethod
    def add_query_hints(query: str, hints: Dict[str, str], db_type: str) -> str:
        """
        Add query hints for optimization.
        
        Args:
            query: SQL query
            hints: Dictionary of hints (e.g., {'index': 'IDX_NAME'})
            db_type: Database type ('oracle' or 'mssql')
        
        Returns:
            Query with hints added
        """
        # This is a simplified implementation
        # In production, you'd have more sophisticated hint injection
        if db_type == 'oracle' and 'index' in hints:
            # Oracle hint syntax: /*+ INDEX(table_name index_name) */
            hint = f"/*+ INDEX({hints.get('table', 'table_name')} {hints['index']}) */"
            # Insert hint after SELECT
            if query.strip().upper().startswith('SELECT'):
                query = query.replace('SELECT', f'SELECT {hint}', 1)
        
        elif db_type == 'mssql' and 'index' in hints:
            # MSSQL hint syntax: WITH (INDEX(index_name))
            hint = f"WITH (INDEX({hints['index']}))"
            # Add to FROM clause
            if 'FROM' in query.upper():
                # Simplified - would need proper SQL parsing in production
                pass
        
        return query
    
    @staticmethod
    def optimize_query(query: str, db_type: str) -> str:
        """
        Apply basic query optimizations.
        
        Args:
            query: SQL query
            db_type: Database type
        
        Returns:
            Optimized query
        """
        # Remove unnecessary whitespace
        query = ' '.join(query.split())
        
        # Add basic optimizations based on database type
        if db_type == 'oracle':
            # Ensure ROWNUM is used efficiently
            pass
        elif db_type == 'mssql':
            # Ensure TOP is used efficiently
            pass
        
        return query


# Global profiler instance
_profiler: Optional[PerformanceProfiler] = None


def get_profiler() -> PerformanceProfiler:
    """Get the global performance profiler."""
    global _profiler
    if _profiler is None:
        _profiler = PerformanceProfiler()
    return _profiler

