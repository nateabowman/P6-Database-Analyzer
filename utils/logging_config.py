"""Logging configuration for P6 Database Analyzer."""

import logging
import logging.handlers
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from utils.security import SecurityValidator


class SensitiveDataFilter(logging.Filter):
    """Filter to remove sensitive data from log records."""
    
    SENSITIVE_KEYWORDS = [
        'password', 'pwd', 'passwd', 'credential', 'secret', 'token',
        'api_key', 'apikey', 'connection_string', 'dsn', 'auth'
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter sensitive data from log messages."""
        # Sanitize the message
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = self._sanitize_message(record.msg)
        
        # Sanitize args
        if hasattr(record, 'args') and record.args:
            if isinstance(record.args, tuple):
                record.args = tuple(
                    self._sanitize_message(str(arg)) if isinstance(arg, str) else arg
                    for arg in record.args
                )
        
        return True
    
    def _sanitize_message(self, message: str) -> str:
        """Remove sensitive data from message."""
        msg_lower = message.lower()
        for keyword in self.SENSITIVE_KEYWORDS:
            if keyword in msg_lower:
                # Replace potential sensitive values with [REDACTED]
                import re
                pattern = re.compile(
                    rf'{keyword}\s*[:=]\s*["\']?([^"\'\s]+)["\']?',
                    re.IGNORECASE
                )
                message = pattern.sub(f'{keyword}=[REDACTED]', message)
        return message


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, default=str)


def setup_logging(
    log_level: str = 'INFO',
    log_dir: Optional[str] = None,
    log_file: Optional[str] = None,
    use_json: bool = False,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: ./logs)
        log_file: Log file name (default: p6_analyzer.log)
        use_json: Use JSON format for logs (default: False)
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup log files to keep
    
    Returns:
        Configured logger instance
    """
    # Create log directory if it doesn't exist
    if log_dir is None:
        log_dir = os.path.join(os.getcwd(), 'logs')
    
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    if log_file is None:
        log_file = 'p6_analyzer.log'
    
    log_path = os.path.join(log_dir, log_file)
    
    # Get root logger
    logger = logging.getLogger('p6_analyzer')
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create formatter
    if use_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(SensitiveDataFilter())
    logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(SensitiveDataFilter())
    logger.addHandler(file_handler)
    
    # Error file handler (separate file for errors)
    error_log_path = os.path.join(log_dir, 'p6_analyzer_errors.log')
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    error_handler.addFilter(SensitiveDataFilter())
    logger.addHandler(error_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(f'p6_analyzer.{name}')

