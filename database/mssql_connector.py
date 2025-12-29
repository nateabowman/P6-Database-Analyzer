"""MSSQL database connector for Primavera P6 databases."""

import pyodbc
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from datetime import datetime
from utils.logging_config import get_logger
from utils.exceptions import DatabaseConnectionError, DatabaseQueryError
from utils.metrics import get_metrics

logger = get_logger(__name__)
metrics = get_metrics()


class MSSQLConnector:
    """Handles connections to Microsoft SQL Server P6 databases."""
    
    def __init__(self, server: str, database: str, username: str, 
                 password: str, driver: str = "ODBC Driver 17 for SQL Server"):
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.driver = driver
        self.connection = None
        self.connection_time = None
        self.last_health_check = None
        self.query_count = 0
        self.error_count = 0
    
    def connect(self, use_tls: bool = False, tls_verify: bool = True) -> bool:
        """
        Establish connection to MSSQL database.
        
        Args:
            use_tls: Enable TLS/SSL connection
            tls_verify: Verify TLS certificates
        """
        timer_id = metrics.start_timer('mssql.connection.attempt')
        try:
            logger.info(f"Connecting to MSSQL database: {self.server}/{self.database}")
            # Build connection string - pyodbc handles escaping of special characters
            # in connection string values, but we construct it carefully
            connection_string = (
                f"DRIVER={{{self.driver}}};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password};"
            )
            
            # TLS/SSL configuration
            if use_tls:
                if tls_verify:
                    connection_string += "Encrypt=yes;TrustServerCertificate=no;"
                else:
                    connection_string += "Encrypt=yes;TrustServerCertificate=yes;"
                logger.info("TLS enabled for MSSQL connection")
            else:
                connection_string += "TrustServerCertificate=yes;"
            
            self.connection = pyodbc.connect(connection_string)
            self.connection_time = datetime.now()
            self.last_health_check = datetime.now()
            metrics.increment('mssql.connection.success')
            metrics.stop_timer(timer_id)
            logger.info("Successfully connected to MSSQL database")
            return True
        except Exception as e:
            metrics.increment('mssql.connection.failure')
            metrics.stop_timer(timer_id)
            logger.error(f"Failed to connect to MSSQL database: {str(e)}")
            # Don't expose connection details in error message
            raise DatabaseConnectionError(
                "Failed to connect to MSSQL database",
                {'server': self.server, 'database': self.database}
            )
    
    def disconnect(self):
        """Close database connection and clear sensitive data."""
        if self.connection:
            logger.info("Disconnecting from MSSQL database")
            try:
                self.connection.close()
            except Exception as e:
                logger.warning(f"Error during disconnect: {str(e)}")
            self.connection = None
            self.connection_time = None
            self.last_health_check = None
        # Clear password from memory (best practice)
        self.password = None
        logger.debug("MSSQL connection closed and sensitive data cleared")
    
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
        timer_id = metrics.start_timer('mssql.query.execution')
        self.query_count += 1
        try:
            logger.debug(f"Executing MSSQL query (query #{self.query_count})")
            with self.get_cursor() as cursor:
                if params:
                    # Convert dict params to tuple for pyodbc
                    param_values = tuple(params.values())
                    cursor.execute(query, param_values)
                else:
                    cursor.execute(query)
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                for row in cursor.fetchall():
                    row_dict = {}
                    for i, col in enumerate(columns):
                        value = row[i]
                        # Convert bytes to string if needed
                        if isinstance(value, bytes):
                            value = value.decode('utf-8', errors='ignore')
                        row_dict[col] = value
                    results.append(row_dict)
                
                metrics.increment('mssql.query.success')
                metrics.record('mssql.query.result_count', len(results))
                logger.debug(f"Query executed successfully, returned {len(results)} rows")
                return results
        except Exception as e:
            self.error_count += 1
            metrics.increment('mssql.query.error')
            logger.error(f"Query execution failed: {str(e)}")
            raise DatabaseQueryError(f"Query execution failed: {str(e)}")
        finally:
            metrics.stop_timer(timer_id)
    
    def execute_scalar(self, query: str, params: Optional[Dict] = None) -> Any:
        """Execute a query and return a single scalar value."""
        with self.get_cursor() as cursor:
            if params:
                param_values = tuple(params.values())
                cursor.execute(query, param_values)
            else:
                cursor.execute(query)
            result = cursor.fetchone()
            return result[0] if result else None
    
    def is_connected(self) -> bool:
        """Check if connection is active."""
        try:
            if self.connection:
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                self.last_health_check = datetime.now()
                return True
            return False
        except Exception as e:
            logger.warning(f"Connection health check failed: {str(e)}")
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information and statistics."""
        return {
            'server': self.server,
            'database': self.database,
            'username': self.username,
            'driver': self.driver,
            'connected': self.is_connected(),
            'connection_time': self.connection_time.isoformat() if self.connection_time else None,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'query_count': self.query_count,
            'error_count': self.error_count
        }

