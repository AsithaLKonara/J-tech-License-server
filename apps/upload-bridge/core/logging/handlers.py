"""
Log Handlers - Custom handlers for enterprise logging.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler as BaseRotatingFileHandler
from pathlib import Path


class RotatingFileHandler(BaseRotatingFileHandler):
    """
    Rotating file handler with automatic directory creation.
    
    Extends the standard RotatingFileHandler to automatically
    create log directories if they don't exist.
    """
    
    def __init__(self, filename: str, max_bytes: int = 10 * 1024 * 1024, backup_count: int = 5):
        """
        Initialize rotating file handler.
        
        Args:
            filename: Log file path
            max_bytes: Maximum file size before rotation
            backup_count: Number of backup files to keep
        """
        # Create directory if it doesn't exist
        log_path = Path(filename)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        super().__init__(filename, maxBytes=max_bytes, backupCount=backup_count)


class ConsoleHandler(logging.StreamHandler):
    """
    Console handler with color support (optional).
    
    Provides console output with optional color coding for different log levels.
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def __init__(self, use_colors: bool = True):
        """
        Initialize console handler.
        
        Args:
            use_colors: Enable color output (if terminal supports it)
        """
        super().__init__(sys.stdout)
        self.use_colors = use_colors and sys.stdout.isatty()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with optional colors."""
        formatted = super().format(record)
        
        if self.use_colors and record.levelname in self.COLORS:
            color = self.COLORS[record.levelname]
            reset = self.COLORS['RESET']
            return f"{color}{formatted}{reset}"
        
        return formatted

