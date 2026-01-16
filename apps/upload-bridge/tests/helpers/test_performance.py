"""
Performance Test Suite

Performance and scalability tests.
"""

import sys
import time
import gc
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from domain.pattern_state import PatternState
from domain.layers import LayerManager
from core.pattern import Pattern, Frame, PatternMetadata
from tests.helpers.report_generator import TestResult, TestSuiteResult

# Try to import psutil for memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class PerformanceTestSuite:
    """Test suite for performance tests."""
    
    def __init__(self, app: Optional[QApplication] = None):
        """Initialize test suite."""
        self.app = app or QApplication.instance() or QApplication(sys.argv)
        self.test_results: List[TestResult] = []
    
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
    
    def log_test(self, name: str, passed: bool, error_message: Optional[str] = None, execution_time: float = 0.0, details: Optional[Dict[str, Any]] = None):
        """Log test result."""
        self.test_results.append(TestResult(
            name=name,
            suite="Performance",
            passed=passed,
            skipped=False,
            error_message=error_message,
            execution_time=execution_time,
            details=details or {}
        ))
    
    def test_large_pattern(self) -> bool:
        """Test with large pattern (64x64, 100+ frames)."""
        start_time = time.time()
        memory_before = self.get_memory_usage()
        
        try:
            # Create large pattern
            pattern, state, manager = self.create_test_pattern(64, 64, 100)
            
            # Verify pattern created
            created = (pattern.metadata.width == 64 and 
                      pattern.metadata.height == 64 and 
                      len(pattern.frames) == 100)
            
            # Test operations
            operation_start = time.time()
            for i in range(10):  # Test 10 frames
                layers = manager.get_layers(i)
                if len(layers) == 0:
                    manager.add_layer(i, f"Layer {i}")
            
            operation_time = time.time() - operation_start
            memory_after = self.get_memory_usage()
            memory_delta = memory_after - memory_before
            
            # Allow up to 500MB for large pattern (64x64x100 = 4M pixels)
            memory_ok = memory_delta < 500 if PSUTIL_AVAILABLE else True
            time_ok = operation_time < 5.0  # Should complete in < 5 seconds
            
            passed = created and memory_ok and time_ok
            execution_time = time.time() - start_time
            
            self.log_test(
                "Large Pattern (64x64, 100 frames)",
                passed,
                None if passed else f"Memory: {memory_delta:.1f}MB, Time: {operation_time:.2f}s",
                execution_time,
                {'memory_delta_mb': memory_delta, 'operation_time': operation_time}
            )
            
            # Cleanup
            del pattern, state, manager
            gc.collect()
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Large Pattern (64x64, 100 frames)", False, str(e), execution_time)
            return False
    
    def test_many_layers(self) -> bool:
        """Test with many layers (20+ per frame)."""
        start_time = time.time()
        memory_before = self.get_memory_usage()
        
        try:
            pattern, state, manager = self.create_test_pattern(32, 32, 1)
            frame_index = 0
            
            # Add 20 layers
            operation_start = time.time()
            for i in range(20):
                manager.add_layer(frame_index, f"Layer {i}")
            
            operation_time = time.time() - operation_start
            
            # Verify all layers exist
            layers = manager.get_layers(frame_index)
            all_created = len(layers) >= 20
            
            # Test composite rendering
            render_start = time.time()
            for _ in range(5):  # Render 5 times
                manager.get_composite_pixels(frame_index)
            render_time = time.time() - render_start
            
            memory_after = self.get_memory_usage()
            memory_delta = memory_after - memory_before
            
            # Performance thresholds
            operation_ok = operation_time < 2.0  # Should be fast (more layers = more time)
            render_ok = render_time < 5.0  # Rendering should be reasonable (20 layers takes longer)
            memory_ok = memory_delta < 200 if PSUTIL_AVAILABLE else True  # Allow up to 200MB for 20 layers
            
            passed = all_created and operation_ok and render_ok and memory_ok
            execution_time = time.time() - start_time
            
            self.log_test(
                "Many Layers (20+ per frame)",
                passed,
                None if passed else f"Layers: {len(layers)}, Op time: {operation_time:.3f}s, Render: {render_time:.3f}s",
                execution_time,
                {'layer_count': len(layers), 'operation_time': operation_time, 'render_time': render_time}
            )
            
            # Cleanup
            del pattern, state, manager
            gc.collect()
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Many Layers (20+ per frame)", False, str(e), execution_time)
            return False
    
    def test_many_automation_layers(self) -> bool:
        """Test with many automation layers (5+)."""
        start_time = time.time()
        memory_before = self.get_memory_usage()
        
        try:
            pattern, state, manager = self.create_test_pattern(16, 16, 1)
            frame_index = 0
            
            # Add 5 automation layers
            operation_start = time.time()
            auto_names = ["Auto: Scroll Left", "Auto: Rotate 90", "Auto: Mirror H", 
                         "Auto: Invert", "Auto: Fade"]
            for name in auto_names:
                manager.add_layer(frame_index, name)
            
            operation_time = time.time() - operation_start
            
            # Verify all created
            layers = manager.get_layers(frame_index)
            auto_layers = [l for l in layers if l.name.startswith("Auto:")]
            all_created = len(auto_layers) >= 5
            
            # Test composite rendering with automation layers
            render_start = time.time()
            for _ in range(5):
                manager.get_composite_pixels(frame_index)
            render_time = time.time() - render_start
            
            memory_after = self.get_memory_usage()
            memory_delta = memory_after - memory_before
            
            operation_ok = operation_time < 1.0
            render_ok = render_time < 2.0
            memory_ok = memory_delta < 50 if PSUTIL_AVAILABLE else True
            
            passed = all_created and operation_ok and render_ok and memory_ok
            execution_time = time.time() - start_time
            
            self.log_test(
                "Many Automation Layers (5+)",
                passed,
                None if passed else f"Count: {len(auto_layers)}, Render: {render_time:.3f}s",
                execution_time,
                {'auto_layer_count': len(auto_layers), 'render_time': render_time}
            )
            
            # Cleanup
            del pattern, state, manager
            gc.collect()
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Many Automation Layers (5+)", False, str(e), execution_time)
            return False
    
    def test_very_large_pattern(self) -> bool:
        """Test with very large pattern (256×256, 100+ frames)."""
        start_time = time.time()
        memory_before = self.get_memory_usage()
        
        try:
            # Create very large pattern (256×256 = 65,536 pixels per frame)
            pattern, state, manager = self.create_test_pattern(256, 256, 100)
            
            # Verify pattern created
            created = (pattern.metadata.width == 256 and 
                      pattern.metadata.height == 256 and 
                      len(pattern.frames) == 100)
            
            # Test operations
            operation_start = time.time()
            for i in range(10):  # Test 10 frames
                layers = manager.get_layers(i)
                if len(layers) == 0:
                    manager.add_layer(i, f"Layer {i}")
            
            operation_time = time.time() - operation_start
            memory_after = self.get_memory_usage()
            memory_delta = memory_after - memory_before
            
            # 256×256×100 = 6.5M pixels = ~19.5MB for RGB data, allow up to 2GB for overhead
            memory_ok = memory_delta < 2000 if PSUTIL_AVAILABLE else True
            time_ok = operation_time < 30.0  # Should complete in < 30 seconds for very large pattern
            
            passed = created and memory_ok and time_ok
            execution_time = time.time() - start_time
            
            self.log_test(
                "Very Large Pattern (256×256, 100 frames)",
                passed,
                None if passed else f"Memory: {memory_delta:.1f}MB, Time: {operation_time:.2f}s",
                execution_time,
                {'memory_delta_mb': memory_delta, 'operation_time': operation_time}
            )
            
            # Cleanup
            del pattern, state, manager
            gc.collect()
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Very Large Pattern (256×256, 100 frames)", False, str(e), execution_time)
            return False
    
    def test_many_frames(self) -> bool:
        """Test with many frames (500+ frames)."""
        start_time = time.time()
        memory_before = self.get_memory_usage()
        
        try:
            # Create pattern with many frames (500 frames)
            pattern, state, manager = self.create_test_pattern(32, 32, 500)
            
            # Verify pattern created
            created = (pattern.metadata.width == 32 and 
                      pattern.metadata.height == 32 and 
                      len(pattern.frames) == 500)
            
            # Test operations across many frames
            operation_start = time.time()
            # Add layers to first, middle, and last frames
            manager.add_layer(0, "First Frame Layer")
            manager.add_layer(250, "Middle Frame Layer")
            manager.add_layer(499, "Last Frame Layer")
            
            # Test frame access
            for frame_idx in [0, 100, 200, 300, 400, 499]:
                layers = manager.get_layers(frame_idx)
                if frame_idx == 0 or frame_idx == 250 or frame_idx == 499:
                    # Should have at least one layer for these frames
                    if len(layers) == 0:
                        created = False
                        break
            
            operation_time = time.time() - operation_start
            memory_after = self.get_memory_usage()
            memory_delta = memory_after - memory_before
            
            # 32×32×500 = 512K pixels = ~1.5MB for RGB data, allow up to 500MB for overhead
            memory_ok = memory_delta < 500 if PSUTIL_AVAILABLE else True
            time_ok = operation_time < 10.0  # Should complete in < 10 seconds
            
            passed = created and memory_ok and time_ok
            execution_time = time.time() - start_time
            
            self.log_test(
                "Many Frames (500+ frames)",
                passed,
                None if passed else f"Memory: {memory_delta:.1f}MB, Time: {operation_time:.2f}s",
                execution_time,
                {'memory_delta_mb': memory_delta, 'operation_time': operation_time, 'frame_count': len(pattern.frames)}
            )
            
            # Cleanup
            del pattern, state, manager
            gc.collect()
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Many Frames (500+ frames)", False, str(e), execution_time)
            return False
    
    def test_batch_operations(self) -> bool:
        """Test batch operations performance."""
        start_time = time.time()
        memory_before = self.get_memory_usage()
        
        try:
            pattern, state, manager = self.create_test_pattern(16, 16, 10)
            
            # Test copying layer to many frames
            source_frame = 0
            source_layer = manager.add_layer(source_frame, "Source")
            test_pixels = [(100, 100, 100)] * (16 * 16)
            manager.replace_pixels(source_frame, test_pixels, source_layer)
            
            operation_start = time.time()
            for i in range(1, 10):
                target_layer = manager.add_layer(i, "Copy")
                manager.replace_pixels(i, test_pixels, target_layer)
            
            operation_time = time.time() - operation_start
            
            # Verify all copied - check that layers exist and have correct pixels
            # Since we're adding layers per frame, each frame should have multiple layers
            # We should check that each frame has at least one "Copy" layer with correct pixels
            all_copied = True
            for i in range(1, 10):
                layers = manager.get_layers(i)
                if len(layers) == 0:
                    all_copied = False
                    break
                # Find all "Copy" layers
                copy_layers = [layer for layer in layers if layer.name == "Copy"]
                if len(copy_layers) == 0:
                    # If no "Copy" layer found, check if any layer has the correct pixels
                    # This handles cases where layer names might differ
                    found_match = False
                    for layer in layers:
                        if len(layer.pixels) > 0 and layer.pixels[0] == test_pixels[0]:
                            found_match = True
                            break
                    if not found_match:
                        all_copied = False
                        break
                else:
                    # Check that at least one copy layer has correct pixels
                    found_match = False
                    for copy_layer in copy_layers:
                        if len(copy_layer.pixels) > 0 and copy_layer.pixels[0] == test_pixels[0]:
                            found_match = True
                            break
                    if not found_match:
                        all_copied = False
                        break
            
            memory_after = self.get_memory_usage()
            memory_delta = memory_after - memory_before
            
            operation_ok = operation_time < 2.0  # Should be fast
            memory_ok = memory_delta < 200 if PSUTIL_AVAILABLE else True
            
            passed = all_copied and operation_ok and memory_ok
            execution_time = time.time() - start_time
            
            self.log_test(
                "Batch Operations (Copy to 9 frames)",
                passed,
                None if passed else f"Time: {operation_time:.3f}s, Memory: {memory_delta:.1f}MB",
                execution_time,
                {'operation_time': operation_time, 'memory_delta_mb': memory_delta}
            )
            
            # Cleanup
            del pattern, state, manager
            gc.collect()
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Batch Operations (Copy to 9 frames)", False, str(e), execution_time)
            return False
    
    def run_all_tests(self) -> TestSuiteResult:
        """Run all performance tests."""
        print("\n" + "=" * 60)
        print("Performance Test Suite")
        print("=" * 60)
        
        test_methods = [
            self.test_large_pattern,
            self.test_very_large_pattern,
            self.test_many_frames,
            self.test_many_layers,
            self.test_many_automation_layers,
            self.test_batch_operations,
        ]
        
        start_time = time.time()
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"ERROR in {test_method.__name__}: {e}")
        
        execution_time = time.time() - start_time
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r.passed)
        failed = total - passed
        skipped = sum(1 for r in self.test_results if r.skipped)
        
        suite_result = TestSuiteResult(
            name="Performance",
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            execution_time=execution_time,
            tests=self.test_results
        )
        
        print(f"\nPerformance: {passed}/{total} passed ({execution_time:.2f}s)")
        
        return suite_result

