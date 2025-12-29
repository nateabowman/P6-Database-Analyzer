"""Tests for SecurityValidator."""

import pytest
from utils.security import SecurityValidator


class TestSecurityValidator:
    """Test cases for SecurityValidator."""
    
    def test_validate_table_name_valid(self):
        """Test validation of valid table names."""
        assert SecurityValidator.validate_table_name("PROJECT") is True
        assert SecurityValidator.validate_table_name("TASK") is True
        assert SecurityValidator.validate_table_name("valid_table_name") is True
    
    def test_validate_table_name_invalid(self):
        """Test validation of invalid table names."""
        assert SecurityValidator.validate_table_name("") is False
        assert SecurityValidator.validate_table_name("DROP TABLE") is False
        assert SecurityValidator.validate_table_name("'; DROP TABLE--") is False
    
    def test_sanitize_table_name(self):
        """Test table name sanitization."""
        assert SecurityValidator.sanitize_table_name("PROJECT") == "PROJECT"
        assert SecurityValidator.sanitize_table_name("project") == "PROJECT"
        assert SecurityValidator.sanitize_table_name("  TASK  ") == "TASK"
        assert SecurityValidator.sanitize_table_name("invalid; DROP") is None
    
    def test_validate_port(self):
        """Test port validation."""
        assert SecurityValidator.validate_port("1521") is True
        assert SecurityValidator.validate_port("1433") is True
        assert SecurityValidator.validate_port("65535") is True
        assert SecurityValidator.validate_port("1") is True
        assert SecurityValidator.validate_port("0") is False
        assert SecurityValidator.validate_port("65536") is False
        assert SecurityValidator.validate_port("invalid") is False
        assert SecurityValidator.validate_port("-1") is False
    
    def test_validate_hostname(self):
        """Test hostname validation."""
        assert SecurityValidator.validate_hostname("localhost") is True
        assert SecurityValidator.validate_hostname("server.example.com") is True
        assert SecurityValidator.validate_hostname("192.168.1.1") is True
        assert SecurityValidator.validate_hostname("") is False
        assert SecurityValidator.validate_hostname("a" * 256) is False  # Too long
        assert SecurityValidator.validate_hostname("server; DROP") is False
    
    def test_sanitize_for_html(self):
        """Test HTML sanitization."""
        assert SecurityValidator.sanitize_for_html("<script>alert('xss')</script>") == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
        assert SecurityValidator.sanitize_for_html("Hello & World") == "Hello &amp; World"
        assert SecurityValidator.sanitize_for_html('"quoted"') == "&quot;quoted&quot;"
        assert SecurityValidator.sanitize_for_html("") == ""
        assert SecurityValidator.sanitize_for_html(None) == ""
    
    def test_validate_file_path(self):
        """Test file path validation."""
        assert SecurityValidator.validate_file_path("report.html", ['.html']) is True
        assert SecurityValidator.validate_file_path("report.pdf", ['.pdf']) is True
        assert SecurityValidator.validate_file_path("../etc/passwd", ['.html']) is False
        assert SecurityValidator.validate_file_path("report.txt", ['.html', '.pdf']) is False
        assert SecurityValidator.validate_file_path("", ['.html']) is False
    
    def test_sanitize_log_data(self):
        """Test log data sanitization."""
        data = {
            'username': 'test',
            'password': 'secret123',
            'host': 'localhost'
        }
        sanitized = SecurityValidator.sanitize_log_data(data)
        assert sanitized['password'] == '[REDACTED]'
        assert sanitized['username'] == 'test'
        assert sanitized['host'] == 'localhost'
        
        # Test with list
        data_list = [
            {'key': 'value', 'password': 'secret'},
            {'key2': 'value2'}
        ]
        sanitized_list = SecurityValidator.sanitize_log_data(data_list)
        assert sanitized_list[0]['password'] == '[REDACTED]'
        assert sanitized_list[1]['key2'] == 'value2'

