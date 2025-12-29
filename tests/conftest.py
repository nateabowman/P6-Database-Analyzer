"""Pytest configuration and fixtures."""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from unittest.mock import Mock, MagicMock
from database.oracle_connector import OracleConnector
from database.mssql_connector import MSSQLConnector


@pytest.fixture
def mock_oracle_connector():
    """Create a mock Oracle connector."""
    connector = Mock(spec=OracleConnector)
    connector.host = "test-host"
    connector.port = 1521
    connector.service_name = "test_service"
    connector.username = "test_user"
    connector.connection = None
    connector.connection_time = None
    connector.last_health_check = None
    connector.query_count = 0
    connector.error_count = 0
    
    # Mock methods
    connector.connect = Mock(return_value=True)
    connector.disconnect = Mock()
    connector.is_connected = Mock(return_value=True)
    connector.execute_query = Mock(return_value=[])
    connector.execute_scalar = Mock(return_value=0)
    connector.get_connection_info = Mock(return_value={
        'host': 'test-host',
        'port': 1521,
        'connected': True
    })
    
    return connector


@pytest.fixture
def mock_mssql_connector():
    """Create a mock MSSQL connector."""
    connector = Mock(spec=MSSQLConnector)
    connector.server = "test-server"
    connector.database = "test_db"
    connector.username = "test_user"
    connector.connection = None
    connector.connection_time = None
    connector.last_health_check = None
    connector.query_count = 0
    connector.error_count = 0
    
    # Mock methods
    connector.connect = Mock(return_value=True)
    connector.disconnect = Mock()
    connector.is_connected = Mock(return_value=True)
    connector.execute_query = Mock(return_value=[])
    connector.execute_scalar = Mock(return_value=0)
    connector.get_connection_info = Mock(return_value={
        'server': 'test-server',
        'database': 'test_db',
        'connected': True
    })
    
    return connector


@pytest.fixture
def sample_table_data():
    """Sample table data for testing."""
    return [
        {'table_name': 'PROJECT', 'num_rows': 100, 'size_mb': 10.5},
        {'table_name': 'TASK', 'num_rows': 1000, 'size_mb': 50.2},
        {'table_name': 'RESOURCE', 'num_rows': 500, 'size_mb': 25.8}
    ]


@pytest.fixture
def sample_index_data():
    """Sample index fragmentation data for testing."""
    return [
        {
            'table_name': 'PROJECT',
            'index_name': 'PK_PROJECT',
            'fragmentation_percent': 15.5,
            'num_rows': 100
        },
        {
            'table_name': 'TASK',
            'index_name': 'PK_TASK',
            'fragmentation_percent': 45.2,
            'num_rows': 1000
        }
    ]

