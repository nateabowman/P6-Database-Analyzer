"""Connection pooling for database connections."""

import threading
from queue import Queue, Empty
from typing import Optional, Dict, Any
from contextlib import contextmanager
from utils.logging_config import get_logger
from utils.exceptions import DatabaseConnectionError
from database.oracle_connector import OracleConnector
from database.mssql_connector import MSSQLConnector

logger = get_logger(__name__)


class ConnectionPool:
    """Manages a pool of database connections."""
    
    def __init__(
        self,
        connector_class,
        max_connections: int = 5,
        min_connections: int = 1,
        connection_params: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize connection pool.
        
        Args:
            connector_class: Connector class (OracleConnector or MSSQLConnector)
            max_connections: Maximum number of connections in pool
            min_connections: Minimum number of connections to maintain
            connection_params: Parameters for creating connections
        """
        self.connector_class = connector_class
        self.max_connections = max_connections
        self.min_connections = min_connections
        self.connection_params = connection_params or {}
        self.pool: Queue = Queue(maxsize=max_connections)
        self.active_connections = 0
        self.lock = threading.Lock()
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize the connection pool with minimum connections."""
        for _ in range(self.min_connections):
            try:
                connector = self._create_connector()
                if connector:
                    connector.connect()
                    self.pool.put(connector)
                    with self.lock:
                        self.active_connections += 1
            except Exception as e:
                logger.warning(f"Failed to create initial connection: {str(e)}")
        
        logger.info(f"Connection pool initialized with {self.pool.qsize()} connections")
    
    def _create_connector(self):
        """Create a new connector instance."""
        try:
            return self.connector_class(**self.connection_params)
        except Exception as e:
            logger.error(f"Failed to create connector: {str(e)}")
            return None
    
    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool.
        
        Yields:
            Database connector instance
        """
        connector = None
        try:
            # Try to get from pool
            try:
                connector = self.pool.get(timeout=5)
            except Empty:
                # Create new connection if pool is empty and under max
                with self.lock:
                    if self.active_connections < self.max_connections:
                        connector = self._create_connector()
                        if connector:
                            connector.connect()
                            self.active_connections += 1
                    else:
                        # Wait for available connection
                        connector = self.pool.get(timeout=30)
            
            if not connector or not connector.is_connected():
                # Reconnect if needed
                if connector:
                    try:
                        connector.disconnect()
                    except:
                        pass
                connector = self._create_connector()
                if connector:
                    connector.connect()
            
            yield connector
        
        finally:
            # Return connection to pool
            if connector:
                try:
                    if connector.is_connected():
                        self.pool.put(connector)
                    else:
                        # Connection is bad, create new one
                        with self.lock:
                            self.active_connections -= 1
                        try:
                            connector.disconnect()
                        except:
                            pass
                except Exception as e:
                    logger.warning(f"Error returning connection to pool: {str(e)}")
                    with self.lock:
                        self.active_connections -= 1
    
    def close_all(self):
        """Close all connections in the pool."""
        logger.info("Closing all connections in pool")
        while not self.pool.empty():
            try:
                connector = self.pool.get_nowait()
                connector.disconnect()
                with self.lock:
                    self.active_connections -= 1
            except Empty:
                break
            except Exception as e:
                logger.warning(f"Error closing connection: {str(e)}")
        
        logger.info("All connections closed")


class ConnectionPoolManager:
    """Manages multiple connection pools."""
    
    def __init__(self):
        self.pools: Dict[str, ConnectionPool] = {}
        self.lock = threading.Lock()
    
    def get_pool(
        self,
        pool_key: str,
        connector_class,
        max_connections: int = 5,
        min_connections: int = 1,
        connection_params: Optional[Dict[str, Any]] = None
    ) -> ConnectionPool:
        """
        Get or create a connection pool.
        
        Args:
            pool_key: Unique key for the pool
            connector_class: Connector class
            max_connections: Maximum connections
            min_connections: Minimum connections
            connection_params: Connection parameters
        
        Returns:
            ConnectionPool instance
        """
        with self.lock:
            if pool_key not in self.pools:
                self.pools[pool_key] = ConnectionPool(
                    connector_class,
                    max_connections,
                    min_connections,
                    connection_params
                )
            return self.pools[pool_key]
    
    def close_all_pools(self):
        """Close all connection pools."""
        with self.lock:
            for pool in self.pools.values():
                pool.close_all()
            self.pools.clear()


# Global pool manager
_pool_manager: Optional[ConnectionPoolManager] = None


def get_pool_manager() -> ConnectionPoolManager:
    """Get the global connection pool manager."""
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = ConnectionPoolManager()
    return _pool_manager

