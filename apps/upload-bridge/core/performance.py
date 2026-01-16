"""
Performance Utilities - Optimization helpers for pattern loading and processing.

Provides caching, lazy loading, and performance monitoring utilities.
"""

import time
import functools
from typing import Dict, Any, Optional, Callable
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor and log performance metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
    
    def time_operation(self, operation_name: str):
        """Context manager for timing operations."""
        return _TimingContext(self, operation_name)
    
    def record_metric(self, name: str, value: float):
        """Record a performance metric."""
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(value)
    
    def get_average(self, name: str) -> Optional[float]:
        """Get average time for an operation."""
        if name not in self.metrics or not self.metrics[name]:
            return None
        return sum(self.metrics[name]) / len(self.metrics[name])
    
    def get_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary statistics for all metrics."""
        summary = {}
        for name, values in self.metrics.items():
            if values:
                summary[name] = {
                    'count': len(values),
                    'total': sum(values),
                    'average': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values)
                }
        return summary


class _TimingContext:
    """Context manager for timing operations."""
    
    def __init__(self, monitor: PerformanceMonitor, operation_name: str):
        self.monitor = monitor
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.monitor.record_metric(self.operation_name, duration)
            logger.debug(f"{self.operation_name} took {duration:.3f}s")


def timed_operation(operation_name: Optional[str] = None):
    """
    Decorator to time a function execution.
    
    Usage:
        @timed_operation("load_pattern")
        def load_pattern(file_path):
            ...
    """
    def decorator(func: Callable):
        name = operation_name or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                logger.debug(f"{name} took {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(f"{name} failed after {duration:.3f}s: {e}")
                raise
        
        return wrapper
    return decorator


class LRUCache:
    """Simple LRU cache implementation."""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
        self.hits = 0
        self.misses = 0
    
    def get(self, key: Any) -> Optional[Any]:
        """Get value from cache."""
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None
    
    def put(self, key: Any, value: Any):
        """Put value in cache."""
        if key in self.cache:
            # Update existing
            self.cache.move_to_end(key)
        else:
            # Check if we need to evict
            if len(self.cache) >= self.max_size:
                # Remove oldest (first item)
                self.cache.popitem(last=False)
        
        self.cache[key] = value
    
    def clear(self):
        """Clear the cache."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.1f}%"
        }


# Global performance monitor instance
_performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    return _performance_monitor

