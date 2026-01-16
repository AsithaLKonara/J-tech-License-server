"""
Enterprise Logger - Structured logging with levels and rotation.

Provides enterprise-grade logging capabilities.
"""

import logging
import sys
from enum import Enum
from pathlib import Path
from typing import Optional
from datetime import datetime

from core.logging.formatters import StructuredFormatter, JSONFormatter
from core.logging.handlers import RotatingFileHandler, ConsoleHandler


class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class EnterpriseLogger:
    """
    Enterprise-grade logger with structured logging support.
    
    Features:
    - Multiple log levels
    - Structured logging (JSON)
    - Log rotation
    - Console and file handlers
    - Performance metrics
    - Audit trail
    """
    
    _instance: Optional['EnterpriseLogger'] = None
    _configured: bool = False
    
    def __init__(self):
        """Initialize the enterprise logger."""
        if EnterpriseLogger._instance is not None:
            raise RuntimeError("EnterpriseLogger is a singleton. Use get_logger() instead.")
        
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.loggers: dict[str, logging.Logger] = {}
        EnterpriseLogger._instance = self
    
    @classmethod
    def instance(cls) -> 'EnterpriseLogger':
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def setup(
        self,
        level: LogLevel = LogLevel.INFO,
        log_to_file: bool = True,
        log_to_console: bool = True,
        json_format: bool = False,
        log_dir: Optional[Path] = None,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ) -> None:
        """
        Setup logging configuration.
        
        Args:
            level: Log level
            log_to_file: Enable file logging
            log_to_console: Enable console logging
            json_format: Use JSON format for structured logging
            log_dir: Log directory (default: logs/)
            max_bytes: Max file size before rotation
            backup_count: Number of backup files to keep
        """
        if log_dir:
            self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(level.value)
        root_logger.handlers.clear()
        
        # Formatter
        if json_format:
            formatter = JSONFormatter()
        else:
            formatter = StructuredFormatter()
        
        # Console handler
        if log_to_console:
            console_handler = ConsoleHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(level.value)
            root_logger.addHandler(console_handler)
        
        # File handler with rotation
        if log_to_file:
            log_file = self.log_dir / "application.log"
            file_handler = RotatingFileHandler(
                str(log_file),
                max_bytes=max_bytes,
                backup_count=backup_count
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level.value)
            root_logger.addHandler(file_handler)
        
        # Error log file (errors only)
        error_log_file = self.log_dir / "errors.log"
        error_handler = RotatingFileHandler(
            str(error_log_file),
            max_bytes=max_bytes,
            backup_count=backup_count
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)
        
        # Audit log file (audit trail)
        audit_log_file = self.log_dir / "audit.log"
        audit_handler = RotatingFileHandler(
            str(audit_log_file),
            max_bytes=max_bytes,
            backup_count=backup_count
        )
        audit_handler.setFormatter(formatter)
        audit_handler.setLevel(logging.INFO)
        # Filter for audit events only
        audit_handler.addFilter(lambda record: hasattr(record, 'audit') and record.audit)
        root_logger.addHandler(audit_handler)
        
        EnterpriseLogger._configured = True
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger instance.
        
        Args:
            name: Logger name (typically module name)
        
        Returns:
            Logger instance
        """
        if name not in self.loggers:
            logger = logging.getLogger(name)
            self.loggers[name] = logger
        return self.loggers[name]
    
    def log_audit(self, action: str, user: Optional[str] = None, details: Optional[dict] = None) -> None:
        """
        Log an audit event.
        
        Args:
            action: Action performed
            user: User who performed the action
            details: Additional details
        """
        logger = self.get_logger("audit")
        extra = {
            'audit': True,
            'action': action,
            'user': user,
            'timestamp': datetime.now().isoformat(),
            **(details or {})
        }
        logger.info(f"Audit: {action}", extra=extra)
    
    def log_performance(self, operation: str, duration_ms: float, details: Optional[dict] = None) -> None:
        """
        Log a performance metric.
        
        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            details: Additional details
        """
        logger = self.get_logger("performance")
        extra = {
            'performance': True,
            'operation': operation,
            'duration_ms': duration_ms,
            'timestamp': datetime.now().isoformat(),
            **(details or {})
        }
        logger.info(f"Performance: {operation} took {duration_ms:.2f}ms", extra=extra)


def setup_logging(
    level: LogLevel = LogLevel.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True,
    json_format: bool = False,
    log_dir: Optional[Path] = None
) -> None:
    """
    Setup enterprise logging.
    
    Args:
        level: Log level
        log_to_file: Enable file logging
        log_to_console: Enable console logging
        json_format: Use JSON format
        log_dir: Log directory
    """
    logger = EnterpriseLogger.instance()
    logger.setup(
        level=level,
        log_to_file=log_to_file,
        log_to_console=log_to_console,
        json_format=json_format,
        log_dir=log_dir
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    if not EnterpriseLogger._configured:
        # Auto-setup with defaults
        setup_logging()
    
    logger = EnterpriseLogger.instance()
    return logger.get_logger(name)

