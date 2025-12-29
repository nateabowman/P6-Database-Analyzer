"""Tests for index fragmentation checker."""

import pytest
from analyzers.index_fragmentation import IndexFragmentationChecker
from utils.exceptions import AnalysisError


class TestIndexFragmentationChecker:
    """Test cases for IndexFragmentationChecker."""
    
    def test_init_oracle(self, mock_oracle_connector):
        """Test initialization with Oracle connector."""
        checker = IndexFragmentationChecker(mock_oracle_connector)
        assert checker.db_type == 'oracle'
    
    def test_init_mssql(self, mock_mssql_connector):
        """Test initialization with MSSQL connector."""
        checker = IndexFragmentationChecker(mock_mssql_connector)
        assert checker.db_type == 'mssql'
    
    def test_check_fragmentation_healthy(self, mock_oracle_connector):
        """Test fragmentation check with healthy indexes."""
        mock_oracle_connector.execute_query.return_value = []
        
        checker = IndexFragmentationChecker(mock_oracle_connector)
        results = checker.check_fragmentation(threshold=30.0)
        
        assert results['status'] == 'healthy'
        assert len(results['fragmented_indexes']) == 0
    
    def test_check_fragmentation_high(self, mock_oracle_connector):
        """Test fragmentation check with high fragmentation."""
        mock_oracle_connector.execute_query.return_value = [
            {
                'index_name': 'IDX_TEST',
                'table_name': 'TEST_TABLE',
                'num_rows': 1000,
                'fragmentation_percent': 55.5
            }
        ]
        
        checker = IndexFragmentationChecker(mock_oracle_connector)
        results = checker.check_fragmentation(threshold=30.0)
        
        assert results['status'] == 'critical'
        assert len(results['high_fragmentation']) == 1
    
    def test_check_fragmentation_medium(self, mock_oracle_connector):
        """Test fragmentation check with medium fragmentation."""
        mock_oracle_connector.execute_query.return_value = [
            {
                'index_name': 'IDX_TEST',
                'table_name': 'TEST_TABLE',
                'num_rows': 1000,
                'fragmentation_percent': 35.0
            }
        ]
        
        checker = IndexFragmentationChecker(mock_oracle_connector)
        results = checker.check_fragmentation(threshold=30.0)
        
        assert results['status'] == 'warning'
        assert len(results['medium_fragmentation']) == 1
    
    def test_check_fragmentation_error(self, mock_oracle_connector):
        """Test fragmentation check with error."""
        mock_oracle_connector.execute_query.side_effect = Exception("Database error")
        
        checker = IndexFragmentationChecker(mock_oracle_connector)
        
        with pytest.raises(AnalysisError):
            checker.check_fragmentation()

