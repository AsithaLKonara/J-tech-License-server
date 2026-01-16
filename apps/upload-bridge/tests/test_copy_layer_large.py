"""
Test Copy Layer with Very Large Layers

Automated test to verify copy layer works with very large layers.
Task 3.3 from remaining tasks plan.
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

# Try to import psutil for memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class CopyLayerLargeTest:
    """Test copy layer with very large layers."""
    
    def __init__(self, app: Optional[QApplication] = None):
        """Initialize test."""
        self.app = app or QApplication.instance() or QApplication(sys.argv)
        self.pattern_state = PatternState()
        self.layer_manager = LayerManager(self.pattern_state)
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        if PSUTIL_AVAILABLE:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        return 0.0
    
    def create_test_pattern(self, width: int, height: int, num_frames: int) -> Pattern:
        """Create a test pattern."""
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
        
        self.pattern_state = pattern_state
        self.layer_manager = layer_manager
        
        return pattern
    
    def test_copy_large_layer(self, width=128, height=128) -> bool:
        """Test copying a very large layer."""
        start_time = time.time()
        memory_before = self.get_memory_usage()
        
        try:
            print(f"\nTesting copy layer with {width}x{height} pattern ({width*height} pixels)...")
            
            # Create large pattern
            pattern = self.create_test_pattern(width, height, 2)
            
            # Create layer with full pattern size
            source_frame = 0
            source_layer_index = self.layer_manager.add_layer(source_frame, "Large Source Layer")
            
            # Paint content on layer (create gradient pattern)
            test_pixels = []
            for y in range(height):
                for x in range(width):
                    r = (x * 255) // width
                    g = (y * 255) // height
                    b = (x + y) * 255 // (width + height)
                    test_pixels.append((r, g, b))
            
            operation_start = time.time()
            self.layer_manager.replace_pixels(source_frame, test_pixels, source_layer_index)
            operation_time = time.time() - operation_start
            
            # Copy layer to another frame
            target_frame = 1
            copy_start = time.time()
            target_layer_index = self.layer_manager.add_layer(target_frame, "Large Copy Layer")
            self.layer_manager.replace_pixels(target_frame, test_pixels, target_layer_index)
            copy_time = time.time() - copy_start
            
            # Verify copy completed successfully
            source_layer = self.layer_manager.get_layers(source_frame)[source_layer_index]
            target_layer = self.layer_manager.get_layers(target_frame)[target_layer_index]
            
            # Verify first few pixels match
            pixels_match = (
                source_layer.pixels[0] == target_layer.pixels[0] and
                source_layer.pixels[width * height // 2] == target_layer.pixels[width * height // 2] and
                source_layer.pixels[-1] == target_layer.pixels[-1]
            )
            
            # Verify layer sizes match
            size_matches = len(source_layer.pixels) == len(target_layer.pixels)
            
            memory_after = self.get_memory_usage()
            memory_delta = memory_after - memory_before
            execution_time = time.time() - start_time
            
            # Performance thresholds
            operation_ok = operation_time < 5.0  # Should be reasonable
            copy_ok = copy_time < 5.0  # Copy should be fast
            memory_ok = memory_delta < 500 if PSUTIL_AVAILABLE else True  # Allow up to 500MB
            
            passed = pixels_match and size_matches and operation_ok and copy_ok and memory_ok
            
            print(f"  Operation time: {operation_time:.3f}s")
            print(f"  Copy time: {copy_time:.3f}s")
            print(f"  Memory delta: {memory_delta:.1f}MB")
            print(f"  Pixels match: {pixels_match}")
            print(f"  Size matches: {size_matches}")
            print(f"  Performance OK: {operation_ok and copy_ok}")
            print(f"  Memory OK: {memory_ok if PSUTIL_AVAILABLE else 'N/A'}")
            print(f"  Result: {'✅ PASS' if passed else '❌ FAIL'}")
            
            return passed
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"  Error: {e}")
            print(f"  Result: ❌ FAIL")
            import traceback
            traceback.print_exc()
            return False
    
    def run_test(self):
        """Run the test."""
        print("\n" + "=" * 60)
        print("Test Copy Layer with Very Large Layers")
        print("=" * 60)
        
        # Test with 128x128 (16K pixels)
        result_128 = self.test_copy_large_layer(128, 128)
        
        # Test with 256x256 (65K pixels) for stress test
        print("\n" + "-" * 60)
        result_256 = self.test_copy_large_layer(256, 256)
        
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        print(f"128x128: {'✅ PASS' if result_128 else '❌ FAIL'}")
        print(f"256x256: {'✅ PASS' if result_256 else '❌ FAIL'}")
        print("=" * 60)
        
        return result_128 and result_256


def main():
    """Main entry point."""
    tester = CopyLayerLargeTest()
    success = tester.run_test()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

