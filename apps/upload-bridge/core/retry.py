"""
Retry Utility Module

Provides retry decorators and utilities for handling transient errors.
Supports exponential backoff, configurable attempts, and custom exception handling.
"""

import time
import logging
from functools import wraps
from typing import Callable, Type, Tuple, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Retry strategies."""

    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    CONSTANT = "constant"


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None,
    on_failure: Optional[Callable[[Exception], None]] = None,
):
    """
    Retry decorator with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        delay: Initial delay in seconds (default: 1.0)
        backoff: Backoff multiplier (default: 2.0)
        strategy: Retry strategy (exponential, linear, constant)
        exceptions: Tuple of exceptions to catch and retry on
        on_retry: Optional callback called on each retry (attempt_num, exception)
        on_failure: Optional callback called on final failure (exception)

    Example:
        @retry(max_attempts=3, delay=1.0, exceptions=(ConnectionError, TimeoutError))
        def network_request():
            # ... network code ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_attempts:
                        # Call retry callback if provided
                        if on_retry:
                            try:
                                on_retry(attempt, e)
                            except Exception:
                                pass

                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay:.2f}s..."
                        )

                        time.sleep(current_delay)

                        # Calculate next delay based on strategy
                        if strategy == RetryStrategy.EXPONENTIAL:
                            current_delay *= backoff
                        elif strategy == RetryStrategy.LINEAR:
                            current_delay += backoff
                        # CONSTANT: keep current_delay unchanged
                    else:
                        # Final attempt failed
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {e}"
                        )
                        if on_failure:
                            try:
                                on_failure(e)
                            except Exception:
                                pass

            # All attempts failed, raise last exception
            raise last_exception

        return wrapper

    return decorator


def retry_network_errors(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
):
    """
    Convenience decorator for network operations.

    Retries on common network errors:
    - ConnectionError
    - TimeoutError
    - requests.exceptions.RequestException

    Args:
        max_attempts: Maximum retry attempts (default: 3)
        delay: Initial delay in seconds (default: 1.0)
        backoff: Backoff multiplier (default: 2.0)
    """
    try:
        import requests

        network_exceptions = (
            ConnectionError,
            TimeoutError,
            requests.exceptions.RequestException,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        )
    except ImportError:
        network_exceptions = (ConnectionError, TimeoutError)

    return retry(
        max_attempts=max_attempts,
        delay=delay,
        backoff=backoff,
        strategy=RetryStrategy.EXPONENTIAL,
        exceptions=network_exceptions,
    )


def retry_device_errors(
    max_attempts: int = 3,
    delay: float = 0.5,
    backoff: float = 1.5,
):
    """
    Convenience decorator for device operations.

    Retries on common device errors:
    - Serial port errors
    - Device communication timeouts
    - Device not responding

    Args:
        max_attempts: Maximum retry attempts (default: 3)
        delay: Initial delay in seconds (default: 0.5)
        backoff: Backoff multiplier (default: 1.5)
    """
    device_exceptions = (
        IOError,
        OSError,
        TimeoutError,
    )

    # Add serial-specific exceptions if available
    try:
        import serial

        device_exceptions += (
            serial.SerialException,
            serial.SerialTimeoutException,
        )
    except ImportError:
        pass

    return retry(
        max_attempts=max_attempts,
        delay=delay,
        backoff=backoff,
        strategy=RetryStrategy.EXPONENTIAL,
        exceptions=device_exceptions,
    )


def retry_file_operations(
    max_attempts: int = 3,
    delay: float = 0.1,
    backoff: float = 1.5,
):
    """
    Convenience decorator for file I/O operations.

    Retries on common file errors:
    - PermissionError
    - IOError
    - OSError (for file operations)

    Args:
        max_attempts: Maximum retry attempts (default: 3)
        delay: Initial delay in seconds (default: 0.1)
        backoff: Backoff multiplier (default: 1.5)
    """
    file_exceptions = (
        PermissionError,
        IOError,
        OSError,
    )

    return retry(
        max_attempts=max_attempts,
        delay=delay,
        backoff=backoff,
        strategy=RetryStrategy.EXPONENTIAL,
        exceptions=file_exceptions,
    )


class RetryableOperation:
    """
    Context manager for retryable operations with manual retry control.

    Example:
        with RetryableOperation(max_attempts=3) as op:
            try:
                result = risky_operation()
                op.mark_success()
            except Exception as e:
                if op.should_retry():
                    op.retry()
                else:
                    raise
    """

    def __init__(
        self,
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    ):
        self.max_attempts = max_attempts
        self.delay = delay
        self.backoff = backoff
        self.strategy = strategy
        self.attempt = 0
        self.success = False
        self.current_delay = delay

    def __enter__(self):
        self.attempt = 0
        self.success = False
        self.current_delay = self.delay
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.success

    def mark_success(self):
        """Mark operation as successful."""
        self.success = True

    def should_retry(self) -> bool:
        """Check if operation should retry."""
        return self.attempt < self.max_attempts

    def retry(self):
        """Increment attempt and wait before retry."""
        if not self.should_retry():
            raise RuntimeError("Max attempts reached")

        self.attempt += 1
        time.sleep(self.current_delay)

        # Calculate next delay
        if self.strategy == RetryStrategy.EXPONENTIAL:
            self.current_delay *= self.backoff
        elif self.strategy == RetryStrategy.LINEAR:
            self.current_delay += self.backoff
