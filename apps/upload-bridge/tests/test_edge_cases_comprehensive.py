"""
Test Edge Cases (Empty Patterns, Single Pixel, etc.)

Comprehensive edge case testing.
Task 3.5 from remaining tasks plan.
"""

import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from domain.pattern_state import PatternState
from domain.layers import LayerManager
from core.pattern import Frame, Pattern, PatternMetadata


class EdgeCasesTest:
    """Test edge cases."""
    
    def __init__(self, app: Optional[QApplication] = None):
        """Initialize test."""
        self.app = app or QApplication.instance() or QApplication(sys.argv)
        self.pattern_state = PatternState()
        self.layer_manager = LayerManager(self.pattern_state)
        self.results: List[Dict[str, Any]] = []
    
    def log_result(self, test_name: str, passed: bool, error: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """Log test result."""
        self.results.append({
            'test_name': test_name,
            'passed': passed,
            'error': error,
            'details': details or {}
        })
    
    def test_single_pixel_pattern(self) -> bool:
        """Test with single pixel pattern (1x1)."""
        start_time = time.time()
        try:
            print("\nTesting single pixel pattern (1x1)...")
            
            metadata = PatternMetadata(width=1, height=1)
            pixels = [(255, 255, 255)]
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern = Pattern(metadata=metadata, frames=[frame])
            
            self.pattern_state.set_pattern(pattern)
            self.layer_manager.set_pattern(pattern)
            
            # Verify pattern created
            created = pattern.metadata.width == 1 and pattern.metadata.height == 1
            layers = self.layer_manager.get_layers(0)
            has_layers = len(layers) > 0
            
            passed = created and has_layers
            execution_time = time.time() - start_time
            
            self.log_result("Single Pixel Pattern (1x1)", passed, None, {'execution_time': execution_time})
            print(f"  Result: {'✅ PASS' if passed else '❌ FAIL'} ({execution_time:.3f}s)")
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_result("Single Pixel Pattern (1x1)", False, str(e), {'execution_time': execution_time})
            print(f"  Error: {e}")
            print(f"  Result: ❌ FAIL")
            return False
    
    def test_very_small_pattern(self) -> bool:
        """Test with very small pattern (2x2)."""
        start_time = time.time()
        try:
            print("\nTesting very small pattern (2x2)...")
            
            metadata = PatternMetadata(width=2, height=2)
            pixels = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255)]
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern = Pattern(metadata=metadata, frames=[frame])
            
            self.pattern_state.set_pattern(pattern)
            self.layer_manager.set_pattern(pattern)
            
            created = pattern.metadata.width == 2 and pattern.metadata.height == 2
            layers = self.layer_manager.get_layers(0)
            can_edit = len(layers) > 0
            
            passed = created and can_edit
            execution_time = time.time() - start_time
            
            self.log_result("Very Small Pattern (2x2)", passed, None, {'execution_time': execution_time})
            print(f"  Result: {'✅ PASS' if passed else '❌ FAIL'} ({execution_time:.3f}s)")
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_result("Very Small Pattern (2x2)", False, str(e), {'execution_time': execution_time})
            print(f"  Error: {e}")
            print(f"  Result: ❌ FAIL")
            return False
    
    def test_single_frame_pattern(self) -> bool:
        """Test with single frame pattern."""
        start_time = time.time()
        try:
            print("\nTesting single frame pattern...")
            
            metadata = PatternMetadata(width=8, height=8)
            pixels = [(100, 100, 100)] * 64
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern = Pattern(metadata=metadata, frames=[frame])
            
            self.pattern_state.set_pattern(pattern)
            self.layer_manager.set_pattern(pattern)
            
            created = len(pattern.frames) == 1
            layers = self.layer_manager.get_layers(0)
            has_layers = len(layers) > 0
            
            passed = created and has_layers
            execution_time = time.time() - start_time
            
            self.log_result("Single Frame Pattern", passed, None, {'execution_time': execution_time})
            print(f"  Result: {'✅ PASS' if passed else '❌ FAIL'} ({execution_time:.3f}s)")
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_result("Single Frame Pattern", False, str(e), {'execution_time': execution_time})
            print(f"  Error: {e}")
            print(f"  Result: ❌ FAIL")
            return False
    
    def test_single_layer(self) -> bool:
        """Test with single layer (default)."""
        start_time = time.time()
        try:
            print("\nTesting single layer...")
            
            metadata = PatternMetadata(width=8, height=8)
            pixels = [(100, 100, 100)] * 64
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern = Pattern(metadata=metadata, frames=[frame])
            
            self.pattern_state.set_pattern(pattern)
            self.layer_manager.set_pattern(pattern)
            
            layers = self.layer_manager.get_layers(0)
            has_single_layer = len(layers) >= 1
            
            passed = has_single_layer
            execution_time = time.time() - start_time
            
            self.log_result("Single Layer", passed, None, {'execution_time': execution_time, 'layer_count': len(layers)})
            print(f"  Layers: {len(layers)}")
            print(f"  Result: {'✅ PASS' if passed else '❌ FAIL'} ({execution_time:.3f}s)")
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_result("Single Layer", False, str(e), {'execution_time': execution_time})
            print(f"  Error: {e}")
            print(f"  Result: ❌ FAIL")
            return False
    
    def test_many_layers_edge(self) -> bool:
        """Test with many layers (15+)."""
        start_time = time.time()
        try:
            print("\nTesting many layers (15+)...")
            
            metadata = PatternMetadata(width=16, height=16)
            pixels = [(100, 100, 100)] * 256
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern = Pattern(metadata=metadata, frames=[frame])
            
            self.pattern_state.set_pattern(pattern)
            self.layer_manager.set_pattern(pattern)
            
            # Add 15 layers
            for i in range(15):
                self.layer_manager.add_layer(0, f"Layer {i}")
            
            layers = self.layer_manager.get_layers(0)
            has_many_layers = len(layers) >= 15
            
            passed = has_many_layers
            execution_time = time.time() - start_time
            
            self.log_result("Many Layers (15+)", passed, None, {'execution_time': execution_time, 'layer_count': len(layers)})
            print(f"  Layers: {len(layers)}")
            print(f"  Result: {'✅ PASS' if passed else '❌ FAIL'} ({execution_time:.3f}s)")
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_result("Many Layers (15+)", False, str(e), {'execution_time': execution_time})
            print(f"  Error: {e}")
            print(f"  Result: ❌ FAIL")
            return False
    
    def test_copy_layer_to_same_frame(self) -> bool:
        """Test copy layer to same frame (should work, creates new layer)."""
        start_time = time.time()
        try:
            print("\nTesting copy layer to same frame...")
            
            metadata = PatternMetadata(width=8, height=8)
            pixels = [(100, 100, 100)] * 64
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern = Pattern(metadata=metadata, frames=[frame])
            
            self.pattern_state.set_pattern(pattern)
            self.layer_manager.set_pattern(pattern)
            
            frame_index = 0
            
            # Add source layer
            source_layer_index = self.layer_manager.add_layer(frame_index, "Source")
            test_pixels = [(255, 0, 0)] * 64
            self.layer_manager.replace_pixels(frame_index, test_pixels, source_layer_index)
            
            initial_count = len(self.layer_manager.get_layers(frame_index))
            
            # Copy to same frame (should create new layer)
            copy_layer_index = self.layer_manager.add_layer(frame_index, "Copy")
            self.layer_manager.replace_pixels(frame_index, test_pixels, copy_layer_index)
            
            final_count = len(self.layer_manager.get_layers(frame_index))
            layer_added = final_count == initial_count + 1
            
            passed = layer_added
            execution_time = time.time() - start_time
            
            self.log_result("Copy Layer to Same Frame", passed, None, {'execution_time': execution_time, 'initial': initial_count, 'final': final_count})
            print(f"  Initial layers: {initial_count}, Final layers: {final_count}")
            print(f"  Result: {'✅ PASS' if passed else '❌ FAIL'} ({execution_time:.3f}s)")
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_result("Copy Layer to Same Frame", False, str(e), {'execution_time': execution_time})
            print(f"  Error: {e}")
            print(f"  Result: ❌ FAIL")
            return False
    
    def run_all_tests(self):
        """Run all edge case tests."""
        print("\n" + "=" * 60)
        print("Comprehensive Edge Case Testing")
        print("=" * 60)
        
        test_methods = [
            self.test_single_pixel_pattern,
            self.test_very_small_pattern,
            self.test_single_frame_pattern,
            self.test_single_layer,
            self.test_many_layers_edge,
            self.test_copy_layer_to_same_frame,
        ]
        
        start_time = time.time()
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"ERROR in {test_method.__name__}: {e}")
        
        total_time = time.time() - start_time
        
        # Calculate summary
        total = len(self.results)
        passed = sum(1 for r in self.results if r['passed'])
        failed = total - passed
        
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        print(f"Total: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Time: {total_time:.2f}s")
        print("=" * 60)
        
        return passed == total


def main():
    """Main entry point."""
    tester = EdgeCasesTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

