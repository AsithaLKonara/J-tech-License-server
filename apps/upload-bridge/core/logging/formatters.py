"""
Log Formatters - Structured and JSON formatters for enterprise logging.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict


class StructuredFormatter(logging.Formatter):
    """
    Structured log formatter with consistent format.
    
    Format: [TIMESTAMP] [LEVEL] [LOGGER] MESSAGE [EXTRA]
    """
    
    def __init__(self):
        """Initialize structured formatter."""
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record."""
        timestamp = datetime.fromtimestamp(record.created).isoformat()
        level = record.levelname
        logger_name = record.name
        message = record.getMessage()
        
        # Build structured message
        parts = [f"[{timestamp}]", f"[{level}]", f"[{logger_name}]", message]
        
        # Add extra fields
        extra_fields = []
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'message', 'pathname', 'process', 'processName', 'relativeCreated',
                          'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info']:
                extra_fields.append(f"{key}={value}")
        
        if extra_fields:
            parts.append(f"[{' '.join(extra_fields)}]")
        
        return " ".join(parts)


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.
    
    Outputs logs in JSON format for easy parsing by log aggregation systems.
    """
    
    def __init__(self):
        """Initialize JSON formatter."""
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'message', 'pathname', 'process', 'processName', 'relativeCreated',
                          'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info']:
                # Only include JSON-serializable values
                try:
                    json.dumps(value)
                    log_data[key] = value
                except (TypeError, ValueError):
                    log_data[key] = str(value)
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

