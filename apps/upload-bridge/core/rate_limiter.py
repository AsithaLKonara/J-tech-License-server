"""
Rate Limiter for WiFi Upload
Prevents abuse and resource exhaustion
"""

import logging
from datetime import datetime, timedelta
from typing import Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    max_uploads_per_hour: int = 10
    max_file_size_mb: int = 10
    max_concurrent_uploads: int = 3
    upload_timeout_minutes: int = 30
    cooldown_seconds: int = 30


class UploadRateLimiter:
    """
    Rate limiter for WiFi uploads to prevent abuse and resource exhaustion.
    
    Features:
    - Tracks uploads per hour
    - Enforces maximum file size
    - Manages concurrent uploads
    - Configurable cooldown periods
    """
    
    def __init__(self, config: RateLimitConfig = None):
        """
        Initialize rate limiter.
        
        Args:
            config: RateLimitConfig instance with limits
        """
        self.config = config or RateLimitConfig()
        self.upload_times = []
        self.concurrent_uploads = 0
        self.last_failed_upload_time = None
        
        logger.info(
            f"Rate limiter initialized: {self.config.max_uploads_per_hour}/hour, "
            f"max file: {self.config.max_file_size_mb}MB, "
            f"max concurrent: {self.config.max_concurrent_uploads}"
        )
    
    def check_file_size(self, file_size_bytes: int) -> Tuple[bool, str]:
        """
        Check if file size is within limits.
        
        Args:
            file_size_bytes: File size in bytes
        
        Returns:
            (allowed: bool, error_message: str)
        """
        max_bytes = self.config.max_file_size_mb * 1024 * 1024
        
        if file_size_bytes > max_bytes:
            error = (
                f"File size {file_size_bytes / (1024*1024):.1f}MB exceeds "
                f"maximum {self.config.max_file_size_mb}MB"
            )
            logger.warning(error)
            return False, error
        
        return True, ""
    
    def check_upload_rate(self) -> Tuple[bool, str]:
        """
        Check if upload rate limit allows new upload.
        
        Returns:
            (allowed: bool, error_message: str)
        """
        now = datetime.now()
        
        # Clean old upload times (older than 1 hour)
        cutoff = now - timedelta(hours=1)
        self.upload_times = [t for t in self.upload_times if t > cutoff]
        
        # Check rate limit
        if len(self.upload_times) >= self.config.max_uploads_per_hour:
            oldest = self.upload_times[0]
            retry_time = oldest + timedelta(hours=1)
            wait_seconds = int((retry_time - now).total_seconds())
            
            error = (
                f"Upload rate limit exceeded ({self.config.max_uploads_per_hour}/hour). "
                f"Please wait {wait_seconds}s before next upload."
            )
            logger.warning(error)
            return False, error
        
        return True, ""
    
    def check_concurrent_uploads(self) -> Tuple[bool, str]:
        """
        Check if concurrent upload limit allows new upload.
        
        Returns:
            (allowed: bool, error_message: str)
        """
        if self.concurrent_uploads >= self.config.max_concurrent_uploads:
            error = (
                f"Maximum concurrent uploads ({self.config.max_concurrent_uploads}) reached. "
                f"Please wait for current uploads to complete."
            )
            logger.warning(error)
            return False, error
        
        return True, ""
    
    def check_cooldown(self) -> Tuple[bool, str]:
        """
        Check if cooldown period after failed upload has expired.
        
        Returns:
            (allowed: bool, error_message: str)
        """
        if self.last_failed_upload_time is None:
            return True, ""
        
        now = datetime.now()
        elapsed = (now - self.last_failed_upload_time).total_seconds()
        
        if elapsed < self.config.cooldown_seconds:
            wait_seconds = int(self.config.cooldown_seconds - elapsed)
            error = f"Cooldown period active. Please wait {wait_seconds}s before retry."
            logger.warning(error)
            return False, error
        
        return True, ""
    
    def can_upload(self, file_size_bytes: int) -> Tuple[bool, str]:
        """
        Check if upload is allowed based on all rate limit rules.
        
        Args:
            file_size_bytes: File size in bytes
        
        Returns:
            (allowed: bool, error_message: str)
        """
        # Check file size
        size_ok, size_error = self.check_file_size(file_size_bytes)
        if not size_ok:
            return False, size_error
        
        # Check cooldown
        cooldown_ok, cooldown_error = self.check_cooldown()
        if not cooldown_ok:
            return False, cooldown_error
        
        # Check concurrent uploads
        concurrent_ok, concurrent_error = self.check_concurrent_uploads()
        if not concurrent_ok:
            return False, concurrent_error
        
        # Check upload rate
        rate_ok, rate_error = self.check_upload_rate()
        if not rate_ok:
            return False, rate_error
        
        return True, ""
    
    def record_upload_start(self) -> None:
        """Record that an upload is starting"""
        self.concurrent_uploads += 1
        logger.debug(f"Upload started. Concurrent uploads: {self.concurrent_uploads}")
    
    def record_upload_success(self) -> None:
        """Record successful upload completion"""
        now = datetime.now()
        self.upload_times.append(now)
        self.concurrent_uploads = max(0, self.concurrent_uploads - 1)
        self.last_failed_upload_time = None
        
        logger.info(
            f"Upload succeeded. "
            f"Total this hour: {len(self.upload_times)}/{self.config.max_uploads_per_hour}. "
            f"Concurrent: {self.concurrent_uploads}"
        )
    
    def record_upload_failure(self) -> None:
        """Record failed upload"""
        self.concurrent_uploads = max(0, self.concurrent_uploads - 1)
        self.last_failed_upload_time = datetime.now()
        
        logger.warning(
            f"Upload failed. Cooldown period started. "
            f"Concurrent uploads: {self.concurrent_uploads}"
        )
    
    def get_status(self) -> dict:
        """
        Get current rate limiter status.
        
        Returns:
            Dictionary with current limits and usage
        """
        now = datetime.now()
        cutoff = now - timedelta(hours=1)
        recent_uploads = len([t for t in self.upload_times if t > cutoff])
        
        return {
            'uploads_this_hour': recent_uploads,
            'max_uploads_per_hour': self.config.max_uploads_per_hour,
            'concurrent_uploads': self.concurrent_uploads,
            'max_concurrent_uploads': self.config.max_concurrent_uploads,
            'max_file_size_mb': self.config.max_file_size_mb,
            'cooldown_active': self.last_failed_upload_time is not None,
            'upload_times': [t.isoformat() for t in self.upload_times[-5:]]  # Last 5 uploads
        }
    
    def reset(self) -> None:
        """Reset all rate limits (for testing)"""
        self.upload_times = []
        self.concurrent_uploads = 0
        self.last_failed_upload_time = None
        logger.info("Rate limiter reset")
