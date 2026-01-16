"""
Circuit breaker pattern implementation for resilient error recovery.

This module provides a circuit breaker implementation that prevents
cascading failures and provides fast-fail behavior when services are down.
"""

import logging
import time
from typing import Callable, Any, Optional, TypeVar, Generic
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"           # Failures exceeded, rejecting calls
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5        # Failures before opening
    success_threshold: int = 2        # Successes to close from half-open
    timeout_seconds: int = 60         # Time before trying again
    expected_exception: type = Exception


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreaker(Generic[T]):
    """
    Circuit breaker for preventing cascading failures.
    
    States:
    - CLOSED: Normal operation, calls go through
    - OPEN: Too many failures, calls rejected immediately
    - HALF_OPEN: Testing if service recovered, limited calls allowed
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Circuit breaker name (for logging)
            config: CircuitBreakerConfig instance
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_check_time: Optional[datetime] = None
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should try to reset the circuit"""
        if self.state != CircuitState.OPEN:
            return False
        
        if self.last_failure_time is None:
            return False
        
        timeout = timedelta(seconds=self.config.timeout_seconds)
        elapsed = datetime.now() - self.last_failure_time
        
        return elapsed >= timeout
    
    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
        
        Returns:
            Function return value
        
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Any exception from the wrapped function
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(f"Circuit {self.name} attempting reset (HALF_OPEN)")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise CircuitBreakerError(f"Circuit {self.name} is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        
        except Exception as e:
            self._on_failure(e)
            raise
    
    def _on_success(self) -> None:
        """Handle successful call"""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            
            if self.success_count >= self.config.success_threshold:
                logger.info(f"Circuit {self.name} closed (recovered)")
                self.state = CircuitState.CLOSED
                self.success_count = 0
        
        self.last_check_time = datetime.now()
    
    def _on_failure(self, exception: Exception) -> None:
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        self.last_check_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            # Failure while testing, go back to OPEN
            logger.warning(f"Circuit {self.name} reopened (still failing)")
            self.state = CircuitState.OPEN
            self.success_count = 0
        
        elif self.failure_count >= self.config.failure_threshold:
            logger.error(f"Circuit {self.name} opened (threshold exceeded)")
            self.state = CircuitState.OPEN
    
    def get_status(self) -> dict:
        """
        Get circuit breaker status.
        
        Returns:
            Dictionary with current state, failure count, etc.
        """
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'last_failure': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'last_check': self.last_check_time.isoformat() if self.last_check_time else None,
        }
    
    def reset(self) -> None:
        """Manually reset the circuit breaker"""
        logger.info(f"Circuit {self.name} manually reset")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers"""
    
    _instance: Optional['CircuitBreakerRegistry'] = None
    _breakers: dict[str, CircuitBreaker] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_breaker(cls, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """
        Get or create a circuit breaker.
        
        Args:
            name: Circuit breaker name
            config: Configuration if creating new
        
        Returns:
            CircuitBreaker instance
        """
        registry = cls()
        
        if name not in registry._breakers:
            registry._breakers[name] = CircuitBreaker(name, config)
        
        return registry._breakers[name]
    
    @classmethod
    def get_all_status(cls) -> dict[str, dict]:
        """
        Get status of all circuit breakers.
        
        Returns:
            Dictionary mapping breaker names to status
        """
        registry = cls()
        return {name: breaker.get_status() for name, breaker in registry._breakers.items()}
    
    @classmethod
    def reset_all(cls) -> None:
        """Reset all circuit breakers"""
        registry = cls()
        for breaker in registry._breakers.values():
            breaker.reset()


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    timeout_seconds: int = 60,
) -> Callable:
    """
    Decorator for circuit breaker protection.
    
    Args:
        name: Circuit breaker name
        failure_threshold: Failures before opening
        timeout_seconds: Time before attempting reset
    
    Returns:
        Decorator function
    """
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        timeout_seconds=timeout_seconds,
    )
    breaker = CircuitBreakerRegistry.get_breaker(name, config)
    
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        
        return wrapper
    
    return decorator


# Example usage and documentation
def example_usage():
    """
    Example of using circuit breaker.
    
    Usage:
        # As decorator
        @circuit_breaker('external_api', failure_threshold=3, timeout_seconds=30)
        def call_external_api():
            # Make API call
            pass
        
        # Or manual usage
        breaker = CircuitBreakerRegistry.get_breaker('external_api')
        try:
            result = breaker.call(call_external_api)
        except CircuitBreakerError:
            logger.error("External API is down, using fallback")
        
        # Check status
        status = CircuitBreakerRegistry.get_all_status()
        for name, info in status.items():
            print(f"{name}: {info['state']}")
    """
    pass
