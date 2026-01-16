"""
FPS Measurement Test Suite

Tests animation preview frame rate (target: ≥30 FPS).
"""

import sys
import time
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


class FPSMeasurementSuite:
    """Test suite for FPS measurement tests."""
    
    # Target FPS: 30 FPS minimum for smooth animation
    TARGET_FPS = 30.0
    
    def __init__(self, app: Optional[QApplication] = None):
        """Initialize test suite."""
        self.app = app or QApplication.instance() or QApplication(sys.argv)
        self.test_results: List[TestResult] = []
    
    def create_test_pattern(self, width: int, height: int, num_frames: int) -> Pattern:
        """Create a test pattern."""
        metadata = PatternMetadata(width=width, height=height)
        frames = []
        for i in range(num_frames):
            pixels = [(i * 10 % 256, i * 20 % 256, i * 30 % 256)] * (width * height)
            frame = Frame(pixels=pixels, duration_ms=100)
            frames.append(frame)
        return Pattern(metadata=metadata, frames=frames)
    
    def measure_fps(self, pattern: Pattern, frames_to_render: int = 60, warmup_frames: int = 5) -> float:
        """
        Measure FPS by rendering frames.
        
        Args:
            pattern: Pattern to render
            frames_to_render: Number of frames to render for measurement
            warmup_frames: Number of frames to render before starting measurement (for cache warmup)
        
        Returns:
            Frames per second (FPS)
        """
        state = PatternState()
        manager = LayerManager(state)
        state.set_pattern(pattern)
        manager.set_pattern(pattern)
        
        # Warmup: render first few frames to warm up caches
        for i in range(warmup_frames):
            if i < len(pattern.frames):
                manager.get_composite_pixels(i)
        
        # Actual measurement
        start_time = time.time()
        for i in range(frames_to_render):
            frame_idx = i % len(pattern.frames)
            manager.get_composite_pixels(frame_idx)
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        if elapsed_time > 0:
            fps = frames_to_render / elapsed_time
        else:
            fps = float('inf')
        
        # Cleanup
        del state, manager
        
        return fps
    
    def log_test(self, name: str, passed: bool, error_message: Optional[str] = None, 
                 execution_time: float = 0.0, details: Optional[Dict[str, Any]] = None):
        """Log test result."""
        self.test_results.append(TestResult(
            name=name,
            suite="FPS Measurement",
            passed=passed,
            skipped=False,
            error_message=error_message,
            execution_time=execution_time,
            details=details or {}
        ))
    
    def test_small_pattern_fps(self) -> bool:
        """Test FPS with small pattern (16×16, 30 frames)."""
        start_time = time.time()
        
        try:
            pattern = self.create_test_pattern(16, 16, 30)
            fps = self.measure_fps(pattern, frames_to_render=60)
            
            passed = fps >= self.TARGET_FPS
            execution_time = time.time() - start_time
            
            self.log_test(
                "Small Pattern FPS (16×16, 30 frames)",
                passed,
                None if passed else f"FPS: {fps:.2f} (target: ≥{self.TARGET_FPS})",
                execution_time,
                {'fps': fps, 'target_fps': self.TARGET_FPS}
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Small Pattern FPS (16×16, 30 frames)", False, str(e), execution_time)
            return False
    
    def test_medium_pattern_fps(self) -> bool:
        """Test FPS with medium pattern (64×64, 100 frames)."""
        start_time = time.time()
        
        try:
            pattern = self.create_test_pattern(64, 64, 100)
            fps = self.measure_fps(pattern, frames_to_render=60)
            
            passed = fps >= self.TARGET_FPS
            execution_time = time.time() - start_time
            
            self.log_test(
                "Medium Pattern FPS (64×64, 100 frames)",
                passed,
                None if passed else f"FPS: {fps:.2f} (target: ≥{self.TARGET_FPS})",
                execution_time,
                {'fps': fps, 'target_fps': self.TARGET_FPS}
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Medium Pattern FPS (64×64, 100 frames)", False, str(e), execution_time)
            return False
    
    def test_large_pattern_fps(self) -> bool:
        """Test FPS with large pattern (128×128, 200 frames)."""
        start_time = time.time()
        
        try:
            pattern = self.create_test_pattern(128, 128, 200)
            fps = self.measure_fps(pattern, frames_to_render=60)
            
            # Allow slightly lower FPS for very large patterns (target: ≥25 FPS)
            target_fps = 25.0
            passed = fps >= target_fps
            execution_time = time.time() - start_time
            
            self.log_test(
                "Large Pattern FPS (128×128, 200 frames)",
                passed,
                None if passed else f"FPS: {fps:.2f} (target: ≥{target_fps})",
                execution_time,
                {'fps': fps, 'target_fps': target_fps}
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Large Pattern FPS (128×128, 200 frames)", False, str(e), execution_time)
            return False
    
    def test_many_frames_fps(self) -> bool:
        """Test FPS with many frames (32×32, 500 frames)."""
        start_time = time.time()
        
        try:
            pattern = self.create_test_pattern(32, 32, 500)
            fps = self.measure_fps(pattern, frames_to_render=60)
            
            passed = fps >= self.TARGET_FPS
            execution_time = time.time() - start_time
            
            self.log_test(
                "Many Frames FPS (32×32, 500 frames)",
                passed,
                None if passed else f"FPS: {fps:.2f} (target: ≥{self.TARGET_FPS})",
                execution_time,
                {'fps': fps, 'target_fps': self.TARGET_FPS, 'frame_count': len(pattern.frames)}
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Many Frames FPS (32×32, 500 frames)", False, str(e), execution_time)
            return False
    
    def test_multiple_layers_fps(self) -> bool:
        """Test FPS with multiple layers (64×64, 30 frames, 10 layers)."""
        start_time = time.time()
        
        try:
            pattern = self.create_test_pattern(64, 64, 30)
            state = PatternState()
            manager = LayerManager(state)
            state.set_pattern(pattern)
            manager.set_pattern(pattern)
            
            # Add 10 layers to first frame
            frame_idx = 0
            for i in range(10):
                manager.add_layer(frame_idx, f"Layer {i}")
            
            # Warmup
            for _ in range(5):
                manager.get_composite_pixels(frame_idx)
            
            # Measure FPS (render same frame with multiple layers multiple times)
            frames_to_render = 60
            start_measure = time.time()
            for _ in range(frames_to_render):
                manager.get_composite_pixels(frame_idx)
            end_measure = time.time()
            
            elapsed_time = end_measure - start_measure
            if elapsed_time > 0:
                fps = frames_to_render / elapsed_time
            else:
                fps = float('inf')
            
            # Allow slightly lower FPS for multiple layers (target: ≥25 FPS)
            target_fps = 25.0
            passed = fps >= target_fps
            execution_time = time.time() - start_time
            
            # Cleanup
            del state, manager
            
            self.log_test(
                "Multiple Layers FPS (64×64, 10 layers)",
                passed,
                None if passed else f"FPS: {fps:.2f} (target: ≥{target_fps})",
                execution_time,
                {'fps': fps, 'target_fps': target_fps, 'layer_count': 10}
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Multiple Layers FPS (64×64, 10 layers)", False, str(e), execution_time)
            return False
    
    def run_all_tests(self) -> TestSuiteResult:
        """Run all FPS measurement tests."""
        print("\n" + "=" * 60)
        print("FPS Measurement Test Suite")
        print("=" * 60)
        print(f"Target FPS: ≥{self.TARGET_FPS} FPS")
        print("=" * 60)
        
        test_methods = [
            self.test_small_pattern_fps,
            self.test_medium_pattern_fps,
            self.test_large_pattern_fps,
            self.test_many_frames_fps,
            self.test_multiple_layers_fps,
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
            name="FPS Measurement",
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            execution_time=execution_time,
            tests=self.test_results
        )
        
        print(f"\nFPS Measurement: {passed}/{total} passed ({execution_time:.2f}s)")
        if failed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result.passed:
                    print(f"  - {result.name}: {result.error_message}")
        
        return suite_result


if __name__ == '__main__':
    suite = FPSMeasurementSuite()
    result = suite.run_all_tests()
    sys.exit(0 if result.failed == 0 else 1)

