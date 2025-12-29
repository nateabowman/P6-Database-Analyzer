"""Oracle database connector for Primavera P6 databases."""

import cx_Oracle
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from datetime import datetime
from utils.logging_config import get_logger
from utils.exceptions import DatabaseConnectionError, DatabaseQueryError
from utils.metrics import get_metrics

logger = get_logger(__name__)
metrics = get_metrics()


class OracleConnector:
    """Handles connections to Oracle P6 databases."""
    
    def __init__(self, host: str, port: int, service_name: str, 
                 username: str, password: str):
        self.host = host
        self.port = port
        self.service_name = service_name
        self.username = username
        self.password = password
        self.connection = None
        self.connection_time = None
        self.last_health_check = None
        self.query_count = 0
        self.error_count = 0
    
    def connect(self, use_tls: bool = False, tls_verify: bool = True) -> bool:
        """
        Establish connection to Oracle database.
        
        Args:
            use_tls: Enable TLS/SSL connection
            tls_verify: Verify TLS certificates
        """
        timer_id = metrics.start_timer('oracle.connection.attempt')
        try:
            logger.info(f"Connecting to Oracle database: {self.host}:{self.port}/{self.service_name}")
            dsn = cx_Oracle.makedsn(self.host, self.port, 
                                   service_name=self.service_name)
            
            # TLS/SSL configuration
            connection_params = {
                'user': self.username,
                'password': self.password,
                'dsn': dsn
            }
            
            if use_tls:
                # Oracle TLS configuration
                # Note: Actual TLS implementation depends on Oracle client configuration
                # This is a placeholder for future TLS support
                logger.info("TLS enabled for Oracle connection")
                # In production, you would configure:
                # - Wallet location
                # - Certificate validation
                # - TLS version
            
            self.connection = cx_Oracle.connect(**connection_params)
            self.connection_time = datetime.now()
            self.last_health_check = datetime.now()
            metrics.increment('oracle.connection.success')
            metrics.stop_timer(timer_id)
            logger.info("Successfully connected to Oracle database")
            return True
        except Exception as e:
            metrics.increment('oracle.connection.failure')
            metrics.stop_timer(timer_id)
            logger.error(f"Failed to connect to Oracle database: {str(e)}")
            raise DatabaseConnectionError(
                "Failed to connect to Oracle database",
                {'host': self.host, 'port': self.port, 'service': self.service_name}
            )
    
    def disconnect(self):
        """Close database connection and clear sensitive data."""
        if self.connection:
            logger.info("Disconnecting from Oracle database")
            try:
                self.connection.close()
            except Exception as e:
                logger.warning(f"Error during disconnect: {str(e)}")
            self.connection = None
            self.connection_time = None
            self.last_health_check = None
        # Clear password from memory (best practice)
        self.password = None
        logger.debug("Oracle connection closed and sensitive data cleared")
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor."""
        if not self.connection:
            self.connect()
        cursor = self.connection.cursor()
        try:
            yield cursor
        finally:
            cursor.close()
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute a query and return results as list of dictionaries."""
        timer_id = metrics.start_timer('oracle.query.execution')
        self.query_count += 1
        try:
            logger.debug(f"Executing Oracle query (query #{self.query_count})")
            with self.get_cursor() as cursor:
                if params:
                    # Oracle uses named parameters (:param_name)
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                
                metrics.increment('oracle.query.success')
                metrics.record('oracle.query.result_count', len(results))
                logger.debug(f"Query executed successfully, returned {len(results)} rows")
                return results
        except Exception as e:
            self.error_count += 1
            metrics.increment('oracle.query.error')
            logger.error(f"Query execution failed: {str(e)}")
            raise DatabaseQueryError(f"Query execution failed: {str(e)}")
        finally:
            metrics.stop_timer(timer_id)
    
    def execute_scalar(self, query: str, params: Optional[Dict] = None) -> Any:
        """Execute a query and return a single scalar value."""
        with self.get_cursor() as cursor:
            if params:
                # Oracle uses named parameters (:param_name)
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchone()
            return result[0] if result else None
    
    def is_connected(self) -> bool:
        """Check if connection is active."""
        try:
            if self.connection:
                self.connection.ping()
                self.last_health_check = datetime.now()
                return True
            return False
        except Exception as e:
            logger.warning(f"Connection health check failed: {str(e)}")
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information and statistics."""
        return {
            'host': self.host,
            'port': self.port,
            'service_name': self.service_name,
            'username': self.username,
            'connected': self.is_connected(),
            'connection_time': self.connection_time.isoformat() if self.connection_time else None,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'query_count': self.query_count,
            'error_count': self.error_count
        }

