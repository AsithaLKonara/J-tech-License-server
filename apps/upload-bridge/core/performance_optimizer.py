"""
Performance optimization utilities for Upload Bridge.

Provides:
- Operation caching with TTL
- Performance benchmarking
- Memory profiling
- Request batching
- Lazy loading support
"""

import logging
import time
import functools
import hashlib
import pickle
from typing import Dict, Optional, Callable, Any, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from threading import Lock
from collections import OrderedDict
import tracemalloc


logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Entry in cache"""
    
    value: Any
    timestamp: datetime = field(default_factory=datetime.now)
    hits: int = 0
    ttl_seconds: float = 300.0
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        age = datetime.now() - self.timestamp
        return age.total_seconds() > self.ttl_seconds
    
    def record_hit(self):
        """Record a cache hit"""
        self.hits += 1


class TTLCache:
    """Time-To-Live cache with automatic expiration"""
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 300.0):
        """
        Initialize TTL cache.
        
        Args:
            max_size: Maximum number of entries
            default_ttl: Default TTL in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()
        self._hits = 0
        self._misses = 0
    
    def _make_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = (args, tuple(sorted(kwargs.items())))
        key_bytes = pickle.dumps(key_data)
        return hashlib.md5(key_bytes).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._cache[key]
            
            # Check if expired
            if entry.is_expired:
                del self._cache[key]
                self._misses += 1
                return None
            
            # Update hit count
            entry.record_hit()
            self._hits += 1
            
            # Move to end (LRU)
            self._cache.move_to_end(key)
            
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
        """
        ttl_seconds = ttl or self.default_ttl
        
        with self._lock:
            # Remove oldest if at max size
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._cache.popitem(last=False)
            
            entry = CacheEntry(value=value, ttl_seconds=ttl_seconds)
            self._cache[key] = entry
    
    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate,
                'total_requests': total_requests,
            }


class CachedOperation:
    """Decorator for caching operation results"""
    
    def __init__(self, cache: Optional[TTLCache] = None, ttl: float = 300.0):
        """
        Initialize cached operation.
        
        Args:
            cache: Cache instance (creates new if not provided)
            ttl: Time-to-live in seconds
        """
        self.cache = cache or TTLCache()
        self.ttl = ttl
    
    def __call__(self, func: Callable) -> Callable:
        """
        Decorate function with caching.
        
        Args:
            func: Function to decorate
        
        Returns:
            Decorated function
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = self.cache._make_key(*args, **kwargs)
            
            # Try to get from cache
            cached_value = self.cache.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value
            
            # Call function
            logger.debug(f"Cache miss for {func.__name__}, calling function")
            result = func(*args, **kwargs)
            
            # Store in cache
            self.cache.set(key, result, self.ttl)
            
            return result
        
        return wrapper


class PerformanceBenchmark:
    """Tracks performance metrics for operations"""
    
    def __init__(self, operation_name: str):
        """
        Initialize benchmark.
        
        Args:
            operation_name: Name of operation
        """
        self.operation_name = operation_name
        self.durations: List[float] = []
        self._start_time: Optional[float] = None
    
    def __enter__(self):
        """Context manager entry"""
        self._start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self._start_time is not None:
            duration = time.perf_counter() - self._start_time
            self.durations.append(duration)
            
            if exc_type is None:
                logger.debug(f"{self.operation_name} took {duration:.3f}s")
            else:
                logger.warning(f"{self.operation_name} failed after {duration:.3f}s")
    
    @property
    def total_duration(self) -> float:
        """Total duration of all operations"""
        return sum(self.durations)
    
    @property
    def average_duration(self) -> float:
        """Average duration per operation"""
        if not self.durations:
            return 0.0
        return self.total_duration / len(self.durations)
    
    @property
    def min_duration(self) -> float:
        """Minimum duration"""
        return min(self.durations) if self.durations else 0.0
    
    @property
    def max_duration(self) -> float:
        """Maximum duration"""
        return max(self.durations) if self.durations else 0.0
    
    @property
    def operation_count(self) -> int:
        """Number of operations"""
        return len(self.durations)
    
    def get_stats(self) -> Dict[str, float]:
        """Get benchmark statistics"""
        return {
            'total_duration': self.total_duration,
            'average_duration': self.average_duration,
            'min_duration': self.min_duration,
            'max_duration': self.max_duration,
            'operation_count': self.operation_count,
        }


