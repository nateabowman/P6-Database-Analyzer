"""Custom exception classes for P6 Database Analyzer."""

from typing import Optional, Dict, Any


class P6AnalyzerException(Exception):
    """Base exception for all P6 Analyzer exceptions."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class DatabaseConnectionError(P6AnalyzerException):
    """Raised when database connection fails."""
    pass


class DatabaseQueryError(P6AnalyzerException):
    """Raised when a database query fails."""
    pass


class AnalysisError(P6AnalyzerException):
    """Raised when an analysis operation fails."""
    pass


class ConfigurationError(P6AnalyzerException):
    """Raised when configuration is invalid or missing."""
    pass


class SecurityError(P6AnalyzerException):
    """Raised when a security validation fails."""
    pass


class ReportGenerationError(P6AnalyzerException):
    """Raised when report generation fails."""
    pass


class ValidationError(P6AnalyzerException):
    """Raised when input validation fails."""
    pass


class CredentialError(P6AnalyzerException):
    """Raised when credential operations fail."""
    pass

