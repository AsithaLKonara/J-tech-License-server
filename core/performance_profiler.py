"""
Performance profiling and optimization utilities for LED Matrix Studio.

Provides tools to measure and optimize rendering, effects, and memory usage.
"""

import time
import psutil
import numpy as np
from typing import Dict, List, Any, Callable, Optional
from contextlib import contextmanager
import gc

from domain.project import Project
from core.compositor import render_frame


class PerformanceProfiler:
    """
    Comprehensive performance profiling for LED Matrix Studio.
    """

    def __init__(self):
        self.results = {}
        self.memory_baseline = None

    @contextmanager
    def profile_section(self, name: str):
        """Context manager for profiling code sections."""
        start_time = time.perf_counter()
        start_memory = psutil.Process().memory_info().rss

        try:
            yield
        finally:
            end_time = time.perf_counter()
            end_memory = psutil.Process().memory_info().rss

            self.results[name] = {
                'duration': end_time - start_time,
                'memory_delta': end_memory - start_memory,
                'memory_mb': (end_memory - start_memory) / (1024 * 1024)
            }

    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics."""
        process = psutil.Process()
        memory = process.memory_info()

        return {
            'rss': memory.rss / (1024 * 1024),  # MB
            'vms': memory.vms / (1024 * 1024),  # MB
            'percent': process.memory_percent()
        }

    def profile_rendering(self, project: Project, frames_to_test: Optional[List[int]] = None) -> Dict[str, Any]:
        """Profile rendering performance."""
        if not frames_to_test:
            frames_to_test = list(range(min(30, project.timeline.total_frames)))

        results = {
            'frame_times': [],
            'total_time': 0,
            'avg_fps': 0,
            'memory_usage': {}
        }

        start_time = time.time()
        memory_usage = []

        for frame_idx in frames_to_test:
            frame_start = time.perf_counter()
            frame = render_frame(project, frame_idx)
            frame_end = time.perf_counter()

            if frame is not None:
                frame_time = frame_end - frame_start
                results['frame_times'].append(frame_time)
                memory_usage.append(self.get_memory_usage()['rss'])

        total_time = time.time() - start_time
        results['total_time'] = total_time
        results['avg_fps'] = len(frames_to_test) / total_time if total_time > 0 else 0
        results['memory_usage'] = {
            'avg_mb': np.mean(memory_usage),
            'max_mb': np.max(memory_usage),
            'min_mb': np.min(memory_usage)
        }

        return results

    def profile_effects(self, project: Project, effect_func: Callable,
                       frames_to_test: int = 10) -> Dict[str, Any]:
        """Profile effect application performance."""
        results = {
            'effect_times': [],
            'total_time': 0,
            'frames_per_second': 0
        }

        start_time = time.time()

        for frame_idx in range(min(frames_to_test, project.timeline.total_frames)):
            frame_start = time.perf_counter()
            effect_func(project.layers[0], frame_idx)  # Apply to first layer
            frame_end = time.perf_counter()

            effect_time = frame_end - frame_start
            results['effect_times'].append(effect_time)

        total_time = time.time() - start_time
        results['total_time'] = total_time
        results['frames_per_second'] = frames_to_test / total_time if total_time > 0 else 0

        return results

    def optimize_numpy_operations(self) -> Dict[str, str]:
        """Provide NumPy optimization recommendations."""
        recommendations = {}

        # Check NumPy threading
        import os
        num_threads = os.environ.get('OMP_NUM_THREADS', 'Not set')
        recommendations['threading'] = f"OMP_NUM_THREADS={num_threads}. Consider setting to 1 for consistent performance."

        # Check if we have multiple cores available
        cpu_count = psutil.cpu_count()
        recommendations['cpu_cores'] = f"Available CPU cores: {cpu_count}"

        # Memory layout recommendations
        recommendations['memory_layout'] = "Use contiguous arrays for better performance"

        return recommendations

    def benchmark_matrix_sizes(self, sizes: List[tuple] = None) -> Dict[str, Any]:
        """Benchmark performance across different matrix sizes."""
        if not sizes:
            sizes = [(8, 8), (16, 8), (32, 16), (64, 32)]

        results = {}

        for width, height in sizes:
            # Create test project
            from domain.timeline import Timeline
            from domain.layer_track import LayerTrack
            from core.frame_utils import empty_frame

            timeline = Timeline(fps=30, duration_seconds=1.0)
            project = Project(timeline=timeline)

            layer = LayerTrack(
                name=f"Benchmark {width}x{height}",
                frames=[empty_frame(width, height) for _ in range(timeline.total_frames)]
            )
            project.layers.append(layer)

            # Profile rendering
            render_results = self.profile_rendering(project)
            results[f"{width}x{height}"] = render_results

        return results

    def detect_memory_leaks(self, project: Project, iterations: int = 10) -> Dict[str, Any]:
        """Detect potential memory leaks by monitoring memory usage over iterations."""
        memory_usage = []
        gc.collect()  # Clean up before starting

        for i in range(iterations):
            # Force garbage collection
            gc.collect()

            # Render frames
            for frame_idx in range(min(5, project.timeline.total_frames)):
                render_frame(project, frame_idx)

            # Record memory
            memory_usage.append(self.get_memory_usage()['rss'])

        # Analyze memory trend
        memory_array = np.array(memory_usage)
        slope = np.polyfit(range(len(memory_array)), memory_array, 1)[0]

        results = {
            'memory_trend': 'increasing' if slope > 1.0 else 'stable',
            'slope_mb_per_iteration': slope,
            'avg_memory_mb': np.mean(memory_usage),
            'memory_variance': np.var(memory_usage)
        }

        return results

    def get_optimization_suggestions(self, profile_results: Dict[str, Any]) -> List[str]:
        """Generate optimization suggestions based on profiling results."""
        suggestions = []

        # Check rendering performance
        if 'avg_fps' in profile_results:
            fps = profile_results['avg_fps']
            if fps < 15:
                suggestions.append("Rendering performance is low. Consider reducing layer count or matrix size.")
            if fps < 30:
                suggestions.append("For real-time preview, target 30+ FPS. Consider optimizing compositing.")

        # Check memory usage
        if 'memory_usage' in profile_results:
            mem = profile_results['memory_usage']
            if mem.get('avg_mb', 0) > 50:
                suggestions.append("High memory usage detected. Consider reducing frame count or matrix resolution.")

        # General suggestions
        suggestions.extend([
            "Use NumPy's vectorized operations for better performance",
            "Consider caching rendered frames for preview",
            "Profile effects individually to identify bottlenecks",
            "Use appropriate data types (uint8 for pixel data)"
        ])

        return suggestions


# Global profiler instance
performance_profiler = PerformanceProfiler()


def profile_function(func: Callable) -> Callable:
    """Decorator to profile function execution."""
    def wrapper(*args, **kwargs):
        with performance_profiler.profile_section(func.__name__):
            return func(*args, **kwargs)
    return wrapper


# Convenience functions for common profiling tasks
def benchmark_rendering(project: Project, frames: int = 30) -> Dict[str, Any]:
    """Quick rendering benchmark."""
    return performance_profiler.profile_rendering(project, list(range(min(frames, project.timeline.total_frames))))


def check_memory_usage() -> Dict[str, float]:
    """Quick memory usage check."""
    return performance_profiler.get_memory_usage()


def get_performance_report(project: Project) -> Dict[str, Any]:
    """Generate comprehensive performance report."""
    report = {
        'rendering': performance_profiler.profile_rendering(project),
        'memory': performance_profiler.get_memory_usage(),
        'optimizations': performance_profiler.optimize_numpy_operations(),
        'suggestions': performance_profiler.get_optimization_suggestions(
            performance_profiler.profile_rendering(project)
        )
    }

    return report
