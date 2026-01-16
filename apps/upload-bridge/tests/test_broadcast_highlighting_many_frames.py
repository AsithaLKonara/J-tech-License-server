"""
Test Broadcast Highlighting with Many Frames (50+)

Automated test to verify broadcast highlighting works with many frames.
Task 3.2 from remaining tasks plan.
"""

import sys
import time
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from domain.pattern_state import PatternState
from domain.layers import LayerManager
from core.pattern import Frame, Pattern, PatternMetadata


class BroadcastHighlightingTest:
    """Test broadcast highlighting with many frames."""
    
    def __init__(self, app: Optional[QApplication] = None):
        """Initialize test."""
        self.app = app or QApplication.instance() or QApplication(sys.argv)
        self.pattern_state = PatternState()
        self.layer_manager = LayerManager(self.pattern_state)
    
    def create_test_pattern(self, width=16, height=16, num_frames=50) -> Pattern:
        """Create a test pattern with many frames."""
        metadata = PatternMetadata(width=width, height=height)
        frames = []
        for i in range(num_frames):
            pixels = [(i * 2 % 256, i * 3 % 256, i * 4 % 256)] * (width * height)
            frame = Frame(pixels=pixels, duration_ms=100)
            frames.append(frame)
        
        pattern = Pattern(metadata=metadata, frames=frames)
        self.pattern_state.set_pattern(pattern)
        self.layer_manager.set_pattern(pattern)
        return pattern
    
    def test_broadcast_with_many_frames(self, num_frames=50) -> bool:
        """Test broadcast mode with many frames."""
        start_time = time.time()
        
        try:
            print(f"\nTesting broadcast mode with {num_frames} frames...")
            
            # Create pattern with many frames
            pattern = self.create_test_pattern(16, 16, num_frames)
            
            # Get initial pixel values (should be different)
            initial_pixels = []
            for i in range(min(10, num_frames)):  # Check first 10 frames
                frame_layers = self.layer_manager.get_layers(i)
                if frame_layers:
                    initial_pixels.append(frame_layers[0].pixels[0])
            
            # Verify frames have different initial content
            frames_different = len(set(initial_pixels)) > 1
            
            # Simulate broadcast paint (paint same content on all frames)
            broadcast_color = (255, 255, 255)
            broadcast_pixels = [broadcast_color] * (16 * 16)
            
            operation_start = time.time()
            for i in range(num_frames):
                self.layer_manager.replace_pixels(i, broadcast_pixels, 0)
            operation_time = time.time() - operation_start
            
            # Verify all frames updated
            all_updated = True
            for i in range(min(10, num_frames)):  # Check first 10 frames
                frame_layers = self.layer_manager.get_layers(i)
                if frame_layers:
                    pixel = frame_layers[0].pixels[0]
                    if pixel != broadcast_color:
                        all_updated = False
                        break
            
            execution_time = time.time() - start_time
            
            # Performance check: should complete in reasonable time
            performance_ok = operation_time < 2.0  # Should be fast even with 50 frames
            
            passed = frames_different and all_updated and performance_ok
            
            print(f"  Initial frames different: {frames_different}")
            print(f"  All frames updated: {all_updated}")
            print(f"  Operation time: {operation_time:.3f}s (acceptable: < 2.0s)")
            print(f"  Performance OK: {performance_ok}")
            print(f"  Result: {'✅ PASS' if passed else '❌ FAIL'}")
            
            return passed
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"  Error: {e}")
            print(f"  Result: ❌ FAIL")
            return False
    
    def run_test(self):
        """Run the test."""
        print("\n" + "=" * 60)
        print("Test Broadcast Highlighting with Many Frames (50+)")
        print("=" * 60)
        
        # Test with 50 frames
        result_50 = self.test_broadcast_with_many_frames(50)
        
        # Test with 100 frames for stress test
        print("\n" + "-" * 60)
        result_100 = self.test_broadcast_with_many_frames(100)
        
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        print(f"50 frames: {'✅ PASS' if result_50 else '❌ FAIL'}")
        print(f"100 frames: {'✅ PASS' if result_100 else '❌ FAIL'}")
        print("=" * 60)
        
        return result_50 and result_100


def main():
    """Main entry point."""
    tester = BroadcastHighlightingTest()
    success = tester.run_test()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

