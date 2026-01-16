"""
Tests for performance utilities.
"""

import unittest
import time
from core.performance import PerformanceMonitor, LRUCache, timed_operation


class TestPerformanceMonitor(unittest.TestCase):
    """Test performance monitoring utilities."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = PerformanceMonitor()
    
    def test_time_operation(self):
        """Test timing an operation."""
        with self.monitor.time_operation("test_op"):
            time.sleep(0.01)  # Small delay
        
        avg = self.monitor.get_average("test_op")
        self.assertIsNotNone(avg)
        self.assertGreater(avg, 0)
    
    def test_record_metric(self):
        """Test recording metrics."""
        self.monitor.record_metric("test", 1.5)
        self.monitor.record_metric("test", 2.5)
        
        avg = self.monitor.get_average("test")
        self.assertEqual(avg, 2.0)
    
    def test_get_summary(self):
        """Test getting summary statistics."""
        self.monitor.record_metric("test", 1.0)
        self.monitor.record_metric("test", 2.0)
        self.monitor.record_metric("test", 3.0)
        
        summary = self.monitor.get_summary()
        self.assertIn("test", summary)
        self.assertEqual(summary["test"]["count"], 3)
        self.assertEqual(summary["test"]["average"], 2.0)
        self.assertEqual(summary["test"]["min"], 1.0)
        self.assertEqual(summary["test"]["max"], 3.0)


class TestLRUCache(unittest.TestCase):
    """Test LRU cache implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cache = LRUCache(max_size=3)
    
    def test_basic_operations(self):
        """Test basic cache operations."""
        self.cache.put("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")
        
        self.assertIsNone(self.cache.get("key2"))
    
    def test_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")
        self.cache.put("key3", "value3")
        
        # Cache is full, adding another should evict key1
        self.cache.put("key4", "value4")
        
        self.assertIsNone(self.cache.get("key1"))  # Evicted
        self.assertEqual(self.cache.get("key2"), "value2")
        self.assertEqual(self.cache.get("key3"), "value3")
        self.assertEqual(self.cache.get("key4"), "value4")
    
    def test_access_updates_lru(self):
        """Test that accessing updates LRU order."""
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")
        self.cache.put("key3", "value3")
        
        # Access key1 to make it most recently used
        self.cache.get("key1")
        
        # Add key4, should evict key2 (least recently used)
        self.cache.put("key4", "value4")
        
        self.assertEqual(self.cache.get("key1"), "value1")  # Still there
        self.assertIsNone(self.cache.get("key2"))  # Evicted
        self.assertEqual(self.cache.get("key3"), "value3")
        self.assertEqual(self.cache.get("key4"), "value4")
    
    def test_cache_stats(self):
        """Test cache statistics."""
        self.cache.put("key1", "value1")
        self.cache.get("key1")  # Hit
        self.cache.get("key2")  # Miss
        
        stats = self.cache.get_stats()
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertIn("hit_rate", stats)
    
    def test_clear_cache(self):
        """Test clearing cache."""
        self.cache.put("key1", "value1")
        self.cache.get("key1")  # Create a hit before clearing
        self.cache.clear()
        
        self.assertIsNone(self.cache.get("key1"))
        stats = self.cache.get_stats()
        self.assertEqual(stats["hits"], 0)
        self.assertEqual(stats["misses"], 1)  # One miss from get("key1") after clear


class TestTimedOperation(unittest.TestCase):
    """Test timed operation decorator."""
    
    def test_timed_operation(self):
        """Test timing a function."""
        @timed_operation("test_function")
        def test_func():
            time.sleep(0.01)
            return "result"
        
        result = test_func()
        self.assertEqual(result, "result")


if __name__ == '__main__':
    unittest.main()

