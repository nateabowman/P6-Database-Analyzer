"""Tests for database connectors."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from database.oracle_connector import OracleConnector
from database.mssql_connector import MSSQLConnector
from utils.exceptions import DatabaseConnectionError, DatabaseQueryError


class TestOracleConnector:
    """Test cases for OracleConnector."""
    
    def test_init(self):
        """Test connector initialization."""
        connector = OracleConnector(
            host="test-host",
            port=1521,
            service_name="test_service",
            username="test_user",
            password="test_pass"
        )
        assert connector.host == "test-host"
        assert connector.port == 1521
        assert connector.service_name == "test_service"
        assert connector.username == "test_user"
        assert connector.connection is None
    
    @patch('database.oracle_connector.cx_Oracle')
    def test_connect_success(self, mock_cx_oracle):
        """Test successful connection."""
        mock_connection = MagicMock()
        mock_cx_oracle.makedsn.return_value = "test_dsn"
        mock_cx_oracle.connect.return_value = mock_connection
        
        connector = OracleConnector("host", 1521, "service", "user", "pass")
        result = connector.connect()
        
        assert result is True
        assert connector.connection == mock_connection
        mock_cx_oracle.connect.assert_called_once()
    
    @patch('database.oracle_connector.cx_Oracle')
    def test_connect_failure(self, mock_cx_oracle):
        """Test connection failure."""
        mock_cx_oracle.makedsn.return_value = "test_dsn"
        mock_cx_oracle.connect.side_effect = Exception("Connection failed")
        
        connector = OracleConnector("host", 1521, "service", "user", "pass")
        
        with pytest.raises(DatabaseConnectionError):
            connector.connect()
    
    def test_disconnect(self):
        """Test disconnection."""
        connector = OracleConnector("host", 1521, "service", "user", "pass")
        connector.connection = MagicMock()
        connector.password = "test_pass"
        
        connector.disconnect()
        
        assert connector.connection is None
        assert connector.password is None
    
    def test_is_connected_true(self):
        """Test connection check when connected."""
        connector = OracleConnector("host", 1521, "service", "user", "pass")
        mock_connection = MagicMock()
        mock_connection.ping.return_value = None
        connector.connection = mock_connection
        
        assert connector.is_connected() is True
    
    def test_is_connected_false(self):
        """Test connection check when not connected."""
        connector = OracleConnector("host", 1521, "service", "user", "pass")
        assert connector.is_connected() is False


class TestMSSQLConnector:
    """Test cases for MSSQLConnector."""
    
    def test_init(self):
        """Test connector initialization."""
        connector = MSSQLConnector(
            server="test-server",
            database="test_db",
            username="test_user",
            password="test_pass"
        )
        assert connector.server == "test-server"
        assert connector.database == "test_db"
        assert connector.username == "test_user"
        assert connector.connection is None
    
    @patch('database.mssql_connector.pyodbc')
    def test_connect_success(self, mock_pyodbc):
        """Test successful connection."""
        mock_connection = MagicMock()
        mock_pyodbc.connect.return_value = mock_connection
        
        connector = MSSQLConnector("server", "db", "user", "pass")
        result = connector.connect()
        
        assert result is True
        assert connector.connection == mock_connection
        mock_pyodbc.connect.assert_called_once()
    
    @patch('database.mssql_connector.pyodbc')
    def test_connect_failure(self, mock_pyodbc):
        """Test connection failure."""
        mock_pyodbc.connect.side_effect = Exception("Connection failed")
        
        connector = MSSQLConnector("server", "db", "user", "pass")
        
        with pytest.raises(DatabaseConnectionError):
            connector.connect()
    
    def test_disconnect(self):
        """Test disconnection."""
        connector = MSSQLConnector("server", "db", "user", "pass")
        connector.connection = MagicMock()
        connector.password = "test_pass"
        
        connector.disconnect()
        
        assert connector.connection is None
        assert connector.password is None

