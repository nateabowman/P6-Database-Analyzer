"""Base class for analyzer plugins."""

from abc import ABC, abstractmethod
from typing import Dict, Any
from database.oracle_connector import OracleConnector
from database.mssql_connector import MSSQLConnector
from typing import Union


class AnalyzerPlugin(ABC):
    """Base class for custom analyzer plugins."""
    
    def __init__(self, connector: Union[OracleConnector, MSSQLConnector]):
        """
        Initialize analyzer plugin.
        
        Args:
            connector: Database connector instance
        """
        self.connector = connector
        self.db_type = self._detect_db_type()
    
    def _detect_db_type(self) -> str:
        """Detect database type from connector."""
        if isinstance(self.connector, OracleConnector):
            return 'oracle'
        elif isinstance(self.connector, MSSQLConnector):
            return 'mssql'
        else:
            raise ValueError("Unknown connector type")
    
    @abstractmethod
    def analyze(self) -> Dict[str, Any]:
        """
        Perform analysis.
        
        Returns:
            Dictionary with analysis results
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Get analyzer name.
        
        Returns:
            Analyzer name
        """
        pass
    
    def get_description(self) -> str:
        """
        Get analyzer description.
        
        Returns:
            Analyzer description
        """
        return f"Custom analyzer: {self.get_name()}"

