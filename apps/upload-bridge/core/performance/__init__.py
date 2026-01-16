"""
Performance optimization modules.
"""

from .cache import FrameCache, get_frame_cache, clear_frame_cache

# Import from parent module file (core.performance module, not this package)
# This allows imports like "from core.performance import PerformanceMonitor"
# to work even though there's both a core/performance.py file and core/performance/ package
import importlib.util
from pathlib import Path

_parent_module_path = Path(__file__).parent.parent / "performance.py"
if _parent_module_path.exists():
    _spec = importlib.util.spec_from_file_location("core.performance_module", _parent_module_path)
    _perf_module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_perf_module)
    
    # Re-export classes and functions from parent module
    PerformanceMonitor = _perf_module.PerformanceMonitor
    LRUCache = _perf_module.LRUCache
    timed_operation = _perf_module.timed_operation
    get_performance_monitor = _perf_module.get_performance_monitor
else:
    # Fallback if parent module doesn't exist
    PerformanceMonitor = None
    LRUCache = None
    timed_operation = None
    get_performance_monitor = None

__all__ = [
    "FrameCache",
    "get_frame_cache",
    "clear_frame_cache",
    "PerformanceMonitor",
    "LRUCache",
    "timed_operation",
    "get_performance_monitor",
]

