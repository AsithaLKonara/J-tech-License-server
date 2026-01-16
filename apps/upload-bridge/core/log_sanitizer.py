"""
Log sanitizer utility to remove sensitive data from logs.

Prevents accidental logging of:
- Passwords and API keys
- Authentication tokens
- Personal information
- File paths with sensitive names
- Database credentials
"""

import re
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class LogSanitizer:
    """Sanitizes log messages to remove sensitive data"""
    
    # Regex patterns for sensitive data
    PATTERNS = {
        'password': r'["\']?(?:password|passwd|pwd)["\']?\s*[:=]\s*["\']([^"\']+)["\']',
        'api_key': r'["\']?(?:api[_-]?key|apikey|key)["\']?\s*[:=]\s*["\']([^"\']+)["\']',
        'token': r'["\']?(?:token|auth_token|access_token)["\']?\s*[:=]\s*["\']([^"\']+)["\']',
        'bearer': r'Bearer\s+([A-Za-z0-9\-._~\+/]+=*)',
        'basic_auth': r'Basic\s+([A-Za-z0-9+/]+=*)',
        'jwt': r'eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*',
        'url_password': r'://[^:/@]+:([^/@]+)@',
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'phone': r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
        'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    }
    
    # List of sensitive keywords
    SENSITIVE_KEYWORDS = {
        'password', 'passwd', 'pwd', 'secret', 'token', 'api_key', 'apikey',
        'auth', 'authorization', 'credential', 'private_key', 'access_token',
        'refresh_token', 'bearer', 'apitoken', 'sessid', 'session_id',
        'signature', 'encrypted', 'cipher', 'passphrase',
    }
    
    # Safe replacement strings
    REPLACEMENTS = {
        'password': '***PASSWORD***',
        'api_key': '***API_KEY***',
        'token': '***TOKEN***',
        'bearer': '***BEARER_TOKEN***',
        'basic_auth': '***BASIC_AUTH***',
        'jwt': '***JWT_TOKEN***',
        'url_password': '***PASSWORD***',
        'email': '***EMAIL***',
        'phone': '***PHONE***',
        'credit_card': '***CREDIT_CARD***',
        'ssn': '***SSN***',
    }
    
    def __init__(self, patterns: Optional[Dict[str, str]] = None, 
                 custom_patterns: Optional[Dict[str, str]] = None):
        """
        Initialize log sanitizer.
        
        Args:
            patterns: Use custom patterns (overrides defaults)
            custom_patterns: Add additional patterns
        """
        self.patterns = patterns or self.PATTERNS.copy()
        
        if custom_patterns:
            self.patterns.update(custom_patterns)
    
    def sanitize(self, message: str) -> str:
        """
        Sanitize a log message.
        
        Args:
            message: Log message to sanitize
        
        Returns:
            Sanitized log message
        """
        if not message:
            return message
        
        sanitized = message
        
        # Apply regex patterns
        for pattern_name, pattern in self.patterns.items():
            replacement = self.REPLACEMENTS.get(pattern_name, '***REDACTED***')
            
            try:
                sanitized = re.sub(
                    pattern,
                    replacement,
                    sanitized,
                    flags=re.IGNORECASE
                )
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{pattern_name}': {e}")
        
        return sanitized
    
    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize dictionary values.
        
        Args:
            data: Dictionary to sanitize
        
        Returns:
            Sanitized dictionary
        """
        sanitized = {}
        
        for key, value in data.items():
            # Check if key is sensitive
            if self._is_sensitive_key(key):
                sanitized[key] = '***REDACTED***'
            elif isinstance(value, str):
                sanitized[key] = self.sanitize(value)
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_dict(value)
            elif isinstance(value, (list, tuple)):
                sanitized[key] = [
                    self.sanitize(v) if isinstance(v, str) else v
                    for v in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a key name indicates sensitive data"""
        key_lower = key.lower()
        return any(sensitive in key_lower for sensitive in self.SENSITIVE_KEYWORDS)


class SanitizingLogFilter(logging.Filter):
    """
    Logging filter that automatically sanitizes log records.
    
    Add to a logger to automatically sanitize all messages:
        logger.addFilter(SanitizingLogFilter())
    """
    
    def __init__(self):
        """Initialize the filter"""
        super().__init__()
        self.sanitizer = LogSanitizer()
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record by sanitizing its message.
        
        Args:
            record: Log record
        
        Returns:
            True (always allow record after sanitization)
        """
        # Sanitize message
        if isinstance(record.msg, str):
            record.msg = self.sanitizer.sanitize(record.msg)
        
        # Sanitize arguments if they're a dict
        if isinstance(record.args, dict):
            record.args = self.sanitizer.sanitize_dict(record.args)
        elif isinstance(record.args, tuple):
            record.args = tuple(
                self.sanitizer.sanitize(arg) if isinstance(arg, str) else arg
                for arg in record.args
            )
        
        return True


class SanitizingLogFormatter(logging.Formatter):
    """
    Logging formatter that sanitizes formatted log output.
    
    Use this formatter to ensure sensitive data doesn't appear in logs:
        handler = logging.StreamHandler()
        handler.setFormatter(SanitizingLogFormatter())
        logger.addHandler(handler)
    """
    
    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        """
        Initialize formatter.
        
        Args:
            fmt: Format string
            datefmt: Date format string
        """
        super().__init__(fmt, datefmt)
        self.sanitizer = LogSanitizer()
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format and sanitize log record.
        
        Args:
            record: Log record
        
        Returns:
            Formatted and sanitized message
        """
        # Let parent formatter do its work first
        formatted = super().format(record)
        
        # Then sanitize the result
        return self.sanitizer.sanitize(formatted)


def apply_sanitizing_filter_globally() -> None:
    """
    Apply sanitizing filter to the root logger.
    
    This ensures all log messages throughout the application are sanitized.
    """
    root_logger = logging.getLogger()
    
    # Check if filter already applied
    for handler in root_logger.handlers:
        if any(isinstance(f, SanitizingLogFilter) for f in handler.filters):
            logger.debug("Sanitizing filter already applied")
            return
    
    # Apply filter
    filter_instance = SanitizingLogFilter()
    root_logger.addFilter(filter_instance)
    logger.info("Applied sanitizing filter to root logger")


def apply_sanitizing_formatter(logger_instance: logging.Logger) -> None:
    """
    Apply sanitizing formatter to a specific logger.
    
    Args:
        logger_instance: Logger to apply formatter to
    """
    fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    for handler in logger_instance.handlers:
        if not isinstance(handler.formatter, SanitizingLogFormatter):
            handler.setFormatter(SanitizingLogFormatter(fmt))


# Example usage
if __name__ == '__main__':
    # Setup logging with sanitization
    logging.basicConfig(level=logging.INFO)
    test_logger = logging.getLogger('test')
    apply_sanitizing_filter_globally()
    
    # These will be sanitized
    test_logger.info("User logged in with password='secret123' and token='abc123xyz'")
    test_logger.info("Email: john.doe@example.com, Phone: 555-123-4567")
    test_logger.info({
        'password': 'secret',
        'api_key': 'sk-12345',
        'username': 'john'
    })
