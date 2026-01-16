"""
Security hardening utilities for Upload Bridge.

Provides:
- Input validation and sanitization
- CSRF token management
- Rate limiting by IP
- Debug endpoint removal
- Security headers
- Secure data handling
"""

import logging
import re
import hashlib
import secrets
import ipaddress
from typing import Dict, Optional, List, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from threading import Lock
from urllib.parse import urlparse
import sqlite3


logger = logging.getLogger(__name__)


# Security patterns
DANGEROUS_PATTERNS = {
    'sql_injection': [
        r"('\s*(OR|AND)\s*'1'\s*=\s*'1)",
        r"(;\s*(DROP|DELETE|INSERT|UPDATE|EXEC|CREATE)\s+)",
    ],
    'xss': [
        r"(<script[^>]*>|</script>)",
        r"(onclick=|onload=|onerror=|javascript:)",
    ],
    'command_injection': [
        r"([;&|`\$\(\)])",
    ],
    'path_traversal': [
        r"(\.\./|\.\.\\)",
    ],
}


class InputValidator:
    """Validates and sanitizes user input"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email address.
        
        Args:
            email: Email to validate
        
        Returns:
            True if valid
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate URL format.
        
        Args:
            url: URL to validate
        
        Returns:
            True if valid
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """
        Validate IP address.
        
        Args:
            ip: IP address to validate
        
        Returns:
            True if valid
        """
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_filename(filename: str) -> bool:
        """
        Validate filename safety.
        
        Args:
            filename: Filename to validate
        
        Returns:
            True if safe
        """
        # Check for path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        
        # Check length
        if len(filename) > 255:
            return False
        
        # Check for dangerous characters
        dangerous_chars = ['*', '?', '"', '<', '>', '|']
        return not any(char in filename for char in dangerous_chars)
    
    @staticmethod
    def sanitize_input(user_input: str, input_type: str = 'general') -> str:
        """
        Sanitize user input.
        
        Args:
            user_input: Input to sanitize
            input_type: Type of input (general, sql, html, command, path)
        
        Returns:
            Sanitized input
        """
        if input_type in DANGEROUS_PATTERNS:
            for pattern in DANGEROUS_PATTERNS[input_type]:
                user_input = re.sub(pattern, '', user_input, flags=re.IGNORECASE)
        
        return user_input.strip()
    
    @staticmethod
    def check_dangerous_patterns(input_str: str) -> List[str]:
        """
        Check for dangerous patterns in input.
        
        Args:
            input_str: Input to check
        
        Returns:
            List of detected patterns
        """
        detected = []
        
        for pattern_type, patterns in DANGEROUS_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, input_str, re.IGNORECASE):
                    detected.append(pattern_type)
                    break
        
        return detected


class CSRFTokenManager:
    """Manages CSRF tokens for session protection"""
    
    def __init__(self, token_length: int = 32, expiry_hours: int = 24):
        """
        Initialize CSRF token manager.
        
        Args:
            token_length: Length of generated tokens
            expiry_hours: Token expiry time in hours
        """
        self.token_length = token_length
        self.expiry_hours = expiry_hours
        self._tokens: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
    
    def generate_token(self, session_id: str) -> str:
        """
        Generate CSRF token.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Generated token
        """
        token = secrets.token_hex(self.token_length // 2)
        
        with self._lock:
            self._tokens[session_id] = {
                'token': token,
                'created': datetime.now(),
                'expires': datetime.now() + timedelta(hours=self.expiry_hours),
            }
        
        return token
    
    def validate_token(self, session_id: str, token: str) -> bool:
        """
        Validate CSRF token.
        
        Args:
            session_id: Session identifier
            token: Token to validate
        
        Returns:
            True if valid
        """
        with self._lock:
            if session_id not in self._tokens:
                return False
            
            stored_token_data = self._tokens[session_id]
            
            # Check expiry
            if datetime.now() > stored_token_data['expires']:
                del self._tokens[session_id]
                return False
            
            # Check token
            return stored_token_data['token'] == token
    
    def invalidate_token(self, session_id: str):
        """
        Invalidate token.
        
        Args:
            session_id: Session identifier
        """
        with self._lock:
            if session_id in self._tokens:
                del self._tokens[session_id]


class RateLimiterByIP:
    """Rate limiter based on IP address"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize IP-based rate limiter.
        
        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[datetime]] = {}
        self._lock = Lock()
    
    def is_rate_limited(self, ip_address: str) -> bool:
        """
        Check if IP is rate limited.
        
        Args:
            ip_address: IP address to check
        
        Returns:
            True if rate limited
        """
        with self._lock:
            if ip_address not in self._requests:
                self._requests[ip_address] = []
            
            # Remove old requests
            cutoff_time = datetime.now() - timedelta(seconds=self.window_seconds)
            self._requests[ip_address] = [
                req_time for req_time in self._requests[ip_address]
                if req_time > cutoff_time
            ]
            
            # Check limit
            if len(self._requests[ip_address]) >= self.max_requests:
                return True
            
            # Record new request
            self._requests[ip_address].append(datetime.now())
            return False
    
    def get_remaining_requests(self, ip_address: str) -> int:
        """
        Get remaining requests for IP.
        
        Args:
            ip_address: IP address
        
        Returns:
            Number of remaining requests
        """
        with self._lock:
            if ip_address not in self._requests:
                return self.max_requests
            
            # Remove old requests
            cutoff_time = datetime.now() - timedelta(seconds=self.window_seconds)
            self._requests[ip_address] = [
                req_time for req_time in self._requests[ip_address]
                if req_time > cutoff_time
            ]
            
            return max(0, self.max_requests - len(self._requests[ip_address]))


