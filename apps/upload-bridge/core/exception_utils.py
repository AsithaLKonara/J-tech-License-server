"""
Exception Handling Utilities
Provides safe, consistent exception handling for HTTP requests and file operations
"""

import logging
import requests
from typing import Optional, Callable, TypeVar, Any
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


def safe_request(
    method: str,
    url: str,
    timeout: float = 10.0,
    max_retries: int = 1,
    **kwargs
) -> Optional[requests.Response]:
    """
    Safely make HTTP requests with proper exception handling and logging.
    
    Args:
        method: HTTP method ('GET', 'POST', etc.)
        url: Target URL
        timeout: Request timeout in seconds
        max_retries: Number of retry attempts
        **kwargs: Additional arguments to pass to requests
    
    Returns:
        Response object if successful, None on failure
    
    Raises:
        Nothing - all exceptions are caught and logged
    """
    attempt = 0
    last_error = None
    
    while attempt < max_retries:
        try:
            response = requests.request(
                method,
                url,
                timeout=timeout,
                **kwargs
            )
            response.raise_for_status()
            return response
            
        except requests.exceptions.ConnectionError as e:
            last_error = e
            logger.warning(f"[Attempt {attempt + 1}/{max_retries}] Connection error for {url}: {e}")
            
        except requests.exceptions.Timeout as e:
            last_error = e
            logger.warning(f"[Attempt {attempt + 1}/{max_retries}] Timeout for {url} after {timeout}s: {e}")
            
        except requests.exceptions.HTTPError as e:
            last_error = e
            logger.error(f"[Attempt {attempt + 1}/{max_retries}] HTTP error for {url}: {e.response.status_code} - {e}")
            if e.response.status_code < 500:
                # Don't retry on client errors
                return None
            
        except requests.exceptions.RequestException as e:
            last_error = e
            logger.error(f"[Attempt {attempt + 1}/{max_retries}] Request error for {url}: {e}")
            
        except Exception as e:
            last_error = e
            logger.error(f"[Attempt {attempt + 1}/{max_retries}] Unexpected error for {url}: {e}", exc_info=True)
            return None
        
        attempt += 1
    
    # All retries failed
    logger.error(f"Request failed after {max_retries} attempts. Last error: {last_error}")
    return None


def handle_exceptions(*exception_types):
    """
    Decorator for handling specific exceptions with logging.
    
    Args:
        *exception_types: Exception types to catch
    
    Example:
        @handle_exceptions(ValueError, KeyError)
        def my_function():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Optional[T]:
            try:
                return func(*args, **kwargs)
            except exception_types as e:
                logger.error(
                    f"Error in {func.__name__}: {type(e).__name__}: {e}",
                    exc_info=True
                )
                return None
        return wrapper
    return decorator


class SafeFileOperation:
    """Context manager for safe file operations with automatic cleanup."""
    
    def __init__(self, file_path: str, mode: str = 'r', auto_cleanup: bool = True):
        self.file_path = file_path
        self.mode = mode
        self.auto_cleanup = auto_cleanup
        self.file_handle = None
    
    def __enter__(self):
        try:
            self.file_handle = open(self.file_path, self.mode)
            return self.file_handle
        except OSError as e:
            logger.error(f"Failed to open file {self.file_path}: {e}")
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file_handle:
            try:
                self.file_handle.close()
            except OSError as e:
                logger.error(f"Failed to close file {self.file_path}: {e}")
        
        # Cleanup on error if enabled
        if exc_type is not None and self.auto_cleanup:
            try:
                import os
                if os.path.exists(self.file_path):
                    os.unlink(self.file_path)
                    logger.info(f"Cleaned up file {self.file_path} after exception")
            except OSError as e:
                logger.error(f"Failed to cleanup file {self.file_path}: {e}")
        
        return False  # Don't suppress exceptions


class TempBinaryFile:
    """Context manager for temporary binary files with guaranteed cleanup."""
    
    def __init__(self, data: bytes, suffix: str = '.bin'):
        import tempfile
        self.data = data
        self.suffix = suffix
        self.temp_file = None
        self.temp_path = None
    
    def __enter__(self) -> str:
        try:
            import tempfile
            self.temp_file = tempfile.NamedTemporaryFile(
                suffix=self.suffix,
                delete=False,
                mode='wb'
            )
            self.temp_path = self.temp_file.name
            self.temp_file.write(self.data)
            self.temp_file.close()
            logger.debug(f"Created temporary file: {self.temp_path} ({len(self.data)} bytes)")
            return self.temp_path
        except Exception as e:
            logger.error(f"Failed to create temporary file: {e}", exc_info=True)
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_path:
            try:
                import os
                if os.path.exists(self.temp_path):
                    os.unlink(self.temp_path)
                    logger.debug(f"Cleaned up temporary file: {self.temp_path}")
            except OSError as e:
                logger.error(f"Failed to cleanup temporary file {self.temp_path}: {e}")
        
        return False  # Don't suppress exceptions
