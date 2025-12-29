"""Tests for SQL injection prevention."""

import pytest
from utils.security import SecurityValidator


class TestSQLInjectionPrevention:
    """Test cases for SQL injection prevention."""
    
    def test_sql_injection_in_table_name(self):
        """Test that SQL injection attempts in table names are blocked."""
        malicious_inputs = [
            "'; DROP TABLE PROJECT; --",
            "1' OR '1'='1",
            "'; DELETE FROM PROJECT; --",
            "UNION SELECT * FROM",
            "'; UPDATE PROJECT SET",
            "'; INSERT INTO PROJECT VALUES",
        ]
        
        for malicious_input in malicious_inputs:
            assert SecurityValidator.validate_table_name(malicious_input) is False
            assert SecurityValidator.sanitize_table_name(malicious_input) is None
    
    def test_sql_injection_in_hostname(self):
        """Test that SQL injection attempts in hostnames are blocked."""
        malicious_inputs = [
            "'; DROP TABLE",
            "server'; DELETE FROM",
            "host' OR '1'='1",
        ]
        
        for malicious_input in malicious_inputs:
            assert SecurityValidator.validate_hostname(malicious_input) is False
    
    def test_parameterized_queries_safe(self):
        """Test that parameterized queries are used (indirect test)."""
        # This is more of a documentation test
        # In actual implementation, queries should use parameters
        valid_table = SecurityValidator.sanitize_table_name("PROJECT")
        assert valid_table == "PROJECT"
        
        # Even with valid table name, should use parameters in actual queries
        # This is verified in integration tests

