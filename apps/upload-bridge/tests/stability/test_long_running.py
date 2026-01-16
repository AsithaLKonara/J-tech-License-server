"""
Long-Running Stability Tests

Tests application stability over extended periods (2+ hours).
Includes memory leak detection and resource monitoring.
"""

import sys
import time
import gc
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from domain.pattern_state import PatternState
from domain.layers import LayerManager
from core.pattern import Pattern, Frame, PatternMetadata

# Try to import psutil for memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class LongRunningStabilityTest:
    """Test suite for long-running stability tests."""
    
    def __init__(self, app: Optional[QApplication] = None):
        """Initialize test suite."""
        self.app = app or QApplication.instance() or QApplication(sys.argv)
        self.results: List[Dict[str, Any]] = []
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        if PSUTIL_AVAILABLE:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        return 0.0
    
    def create_test_pattern(self, width: int, height: int, num_frames: int) -> tuple[Pattern, PatternState, LayerManager]:
        """Create a test pattern with state and manager."""
        pattern_state = PatternState()
        layer_manager = LayerManager(pattern_state)
        
        metadata = PatternMetadata(width=width, height=height)
        frames = []
        for i in range(num_frames):
            pixels = [(i * 10 % 256, i * 20 % 256, i * 30 % 256)] * (width * height)
            frame = Frame(pixels=pixels, duration_ms=100)
            frames.append(frame)
        
        pattern = Pattern(metadata=metadata, frames=frames)
        pattern_state.set_pattern(pattern)
        layer_manager.set_pattern(pattern)
        
        return pattern, pattern_state, layer_manager
    
    def test_tab_switching_stability(self, duration_minutes: int = 5, iterations: int = 100) -> Dict[str, Any]:
        """
        Test tab switching repeatedly for memory leaks.
        
        Note: This simulates tab switching by creating/destroying patterns.
        For actual tab switching, UI tests would be needed.
        """
        start_time = time.time()
        memory_samples = []
        
        try:
            memory_before = self.get_memory_usage()
            
            # Simulate tab switching by creating/destroying patterns
            for i in range(iterations):
                # Create pattern (simulate loading a tab)
                pattern, state, manager = self.create_test_pattern(32, 32, 50)
                
                # Perform operations (simulate tab activity)
                for frame_idx in range(min(10, len(pattern.frames))):
                    layers = manager.get_layers(frame_idx)
                    if len(layers) == 0:
                        manager.add_layer(frame_idx, f"Layer {i}-{frame_idx}")
                    pixels = manager.get_composite_pixels(frame_idx)
                
                # Destroy pattern (simulate closing tab)
                del pattern, state, manager
                gc.collect()
                
                # Sample memory every 10 iterations
                if i % 10 == 0:
                    memory_samples.append(self.get_memory_usage())
                
                # Check time limit
                elapsed = time.time() - start_time
                if elapsed > duration_minutes * 60:
                    break
            
            memory_after = self.get_memory_usage()
            memory_delta = memory_after - memory_before
            memory_max = max(memory_samples) if memory_samples else memory_before
            memory_growth = memory_max - memory_before
            
            # Check for significant memory leak (more than 50MB growth)
            has_leak = memory_growth > 50.0
            
            return {
                'test_name': 'Tab Switching Stability',
                'passed': not has_leak,
                'duration_seconds': time.time() - start_time,
                'iterations': i + 1,
                'memory_before_mb': memory_before,
                'memory_after_mb': memory_after,
                'memory_delta_mb': memory_delta,
                'memory_max_mb': memory_max,
                'memory_growth_mb': memory_growth,
                'has_leak': has_leak,
            }
        except Exception as e:
            return {
                'test_name': 'Tab Switching Stability',
                'passed': False,
                'error': str(e),
                'duration_seconds': time.time() - start_time,
            }
    
    def test_pattern_loading_cycles(self, duration_minutes: int = 5, cycles: int = 200) -> Dict[str, Any]:
        """Test loading/unloading patterns repeatedly."""
        start_time = time.time()
        memory_samples = []
        
        try:
            memory_before = self.get_memory_usage()
            
            for i in range(cycles):
                # Load pattern
                pattern, state, manager = self.create_test_pattern(64, 64, 100)
                
                # Use pattern
                for frame_idx in range(min(20, len(pattern.frames))):
                    pixels = manager.get_composite_pixels(frame_idx)
                
                # Unload pattern
                del pattern, state, manager
                gc.collect()
                
                # Sample memory
                if i % 20 == 0:
                    memory_samples.append(self.get_memory_usage())
                
                # Check time limit
                elapsed = time.time() - start_time
                if elapsed > duration_minutes * 60:
                    break
            
            memory_after = self.get_memory_usage()
            memory_max = max(memory_samples) if memory_samples else memory_before
            memory_growth = memory_max - memory_before
            
            has_leak = memory_growth > 50.0
            
            return {
                'test_name': 'Pattern Loading Cycles',
                'passed': not has_leak,
                'duration_seconds': time.time() - start_time,
                'cycles': i + 1,
                'memory_before_mb': memory_before,
                'memory_after_mb': memory_after,
                'memory_max_mb': memory_max,
                'memory_growth_mb': memory_growth,
                'has_leak': has_leak,
            }
        except Exception as e:
            return {
                'test_name': 'Pattern Loading Cycles',
                'passed': False,
                'error': str(e),
                'duration_seconds': time.time() - start_time,
            }
    
    def test_long_animation_preview(self, duration_minutes: int = 5, pattern_size: tuple = (32, 32, 100)) -> Dict[str, Any]:
        """Test long-running animation preview (simulated)."""
        start_time = time.time()
        memory_samples = []
        
        try:
            pattern, state, manager = self.create_test_pattern(*pattern_size)
            memory_before = self.get_memory_usage()
            
            iterations = 0
            target_duration = duration_minutes * 60
            
            # Simulate animation preview (cycling through frames)
            while time.time() - start_time < target_duration:
                frame_idx = iterations % len(pattern.frames)
                
                # Get composite pixels (simulate rendering)
                pixels = manager.get_composite_pixels(frame_idx)
                
                iterations += 1
                
                # Sample memory every 100 iterations
                if iterations % 100 == 0:
                    memory_samples.append(self.get_memory_usage())
                    gc.collect()
            
            memory_after = self.get_memory_usage()
            memory_max = max(memory_samples) if memory_samples else memory_before
            memory_growth = memory_max - memory_before
            
            has_leak = memory_growth > 50.0
            
            return {
                'test_name': 'Long Animation Preview',
                'passed': not has_leak,
                'duration_seconds': time.time() - start_time,
                'iterations': iterations,
                'memory_before_mb': memory_before,
                'memory_after_mb': memory_after,
                'memory_max_mb': memory_max,
                'memory_growth_mb': memory_growth,
                'has_leak': has_leak,
            }
        except Exception as e:
            return {
                'test_name': 'Long Animation Preview',
                'passed': False,
                'error': str(e),
                'duration_seconds': time.time() - start_time,
            }
    
    def run_all(self, duration_minutes: int = 5) -> List[Dict[str, Any]]:
        """
        Run all stability tests.
        
        Args:
            duration_minutes: Duration for each test in minutes (default 5 for quick testing,
                            use 120+ for full 2+ hour test)
        """
        results = []
        
        print(f"Running stability tests (duration: {duration_minutes} minutes per test)...")
        
        # Test 1: Tab switching
        print("Testing tab switching stability...")
        results.append(self.test_tab_switching_stability(duration_minutes=duration_minutes))
        
        # Test 2: Pattern loading cycles
        print("Testing pattern loading cycles...")
        results.append(self.test_pattern_loading_cycles(duration_minutes=duration_minutes))
        
        # Test 3: Long animation preview
        print("Testing long animation preview...")
        results.append(self.test_long_animation_preview(duration_minutes=duration_minutes))
        
        return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run long-running stability tests")
    parser.add_argument(
        "--duration",
        type=int,
        default=5,
        help="Duration per test in minutes (default: 5, use 120+ for full 2+ hour test)"
    )
    
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    test_suite = LongRunningStabilityTest(app)
    results = test_suite.run_all(duration_minutes=args.duration)
    
    print("\n" + "=" * 60)
    print("STABILITY TEST RESULTS")
    print("=" * 60)
    
    for result in results:
        print(f"\n{result['test_name']}:")
        print(f"  Passed: {result['passed']}")
        print(f"  Duration: {result.get('duration_seconds', 0):.1f}s")
        if 'error' in result:
            print(f"  Error: {result['error']}")
        else:
            print(f"  Memory Growth: {result.get('memory_growth_mb', 0):.2f} MB")
            print(f"  Has Leak: {result.get('has_leak', False)}")
    
    # Exit code
    all_passed = all(r['passed'] for r in results)
    sys.exit(0 if all_passed else 1)

