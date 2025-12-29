"""Failover and retry logic for database connections."""

from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import time
from utils.logging_config import get_logger
from utils.exceptions import DatabaseConnectionError

logger = get_logger(__name__)


class FailoverManager:
    """Manages failover and retry logic."""
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_multiplier: float = 2.0
    ):
        """
        Initialize failover manager.
        
        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries (seconds)
            backoff_multiplier: Multiplier for exponential backoff
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_multiplier = backoff_multiplier
    
    def execute_with_retry(
        self,
        operation: Callable,
        operation_name: str = "operation",
        *args,
        **kwargs
    ) -> Any:
        """
        Execute an operation with retry logic.
        
        Args:
            operation: Function to execute
            operation_name: Name of operation for logging
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation
        
        Returns:
            Result of operation
        
        Raises:
            Exception: If all retries fail
        """
        last_exception = None
        delay = self.retry_delay
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"Attempting {operation_name} (attempt {attempt + 1}/{self.max_retries + 1})")
                return operation(*args, **kwargs)
            except (DatabaseConnectionError, ConnectionError) as e:
                last_exception = e
                if attempt < self.max_retries:
                    logger.warning(
                        f"{operation_name} failed (attempt {attempt + 1}): {str(e)}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    time.sleep(delay)
                    delay *= self.backoff_multiplier
                else:
                    logger.error(f"{operation_name} failed after {self.max_retries + 1} attempts")
            except Exception as e:
                # Don't retry on non-connection errors
                logger.error(f"{operation_name} failed with non-retryable error: {str(e)}")
                raise
        
        # All retries exhausted
        raise last_exception
    
    def execute_with_failover(
        self,
        primary_operation: Callable,
        failover_operations: List[Callable],
        operation_name: str = "operation",
        *args,
        **kwargs
    ) -> Any:
        """
        Execute operation with failover to backup operations.
        
        Args:
            primary_operation: Primary operation to try first
            failover_operations: List of backup operations
            operation_name: Name of operation for logging
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Result from first successful operation
        
        Raises:
            Exception: If all operations fail
        """
        # Try primary first
        try:
            logger.debug(f"Attempting primary {operation_name}")
            return primary_operation(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Primary {operation_name} failed: {str(e)}. Trying failover...")
        
        # Try failover operations
        for i, failover_op in enumerate(failover_operations):
            try:
                logger.debug(f"Attempting failover {operation_name} #{i + 1}")
                return failover_op(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Failover {operation_name} #{i + 1} failed: {str(e)}")
                if i == len(failover_operations) - 1:
                    # Last failover attempt
                    raise
        
        raise Exception(f"All {operation_name} operations failed")


class ConnectionPoolFailover:
    """Failover logic for connection pools."""
    
    def __init__(self, primary_pool, backup_pools: List = None):
        """
        Initialize connection pool failover.
        
        Args:
            primary_pool: Primary connection pool
            backup_pools: List of backup connection pools
        """
        self.primary_pool = primary_pool
        self.backup_pools = backup_pools or []
        self.current_pool = primary_pool
    
    def get_connection(self):
        """Get connection with failover."""
        pools_to_try = [self.current_pool] + [
            p for p in self.backup_pools if p != self.current_pool
        ]
        
        for pool in pools_to_try:
            try:
                return pool.get_connection()
            except Exception as e:
                logger.warning(f"Failed to get connection from pool: {str(e)}")
                continue
        
        raise DatabaseConnectionError("All connection pools failed")