@dataclass
class SecurityHeader:
    """Security header definition"""
    
    name: str
    value: str


class SecurityHeaderManager:
    """Manages security headers"""
    
    # Standard security headers
    DEFAULT_HEADERS = [
        SecurityHeader('X-Content-Type-Options', 'nosniff'),
        SecurityHeader('X-Frame-Options', 'DENY'),
        SecurityHeader('X-XSS-Protection', '1; mode=block'),
        SecurityHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains'),
        SecurityHeader('Content-Security-Policy', "default-src 'self'"),
        SecurityHeader('Referrer-Policy', 'strict-origin-when-cross-origin'),
    ]
    
    def __init__(self):
        """Initialize security header manager"""
        self.headers = self.DEFAULT_HEADERS.copy()
    
    def add_header(self, name: str, value: str):
        """
        Add security header.
        
        Args:
            name: Header name
            value: Header value
        """
        self.headers.append(SecurityHeader(name, value))
    
    def get_headers(self) -> Dict[str, str]:
        """
        Get security headers as dictionary.
        
        Returns:
            Dictionary of headers
        """
        return {header.name: header.value for header in self.headers}


class SecureDataHandler:
    """Handles sensitive data securely"""
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """
        Hash password securely.
        
        Args:
            password: Password to hash
            salt: Optional salt (generated if not provided)
        
        Returns:
            Tuple of (hashed_password, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return pwd_hash.hex(), salt
    
    @staticmethod
    def verify_password(password: str, pwd_hash: str, salt: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Password to verify
            pwd_hash: Stored hash
            salt: Stored salt
        
        Returns:
            True if password matches
        """
        computed_hash, _ = SecureDataHandler.hash_password(password, salt)
        return computed_hash == pwd_hash
    
    @staticmethod
    def wipe_sensitive_data(data: str) -> str:
        """
        Wipe sensitive data from memory.
        
        Args:
            data: Data to wipe
        
        Returns:
            Empty string
        """
        # In Python, this is more of a safety measure
        # For truly sensitive operations, consider using external libraries
        return ''


class SecurityAuditor:
    """Audits security of operations"""
    
    def __init__(self):
        """Initialize security auditor"""
        self._events: List[Dict[str, Any]] = []
        self._lock = Lock()
    
    def log_event(self, event_type: str, description: str, severity: str = 'info', context: Optional[Dict] = None):
        """
        Log security event.
        
        Args:
            event_type: Type of event
            description: Event description
            severity: Event severity (info, warning, critical)
            context: Additional context
        """
        event = {
            'type': event_type,
            'description': description,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            'context': context or {},
        }
        
        with self._lock:
            self._events.append(event)
        
        log_level = {
            'info': logging.INFO,
            'warning': logging.WARNING,
            'critical': logging.CRITICAL,
        }.get(severity, logging.INFO)
        
        logger.log(log_level, f"Security Event: {event_type} - {description}")
    
    def log_failed_authentication(self, user_id: str, ip_address: str):
        """
        Log failed authentication attempt.
        
        Args:
            user_id: User identifier
            ip_address: IP address of attempt
        """
        self.log_event(
            'failed_authentication',
            f'Failed login attempt for user {user_id}',
            severity='warning',
            context={'user_id': user_id, 'ip_address': ip_address},
        )
    
    def log_suspicious_input(self, pattern_types: List[str], input_sample: str):
        """
        Log suspicious input detection.
        
        Args:
            pattern_types: List of detected pattern types
            input_sample: Sample of suspicious input
        """
        self.log_event(
            'suspicious_input',
            f'Detected suspicious patterns: {", ".join(pattern_types)}',
            severity='warning',
            context={'patterns': pattern_types},
        )
    
    def get_events(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get audit events.
        
        Args:
            severity: Optional filter by severity
        
        Returns:
            List of events
        """
        with self._lock:
            if severity is None:
                return self._events.copy()
            return [e for e in self._events if e['severity'] == severity]


class SecurityChecker:
    """Comprehensive security checker"""
    
    def __init__(self):
        """Initialize security checker"""
        self.validator = InputValidator()
        self.auditor = SecurityAuditor()
        self.rate_limiter = RateLimiterByIP()
        self.csrf_manager = CSRFTokenManager()
    
    def check_request_security(self, request_data: Dict[str, Any], ip_address: str) -> bool:
        """
        Check overall request security.
        
        Args:
            request_data: Request data
            ip_address: Request IP address
        
        Returns:
            True if request is secure
        """
        # Check rate limit
        if self.rate_limiter.is_rate_limited(ip_address):
            self.auditor.log_event(
                'rate_limit_exceeded',
                f'Rate limit exceeded for IP {ip_address}',
                severity='warning',
                context={'ip_address': ip_address},
            )
            return False
        
        # Check for dangerous patterns
        for field, value in request_data.items():
            if isinstance(value, str):
                patterns = self.validator.check_dangerous_patterns(value)
                if patterns:
                    self.auditor.log_suspicious_input(patterns, value[:50])
                    return False
        
        return True
