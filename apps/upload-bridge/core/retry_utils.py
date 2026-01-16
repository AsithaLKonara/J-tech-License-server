"""
Retry Logic for Network Operations
Provides exponential backoff and automatic retry for transient failures
"""

import logging
import time
import requests
from typing import Callable, TypeVar, Optional, Any
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        backoff_factor: float = 2.0,
        jitter: bool = True
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_attempts: Maximum number of attempts (including first)
            initial_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            backoff_factor: Multiplier for exponential backoff
            jitter: Whether to add random jitter to delays
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter


def calculate_backoff(
    attempt: int,
    config: RetryConfig
) -> float:
    """
    Calculate delay for exponential backoff.
    
    Args:
        attempt: Attempt number (0-indexed)
        config: RetryConfig instance
    
    Returns:
        Delay in seconds
    """
    delay = config.initial_delay * (config.backoff_factor ** attempt)
    delay = min(delay, config.max_delay)
    
    if config.jitter:
        import random
        delay *= (0.5 + random.random())  # Add ±50% jitter
    
    return delay


def should_retry(exception: Exception) -> bool:
    """
    Determine if an exception should trigger a retry.
    
    Args:
        exception: Exception that was raised
    
    Returns:
        True if should retry, False if should fail immediately
    """
    # Retry on transient network errors
    if isinstance(exception, requests.exceptions.ConnectionError):
        return True
    
    if isinstance(exception, requests.exceptions.Timeout):
        return True
    
    # Retry on server errors (5xx)
    if isinstance(exception, requests.exceptions.HTTPError):
        if hasattr(exception, 'response') and exception.response.status_code >= 500:
            return True
    
    # Don't retry on client errors (4xx) or other exceptions
    return False


def retry_with_backoff(config: RetryConfig = None):
    """
    Decorator for automatic retry with exponential backoff.
    
    Args:
        config: RetryConfig instance
    
    Example:
        @retry_with_backoff(RetryConfig(max_attempts=3))
        def upload_pattern(data):
            ...
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Optional[T]:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    logger.debug(
                        f"Calling {func.__name__} "
                        f"[attempt {attempt + 1}/{config.max_attempts}]"
                    )
                    return func(*args, **kwargs)
                
                except Exception as e:
                    last_exception = e
                    
                    # Check if we should retry
                    if not should_retry(e) or attempt == config.max_attempts - 1:
                        logger.error(
                            f"{func.__name__} failed (no retry): {type(e).__name__}: {e}"
                        )
                        raise
                    
                    # Calculate delay
                    delay = calculate_backoff(attempt, config)
                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    
                    # Wait before retry
                    time.sleep(delay)
            
            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


def retry_request(
    method: str,
    url: str,
    config: RetryConfig = None,
    **kwargs
) -> Optional[requests.Response]:
    """
    Perform HTTP request with automatic retry.
    
    Args:
        method: HTTP method ('GET', 'POST', etc.)
        url: Target URL
        config: RetryConfig instance
        **kwargs: Additional arguments for requests
    
    Returns:
        Response object or None if all retries failed
    """
    if config is None:
        config = RetryConfig()
    
    @retry_with_backoff(config)
    def _make_request():
        return requests.request(method, url, **kwargs)
    
    try:
        return _make_request()
    except Exception as e:
        logger.error(f"Request to {url} failed after {config.max_attempts} attempts: {e}")
        return None


class RetryableOperation:
    """
    Context manager for retryable operations.
    
    Example:
        with RetryableOperation() as operation:
            operation.execute(lambda: some_operation())
    """
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
        self.attempt = 0
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return False
        
        # Check if we should retry
        if not should_retry(exc_val) or self.attempt >= self.config.max_attempts - 1:
            return False
        
        # Log retry
        delay = calculate_backoff(self.attempt, self.config)
        logger.warning(
            f"Operation failed: {exc_val}. "
            f"Retrying in {delay:.1f}s "
            f"[attempt {self.attempt + 1}/{self.config.max_attempts}]"
        )
        
        # Wait before retry
        time.sleep(delay)
        self.attempt += 1
        
        return True  # Suppress exception, will retry
    
    def execute(self, operation: Callable[[], T]) -> Optional[T]:
        """
        Execute an operation with automatic retry.
        
        Args:
            operation: Callable that performs the operation
        
        Returns:
            Result of operation or None if failed
        """
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                logger.debug(
                    f"Executing operation [attempt {attempt + 1}/{self.config.max_attempts}]"
                )
                return operation()
            
            except Exception as e:
                last_exception = e
                
                if not should_retry(e) or attempt == self.config.max_attempts - 1:
                    logger.error(f"Operation failed (no retry): {e}")
                    raise
                
                # Calculate delay and retry
                delay = calculate_backoff(attempt, self.config)
                logger.warning(
                    f"Operation failed: {e}. Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
        
        if last_exception:
            raise last_exception
        
        return None
