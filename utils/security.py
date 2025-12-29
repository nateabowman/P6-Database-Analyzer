"""Security utilities for input validation and sanitization."""

import re
from typing import Optional, Any, Dict


class SecurityValidator:
    """Validates and sanitizes inputs to prevent security vulnerabilities."""
    
    # Whitelist of allowed table names (P6 core tables)
    ALLOWED_TABLE_NAMES = {
        'PROJECT', 'TASK', 'RESOURCE', 'ASSIGNMENT', 'WBS',
        'PROJWBS', 'TASKPRED', 'TASKRSRC', 'TASKACTV', 'TASKNOTE',
        'PROJECT', 'PROJECT', 'CALENDAR', 'SHIFT', 'RSRC', 'RSRCRATE',
        'RSRCCURV', 'RSRCRCAT', 'RSRCRCATVAL', 'RSRCROLE', 'RSRCRATE'
    }
    
    # Valid identifier pattern (alphanumeric and underscore, max 128 chars)
    IDENTIFIER_PATTERN = re.compile(r'^[A-Za-z_][A-Za-z0-9_]{0,127}$')
    
    @staticmethod
    def validate_table_name(table_name: str) -> bool:
        """
        Validate table name to prevent SQL injection.
        
        Args:
            table_name: Table name to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not table_name:
            return False
        
        # Check against whitelist
        if table_name.upper() in SecurityValidator.ALLOWED_TABLE_NAMES:
            return True
        
        # Check identifier pattern
        if SecurityValidator.IDENTIFIER_PATTERN.match(table_name):
            return True
        
        return False
    
    @staticmethod
    def sanitize_table_name(table_name: str) -> Optional[str]:
        """
        Sanitize table name by validating and returning safe version.
        
        Args:
            table_name: Table name to sanitize
            
        Returns:
            Sanitized table name or None if invalid
        """
        if not table_name:
            return None
        
        # Remove any whitespace
        table_name = table_name.strip()
        
        # Validate
        if SecurityValidator.validate_table_name(table_name):
            return table_name.upper()
        
        return None
    
    @staticmethod
    def validate_port(port: str) -> bool:
        """
        Validate port number.
        
        Args:
            port: Port number as string
            
        Returns:
            True if valid (1-65535), False otherwise
        """
        try:
            port_num = int(port)
            return 1 <= port_num <= 65535
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_hostname(hostname: str) -> bool:
        """
        Validate hostname or server name.
        
        Args:
            hostname: Hostname to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not hostname or len(hostname) > 255:
            return False
        
        # Basic validation - alphanumeric, dots, hyphens, underscores
        pattern = re.compile(r'^[A-Za-z0-9._-]+$')
        return bool(pattern.match(hostname))
    
    @staticmethod
    def sanitize_for_html(text: str) -> str:
        """
        Escape HTML special characters to prevent XSS.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text
        """
        if not text:
            return ""
        
        # HTML escape mapping
        html_escape_map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '/': '&#x2F;'
        }
        
        result = str(text)
        for char, escaped in html_escape_map.items():
            result = result.replace(char, escaped)
        
        return result
    
    @staticmethod
    def validate_file_path(file_path: str, allowed_extensions: Optional[list] = None) -> bool:
        """
        Validate file path to prevent directory traversal.
        
        Args:
            file_path: File path to validate
            allowed_extensions: List of allowed file extensions (e.g., ['.html', '.pdf'])
            
        Returns:
            True if valid, False otherwise
        """
        if not file_path:
            return False
        
        # Check for directory traversal attempts
        if '..' in file_path or file_path.startswith('/') or '\\' in file_path:
            # On Windows, allow single backslash but not double
            if file_path.count('\\') > file_path.count('\\\\'):
                return False
        
        # Check extension if specified
        if allowed_extensions:
            file_path_lower = file_path.lower()
            if not any(file_path_lower.endswith(ext.lower()) for ext in allowed_extensions):
                return False
        
        return True
    
    @staticmethod
    def sanitize_log_data(data: Any) -> Any:
        """
        Sanitize data for logging to prevent sensitive information leakage.
        
        Args:
            data: Data to sanitize (can be dict, list, str, etc.)
            
        Returns:
            Sanitized data with sensitive information removed
        """
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                key_lower = str(key).lower()
                # Check if key contains sensitive keywords
                if any(keyword in key_lower for keyword in [
                    'password', 'pwd', 'passwd', 'credential', 'secret',
                    'token', 'api_key', 'apikey', 'connection_string', 'dsn'
                ]):
                    sanitized[key] = '[REDACTED]'
                else:
                    sanitized[key] = SecurityValidator.sanitize_log_data(value)
            return sanitized
        elif isinstance(data, list):
            return [SecurityValidator.sanitize_log_data(item) for item in data]
        elif isinstance(data, str):
            # Check for potential sensitive patterns
            if any(keyword in data.lower() for keyword in [
                'password=', 'pwd=', 'passwd=', 'credential=',
                'secret=', 'token=', 'api_key=', 'apikey='
            ]):
                return '[REDACTED]'
            return data
        else:
            return data

