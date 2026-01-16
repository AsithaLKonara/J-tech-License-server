"""
Reusable logging configuration for Upload Bridge.

Features:
- Centralized logging setup for all modules
- Environment variable overrides
- Color output support
- File rotation with configurable size
- Log file management utilities

Usage:
    from core.logging_config import setup_logging, get_logger
    setup_logging()
    logger = get_logger(__name__)
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional


def _get_level_from_env(default: str = "INFO") -> int:
    level_name = os.getenv("UPLOADBRIDGE_LOG_LEVEL") or os.getenv("LOG_LEVEL") or default
    level_name = level_name.upper()
    return getattr(logging, level_name, logging.INFO)


class ColorFormatter(logging.Formatter):
    """Formatter that adds ANSI color to console output for better readability"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with color codes"""
        levelname = record.levelname
        if levelname in self.COLORS and sys.stdout.isatty():
            # Only use colors if terminal supports it
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
            record.name = f"\033[34m{record.name}{self.RESET}"  # Blue for logger name
        
        return super().format(record)


def setup_logging(
    app_name: str = "UploadBridge",
    level: Optional[int] = None,
    log_to_file: bool = False,
    log_dir: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    enable_colors: bool = True,
) -> logging.Logger:
    """Initialize root logging handlers once.

    Args:
        app_name: Application name for log file
        level: Log level (uses env var if not provided)
        log_to_file: Enable file logging
        log_dir: Directory for log files
        max_bytes: Max size before log rotation
        backup_count: Number of backup log files to keep
        enable_colors: Enable ANSI color output

    Returns:
        Configured root logger
    
    Environment Variables:
        UPLOADBRIDGE_LOG_LEVEL: Override log level
        UPLOADBRIDGE_LOG_FILE: Override log file path
        UPLOADBRIDGE_LOG_DIR: Override log directory
    """
    if getattr(setup_logging, "_configured", False):
        return logging.getLogger()

    log_level = level if level is not None else _get_level_from_env()

    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    # Remove any existing handlers to avoid duplicates
    root = logging.getLogger()
    root.handlers.clear()
    
    # Console handler with optional colors
    try:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        if enable_colors and sys.stdout.isatty():
            formatter = ColorFormatter(fmt=fmt, datefmt=datefmt)
        else:
            formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
        
        console_handler.setFormatter(formatter)
        root.addHandler(console_handler)
    except Exception as e:
        # Fallback to basic handler
        print(f"Warning: Failed to setup console handler: {e}", file=sys.stderr)

    # File handler with rotation
    if log_to_file:
        try:
            log_file = os.getenv("UPLOADBRIDGE_LOG_FILE")
            
            if not log_file:
                # Use log directory if specified
                if log_dir is None:
                    log_dir = os.getenv("UPLOADBRIDGE_LOG_DIR", "logs")
                
                Path(log_dir).mkdir(parents=True, exist_ok=True)
                log_file = os.path.join(log_dir, f"{app_name}.log")
            
            # Use rotating file handler for automatic log rotation
            fh = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8"
            )
            fh.setLevel(log_level)
            fh.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
            root.addHandler(fh)
        except Exception as e:
            # Fallback silently if file handler fails
            print(f"Warning: Failed to setup file handler: {e}", file=sys.stderr)

    root.setLevel(log_level)
    setup_logging._configured = True  # type: ignore[attr-defined]
    
    return root


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Module name (usually __name__)
    
    Returns:
        Logger instance configured for the module
    """
    return logging.getLogger(name)


def set_log_level(level: str) -> None:
    """
    Change log level for all handlers.
    
    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    level_value = getattr(logging, level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(level_value)
    
    for handler in root.handlers:
        handler.setLevel(level_value)


class LogFileManager:
    """Manages log file operations and cleanup"""
    
    def __init__(self, log_dir: Optional[str] = None):
        """
        Initialize log file manager.
        
        Args:
            log_dir: Directory for log files (uses UPLOADBRIDGE_LOG_DIR or 'logs')
        """
        if log_dir is None:
            log_dir = os.getenv("UPLOADBRIDGE_LOG_DIR", "logs")
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def get_log_files(self) -> list[Path]:
        """
        Get list of log files.
        
        Returns:
            List of Path objects for log files, sorted by modification time
        """
        if not self.log_dir.exists():
            return []
        
        return sorted(
            self.log_dir.glob("*.log*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
    
    def get_log_size(self) -> int:
        """
        Get total size of all log files in bytes.
        
        Returns:
            Total size in bytes
        """
        total = 0
        for log_file in self.get_log_files():
            try:
                total += log_file.stat().st_size
            except OSError:
                pass
        
        return total
    
    def cleanup_old_logs(self, max_age_days: int = 30) -> int:
        """
        Delete log files older than specified days.
        
        Args:
            max_age_days: Maximum age of logs to keep
        
        Returns:
            Number of files deleted
        """
        import time
        
        deleted = 0
        cutoff_time = time.time() - (max_age_days * 24 * 3600)
        
        for log_file in self.get_log_files():
            try:
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    deleted += 1
            except OSError:
                pass
        
        return deleted
    
    def get_recent_logs(self, lines: int = 100) -> str:
        """
        Get recent log content from the latest log file.
        
        Args:
            lines: Number of recent lines to retrieve
        
        Returns:
            Log content as string
        """
        log_files = self.get_log_files()
        if not log_files:
            return "No log files found"
        
        try:
            with open(log_files[0], 'r', encoding='utf-8', errors='replace') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                return ''.join(recent_lines)
        except OSError as e:
            return f"Error reading log file: {e}"


# Initialize on import
if not getattr(setup_logging, "_configured", False):
    # Auto-initialize with defaults (no file logging by default)
    setup_logging(log_to_file=False, enable_colors=True)


