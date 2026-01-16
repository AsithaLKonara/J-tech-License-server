"""
Performance Budget Tracking - Monitor and enforce performance budgets

Provides performance budget tracking for different matrix sizes and operations.
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import time


class PerformanceLevel(Enum):
    """Performance quality levels"""
    HIGH = "high"  # 60 FPS
    MEDIUM = "medium"  # 30 FPS
    LOW = "low"  # 15 FPS


@dataclass
class PerformanceBudget:
    """Performance budget for operations"""
    target_fps: float
    max_frame_time_ms: float
    max_matrix_size: Tuple[int, int]  # (width, height)
    enabled_precomputation: bool = False


class PerformanceBudgetTracker:
    """Tracks performance budgets for different matrix sizes"""
    
    # Performance budgets by matrix size
    BUDGETS = {
        (8, 8): PerformanceBudget(target_fps=60.0, max_frame_time_ms=16.67, max_matrix_size=(8, 8)),
        (16, 16): PerformanceBudget(target_fps=60.0, max_frame_time_ms=16.67, max_matrix_size=(16, 16)),
        (32, 32): PerformanceBudget(target_fps=60.0, max_frame_time_ms=16.67, max_matrix_size=(32, 32)),
        (64, 32): PerformanceBudget(target_fps=30.0, max_frame_time_ms=33.33, max_matrix_size=(64, 32)),
        (128, 64): PerformanceBudget(target_fps=15.0, max_frame_time_ms=66.67, max_matrix_size=(128, 64)),
    }
    
    @classmethod
    def get_budget(cls, width: int, height: int) -> PerformanceBudget:
        """
        Get performance budget for matrix size.
        
        Args:
            width: Matrix width
            height: Matrix height
            
        Returns:
            PerformanceBudget for the size (or default for larger)
        """
        size = (width, height)
        
        # Exact match
        if size in cls.BUDGETS:
            return cls.BUDGETS[size]
        
        # Find closest size
        best_match = None
        best_pixels = float('inf')
        
        for budget_size, budget in cls.BUDGETS.items():
            budget_pixels = budget_size[0] * budget_size[1]
            size_pixels = width * height
            
            if budget_pixels >= size_pixels and budget_pixels < best_pixels:
                best_match = budget
                best_pixels = budget_pixels
        
        # Default budget for large matrices
        if best_match is None:
            return PerformanceBudget(
                target_fps=10.0,
                max_frame_time_ms=100.0,
                max_matrix_size=(width, height),
                enabled_precomputation=True
            )
        
        return best_match
    
    @classmethod
    def get_target_fps(cls, width: int, height: int) -> float:
        """Get target FPS for matrix size"""
        return cls.get_budget(width, height).target_fps
    
    @classmethod
    def should_precompute(cls, width: int, height: int) -> bool:
        """Check if precomputation should be enabled"""
        return cls.get_budget(width, height).enabled_precomputation
    
    @classmethod
    def measure_operation(cls, operation, *args, **kwargs) -> Tuple[Any, float]:
        """
        Measure operation execution time.
        
        Args:
            operation: Callable to measure
            *args: Arguments for operation
            **kwargs: Keyword arguments for operation
            
        Returns:
            Tuple of (result, execution_time_ms)
        """
        start_time = time.perf_counter()
        result = operation(*args, **kwargs)
        end_time = time.perf_counter()
        
        execution_time_ms = (end_time - start_time) * 1000.0
        
        return result, execution_time_ms

