"""Factory for creating database connectors."""

from database.oracle_connector import OracleConnector
from database.mssql_connector import MSSQLConnector
from typing import Union


class DatabaseFactory:
    """Factory for creating appropriate database connectors."""
    
    @staticmethod
    def create_connector(db_type: str, **kwargs) -> Union[OracleConnector, MSSQLConnector]:
        """
        Create a database connector based on type.
        
        Args:
            db_type: 'oracle' or 'mssql'
            **kwargs: Connection parameters
            
        Returns:
            Database connector instance
        """
        db_type = db_type.lower()
        
        if db_type == 'oracle':
            return OracleConnector(
                host=kwargs.get('host'),
                port=kwargs.get('port', 1521),
                service_name=kwargs.get('service_name'),
                username=kwargs.get('username'),
                password=kwargs.get('password')
            )
        elif db_type == 'mssql':
            return MSSQLConnector(
                server=kwargs.get('server'),
                database=kwargs.get('database'),
                username=kwargs.get('username'),
                password=kwargs.get('password'),
                driver=kwargs.get('driver', 'ODBC Driver 17 for SQL Server')
            )
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

