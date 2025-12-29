"""Tests for schema health scanner."""

import pytest
from analyzers.schema_health import SchemaHealthScanner
from utils.exceptions import AnalysisError


class TestSchemaHealthScanner:
    """Test cases for SchemaHealthScanner."""
    
    def test_init_oracle(self, mock_oracle_connector):
        """Test initialization with Oracle connector."""
        scanner = SchemaHealthScanner(mock_oracle_connector)
        assert scanner.db_type == 'oracle'
        assert scanner.connector == mock_oracle_connector
    
    def test_init_mssql(self, mock_mssql_connector):
        """Test initialization with MSSQL connector."""
        scanner = SchemaHealthScanner(mock_mssql_connector)
        assert scanner.db_type == 'mssql'
        assert scanner.connector == mock_mssql_connector
    
    def test_get_table_count_oracle(self, mock_oracle_connector):
        """Test getting table count for Oracle."""
        mock_oracle_connector.execute_scalar.return_value = 10
        scanner = SchemaHealthScanner(mock_oracle_connector)
        count = scanner._get_table_count()
        assert count == 10
        mock_oracle_connector.execute_scalar.assert_called_once()
    
    def test_get_table_count_mssql(self, mock_mssql_connector):
        """Test getting table count for MSSQL."""
        mock_mssql_connector.execute_scalar.return_value = 15
        scanner = SchemaHealthScanner(mock_mssql_connector)
        count = scanner._get_table_count()
        assert count == 15
        mock_mssql_connector.execute_scalar.assert_called_once()
    
    def test_get_index_count_oracle(self, mock_oracle_connector):
        """Test getting index count for Oracle."""
        mock_oracle_connector.execute_scalar.return_value = 25
        scanner = SchemaHealthScanner(mock_oracle_connector)
        count = scanner._get_index_count()
        assert count == 25
    
    def test_get_index_count_mssql(self, mock_mssql_connector):
        """Test getting index count for MSSQL."""
        mock_mssql_connector.execute_scalar.return_value = 30
        scanner = SchemaHealthScanner(mock_mssql_connector)
        count = scanner._get_index_count()
        assert count == 30
    
    def test_scan_schema_health_success(self, mock_oracle_connector):
        """Test successful schema health scan."""
        mock_oracle_connector.execute_scalar.side_effect = [10, 25, 15]  # tables, indexes, constraints
        mock_oracle_connector.execute_query.return_value = []
        
        scanner = SchemaHealthScanner(mock_oracle_connector)
        results = scanner.scan_schema_health()
        
        assert results['status'] == 'healthy'
        assert results['table_count'] == 10
        assert results['index_count'] == 25
        assert results['constraint_count'] == 15
    
    def test_scan_schema_health_with_missing_indexes(self, mock_oracle_connector):
        """Test schema health scan with missing indexes."""
        mock_oracle_connector.execute_scalar.side_effect = [10, 25, 15]
        mock_oracle_connector.execute_query.return_value = [
            {
                'constraint_name': 'FK_TEST',
                'table_name': 'TEST_TABLE',
                'r_constraint_name': 'PK_REF'
            }
        ]
        
        scanner = SchemaHealthScanner(mock_oracle_connector)
        results = scanner.scan_schema_health()
        
        assert results['status'] == 'issues_found'
        assert len(results['missing_indexes']) > 0
    
    def test_scan_schema_health_error(self, mock_oracle_connector):
        """Test schema health scan with error."""
        mock_oracle_connector.execute_scalar.side_effect = Exception("Database error")
        
        scanner = SchemaHealthScanner(mock_oracle_connector)
        
        with pytest.raises(AnalysisError):
            scanner.scan_schema_health()
    
    def test_check_missing_fk_indexes(self, mock_oracle_connector):
        """Test checking for missing foreign key indexes."""
        mock_oracle_connector.execute_query.return_value = [
            {
                'constraint_name': 'FK_TEST',
                'table_name': 'TEST_TABLE',
                'r_constraint_name': 'PK_REF'
            }
        ]
        
        scanner = SchemaHealthScanner(mock_oracle_connector)
        issues = scanner._check_missing_fk_indexes()
        
        assert len(issues) == 1
        assert issues[0]['type'] == 'missing_index'
        assert issues[0]['severity'] == 'medium'
    
    def test_check_orphaned_records(self, mock_oracle_connector):
        """Test checking for orphaned records."""
        mock_oracle_connector.execute_scalar.return_value = 1
        
        scanner = SchemaHealthScanner(mock_oracle_connector)
        issues = scanner._check_orphaned_records()
        
        # Should return empty list if no issues
        assert isinstance(issues, list)