class MemoryProfiler:
    """Profiles memory usage"""
    
    def __init__(self):
        """Initialize memory profiler"""
        self._snapshots: List[Tuple[str, tracemalloc.Snapshot]] = []
    
    def start(self):
        """Start memory tracking"""
        tracemalloc.start()
    
    def stop(self):
        """Stop memory tracking"""
        tracemalloc.stop()
    
    def take_snapshot(self, label: str):
        """
        Take memory snapshot.
        
        Args:
            label: Snapshot label
        """
        snapshot = tracemalloc.take_snapshot()
        self._snapshots.append((label, snapshot))
    
    def compare_snapshots(self) -> List[Dict[str, Any]]:
        """
        Compare consecutive snapshots.
        
        Returns:
            List of differences
        """
        differences = []
        
        for i in range(1, len(self._snapshots)):
            prev_label, prev_snapshot = self._snapshots[i - 1]
            curr_label, curr_snapshot = self._snapshots[i]
            
            top_stats = curr_snapshot.compare_to(prev_snapshot, 'lineno')
            
            for stat in top_stats[:10]:  # Top 10 differences
                differences.append({
                    'from': prev_label,
                    'to': curr_label,
                    'statistic': str(stat),
                })
        
        return differences
    
    def get_current_memory(self) -> Dict[str, float]:
        """
        Get current memory usage.
        
        Returns:
            Memory usage statistics
        """
        current, peak = tracemalloc.get_traced_memory()
        
        return {
            'current_mb': current / 1024 / 1024,
            'peak_mb': peak / 1024 / 1024,
        }


class RequestBatcher:
    """Batches requests for improved performance"""
    
    def __init__(self, batch_size: int = 10, timeout: float = 1.0):
        """
        Initialize request batcher.
        
        Args:
            batch_size: Maximum batch size
            timeout: Timeout for batch completion (seconds)
        """
        self.batch_size = batch_size
        self.timeout = timeout
        self._batch: List[Any] = []
        self._lock = Lock()
        self._last_flush = time.time()
    
    def add(self, item: Any) -> bool:
        """
        Add item to batch.
        
        Args:
            item: Item to add
        
        Returns:
            True if batch is ready to process
        """
        with self._lock:
            self._batch.append(item)
            
            # Check if batch is full
            if len(self._batch) >= self.batch_size:
                return True
            
            # Check if timeout expired
            if time.time() - self._last_flush > self.timeout and len(self._batch) > 0:
                return True
            
            return False
    
    def get_batch(self) -> List[Any]:
        """
        Get current batch.
        
        Returns:
            List of batched items
        """
        with self._lock:
            batch = self._batch.copy()
            self._batch.clear()
            self._last_flush = time.time()
            return batch
    
    def flush(self) -> List[Any]:
        """
        Force flush batch.
        
        Returns:
            Items in batch
        """
        return self.get_batch()


class LazyProperty:
    """Lazy-loaded property that caches result"""
    
    def __init__(self, func: Callable):
        """
        Initialize lazy property.
        
        Args:
            func: Function to call for value
        """
        self.func = func
        self.value = None
        self.loaded = False
    
    def __get__(self, obj, objtype=None):
        """Get lazy property value"""
        if not self.loaded:
            self.value = self.func(obj)
            self.loaded = True
        return self.value
    
    def reset(self):
        """Reset lazy property"""
        self.value = None
        self.loaded = False


class PerformanceOptimizer:
    """Central performance optimization service"""
    
    def __init__(self):
        """Initialize optimizer"""
        self._caches: Dict[str, TTLCache] = {}
        self._benchmarks: Dict[str, PerformanceBenchmark] = {}
        self._lock = Lock()
    
    def get_cache(self, name: str, max_size: int = 1000) -> TTLCache:
        """
        Get or create named cache.
        
        Args:
            name: Cache name
            max_size: Maximum cache size
        
        Returns:
            TTL cache instance
        """
        with self._lock:
            if name not in self._caches:
                self._caches[name] = TTLCache(max_size=max_size)
            return self._caches[name]
    
    def get_benchmark(self, name: str) -> PerformanceBenchmark:
        """
        Get or create benchmark.
        
        Args:
            name: Benchmark name
        
        Returns:
            Performance benchmark
        """
        with self._lock:
            if name not in self._benchmarks:
                self._benchmarks[name] = PerformanceBenchmark(name)
            return self._benchmarks[name]
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get all performance statistics"""
        with self._lock:
            return {
                'caches': {
                    name: cache.get_stats()
                    for name, cache in self._caches.items()
                },
                'benchmarks': {
                    name: bench.get_stats()
                    for name, bench in self._benchmarks.items()
                },
            }
    
    def clear_all(self):
        """Clear all caches"""
        with self._lock:
            for cache in self._caches.values():
                cache.clear()


# Global optimizer instance
_optimizer: Optional[PerformanceOptimizer] = None


def get_optimizer() -> PerformanceOptimizer:
    """Get global performance optimizer"""
    global _optimizer
    
    if _optimizer is None:
        _optimizer = PerformanceOptimizer()
    
    return _optimizer


def cached(cache_name: str = "default", ttl: float = 300.0) -> Callable:
    """
    Decorator for caching function results.
    
    Args:
        cache_name: Name of cache to use
        ttl: Time-to-live in seconds
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        optimizer = get_optimizer()
        cache = optimizer.get_cache(cache_name)
        
        return CachedOperation(cache=cache, ttl=ttl)(func)
    
    return decorator
