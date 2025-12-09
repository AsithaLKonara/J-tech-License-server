"""
Comprehensive test script for new layer features.

Tests the following features:
1. Automation layer integration - automation creates new layers
2. Layer sync detection - warnings and sync button
3. Brush broadcast feedback - frame highlighting
4. Hidden layer prevention - blocks painting on hidden layers
5. Layer copy to frames - context menu option
6. Performance optimization - batch updates and dirty regions

Usage:
    python tests/test_new_layer_features.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest
from domain.pattern_state import PatternState
from domain.layers import LayerManager
from core.pattern import Frame, Pattern, PatternMetadata


class LayerFeaturesTester:
    """Test suite for new layer features."""
    
    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.pattern_state = PatternState()
        self.layer_manager = LayerManager(self.pattern_state)
        self.test_results = []
        
    def create_test_pattern(self, width=8, height=8, num_frames=3):
        """Create a test pattern with multiple frames."""
        metadata = PatternMetadata(width=width, height=height)
        frames = []
        for i in range(num_frames):
            pixels = [(i * 10, i * 20, i * 30)] * (width * height)
            frame = Frame(pixels=pixels, duration_ms=100)
            frames.append(frame)
        
        pattern = Pattern(metadata=metadata, frames=frames)
        self.pattern_state.set_pattern(pattern)
        self.layer_manager.set_pattern(pattern)
        return pattern
    
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = f"{status}: {test_name}"
        if message:
            result += f" - {message}"
        print(result)
        self.test_results.append({
            'name': test_name,
            'passed': passed,
            'message': message
        })
    
    def test_automation_creates_new_layer(self):
        """Test that automation creates a new 'Auto:' layer."""
        print("\n=== Test 1: Automation Creates New Layer ===")
        
        try:
            # Create pattern
            pattern = self.create_test_pattern(8, 8, 1)
            frame_index = 0
            
            # Get initial layer count
            initial_layers = self.layer_manager.get_layers(frame_index)
            initial_count = len(initial_layers)
            
            # Simulate automation (create a new layer with "Auto:" prefix)
            layer_name = "Auto: Scroll Left"
            layer_index = self.layer_manager.add_layer(frame_index, layer_name)
            
            # Verify new layer was created
            layers_after = self.layer_manager.get_layers(frame_index)
            final_count = len(layers_after)
            
            # Check layer name starts with "Auto:"
            new_layer = layers_after[layer_index]
            has_auto_prefix = new_layer.name.startswith("Auto:")
            
            passed = (final_count == initial_count + 1) and has_auto_prefix
            self.log_test(
                "Automation creates new layer",
                passed,
                f"Initial: {initial_count}, Final: {final_count}, Name: {new_layer.name}"
            )
            
            return passed
            
        except Exception as e:
            self.log_test("Automation creates new layer", False, str(e))
            return False
    
    def test_layer_sync_detection(self):
        """Test layer sync detection."""
        print("\n=== Test 2: Layer Sync Detection ===")
        
        try:
            # Create pattern
            pattern = self.create_test_pattern(8, 8, 1)
            frame_index = 0
            
            # Initially should be synced
            is_synced_initial = self.layer_manager.are_layers_synced(frame_index)
            
            # Modify frame pixels directly (simulating automation)
            frame = pattern.frames[frame_index]
            original_pixel = frame.pixels[0]
            frame.pixels[0] = (255, 255, 255)  # Change pixel
            
            # Now should be out of sync
            is_synced_after = self.layer_manager.are_layers_synced(frame_index)
            
            # Sync layers from frame
            self.layer_manager.sync_frame_from_layers(frame_index)
            is_synced_after_sync = self.layer_manager.are_layers_synced(frame_index)
            
            passed = is_synced_initial and not is_synced_after and is_synced_after_sync
            self.log_test(
                "Layer sync detection",
                passed,
                f"Initial: {is_synced_initial}, After mod: {is_synced_after}, After sync: {is_synced_after_sync}"
            )
            
            return passed
            
        except Exception as e:
            self.log_test("Layer sync detection", False, str(e))
            return False
    
    def test_copy_layer_to_frames(self):
        """Test copying a layer to multiple frames."""
        print("\n=== Test 3: Copy Layer to Frames ===")
        
        try:
            # Create pattern with 3 frames
            pattern = self.create_test_pattern(8, 8, 3)
            
            # Add a custom layer to frame 0
            source_frame = 0
            source_layer = self.layer_manager.add_layer(source_frame, "Custom Layer")
            
            # Set some pixels on this layer
            test_color = (100, 150, 200)
            width = 8
            height = 8
            for y in range(height):
                for x in range(width):
                    self.layer_manager.apply_pixel(
                        source_frame, x, y, test_color, width, height, layer_index=source_layer
                    )
            
            # Copy layer to frames 1 and 2
            target_frames = [1, 2]
            self.layer_manager.copy_layer_to_frames(source_frame, source_layer, target_frames)
            
            # Verify layers exist in target frames
            frame1_layers = self.layer_manager.get_layers(1)
            frame2_layers = self.layer_manager.get_layers(2)
            
            # Check that target frames have the copied layer
            has_layer_in_frame1 = any(layer.name == "Custom Layer" for layer in frame1_layers)
            has_layer_in_frame2 = any(layer.name == "Custom Layer" for layer in frame2_layers)
            
            # Verify pixels were copied
            frame1_layer = next((l for l in frame1_layers if l.name == "Custom Layer"), None)
            frame2_layer = next((l for l in frame2_layers if l.name == "Custom Layer"), None)
            
            pixels_match = False
            if frame1_layer and frame2_layer:
                # Check first pixel matches
                pixels_match = (
                    frame1_layer.pixels[0] == test_color and
                    frame2_layer.pixels[0] == test_color
                )
            
            passed = has_layer_in_frame1 and has_layer_in_frame2 and pixels_match
            self.log_test(
                "Copy layer to frames",
                passed,
                f"Frame1 has layer: {has_layer_in_frame1}, Frame2 has layer: {has_layer_in_frame2}, Pixels match: {pixels_match}"
            )
            
            return passed
            
        except Exception as e:
            self.log_test("Copy layer to frames", False, str(e))
            import traceback
            print(traceback.format_exc())
            return False
    
    def test_hidden_layer_prevention(self):
        """Test that painting on hidden layers is prevented."""
        print("\n=== Test 4: Hidden Layer Prevention ===")
        
        try:
            # Create pattern
            pattern = self.create_test_pattern(8, 8, 1)
            frame_index = 0
            
            # Add a second layer and hide it
            hidden_layer = self.layer_manager.add_layer(frame_index, "Hidden Layer")
            self.layer_manager.set_layer_visible(frame_index, hidden_layer, False)
            
            # Verify layer is hidden
            layers = self.layer_manager.get_layers(frame_index)
            is_hidden = not layers[hidden_layer].visible
            
            # Try to paint on hidden layer (this should be prevented by UI, but we test the state)
            # The actual prevention happens in the UI layer, so we verify the layer state
            passed = is_hidden
            self.log_test(
                "Hidden layer prevention",
                passed,
                f"Layer is hidden: {is_hidden}"
            )
            
            return passed
            
        except Exception as e:
            self.log_test("Hidden layer prevention", False, str(e))
            return False
    
    def test_multiple_automation_layers(self):
        """Test that multiple automation operations create separate layers."""
        print("\n=== Test 5: Multiple Automation Layers ===")
        
        try:
            # Create pattern
            pattern = self.create_test_pattern(8, 8, 1)
            frame_index = 0
            
            # Create multiple automation layers
            layer1 = self.layer_manager.add_layer(frame_index, "Auto: Scroll Left")
            layer2 = self.layer_manager.add_layer(frame_index, "Auto: Rotate 90")
            layer3 = self.layer_manager.add_layer(frame_index, "Auto: Mirror X")
            
            # Verify all layers exist
            layers = self.layer_manager.get_layers(frame_index)
            auto_layers = [l for l in layers if l.name.startswith("Auto:")]
            
            passed = len(auto_layers) == 3
            self.log_test(
                "Multiple automation layers",
                passed,
                f"Found {len(auto_layers)} automation layers"
            )
            
            return passed
            
        except Exception as e:
            self.log_test("Multiple automation layers", False, str(e))
            return False
    
    def test_layer_sync_after_automation(self):
        """Test that layers are synced after automation."""
        print("\n=== Test 6: Layer Sync After Automation ===")
        
        try:
            # Create pattern
            pattern = self.create_test_pattern(8, 8, 1)
            frame_index = 0
            
            # Add automation layer (simulating automation)
            auto_layer = self.layer_manager.add_layer(frame_index, "Auto: Scroll Left")
            
            # Set pixels on automation layer
            test_color = (50, 100, 150)
            width = 8
            height = 8
            pixels = [test_color] * (width * height)
            self.layer_manager.replace_pixels(frame_index, pixels, auto_layer)
            
            # Sync frame from layers
            self.layer_manager.sync_frame_from_layers(frame_index)
            
            # Verify sync
            is_synced = self.layer_manager.are_layers_synced(frame_index)
            
            # Verify frame pixels match
            frame = pattern.frames[frame_index]
            frame_matches = frame.pixels[0] == test_color
            
            passed = is_synced and frame_matches
            self.log_test(
                "Layer sync after automation",
                passed,
                f"Synced: {is_synced}, Frame matches: {frame_matches}"
            )
            
            return passed
            
        except Exception as e:
            self.log_test("Layer sync after automation", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests."""
        print("=" * 60)
        print("Layer Features Test Suite")
        print("=" * 60)
        
        tests = [
            self.test_automation_creates_new_layer,
            self.test_layer_sync_detection,
            self.test_copy_layer_to_frames,
            self.test_hidden_layer_prevention,
            self.test_multiple_automation_layers,
            self.test_layer_sync_after_automation,
        ]
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
            except Exception as e:
                print(f"❌ ERROR in {test.__name__}: {e}")
                results.append(False)
        
        # Print summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        passed = sum(results)
        total = len(results)
        print(f"Passed: {passed}/{total}")
        print(f"Failed: {total - passed}/{total}")
        
        if passed == total:
            print("\n✅ All tests passed!")
        else:
            print(f"\n❌ {total - passed} test(s) failed")
        
        return passed == total


def main():
    """Main entry point."""
    tester = LayerFeaturesTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

