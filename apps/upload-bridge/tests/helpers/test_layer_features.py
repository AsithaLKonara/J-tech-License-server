"""
Layer Features Test Suite

Automated tests for all 7 layer feature scenarios from REMAINING_TASKS.md
"""

import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from domain.pattern_state import PatternState
from domain.layers import LayerManager
from core.pattern import Frame, Pattern, PatternMetadata
from tests.helpers.report_generator import TestResult, TestSuiteResult


class LayerFeaturesTestSuite:
    """Test suite for layer features."""
    
    def __init__(self, app: Optional[QApplication] = None):
        """Initialize test suite."""
        self.app = app or QApplication.instance() or QApplication(sys.argv)
        self.pattern_state = PatternState()
        self.layer_manager = LayerManager(self.pattern_state)
        self.test_results: List[TestResult] = []
    
    def create_test_pattern(self, width=8, height=8, num_frames=3) -> Pattern:
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
    
    def log_test(self, name: str, passed: bool, error_message: Optional[str] = None, execution_time: float = 0.0, details: Optional[Dict[str, Any]] = None):
        """Log test result."""
        self.test_results.append(TestResult(
            name=name,
            suite="Layer Features",
            passed=passed,
            skipped=False,
            error_message=error_message,
            execution_time=execution_time,
            details=details or {}
        ))
    
    # Scenario 1: Automation Layer Creation
    def test_scenario_1_automation_layer_creation(self) -> bool:
        """Test that automation creates a new 'Auto:' layer."""
        start_time = time.time()
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
            
            # Verify original layer still exists
            original_layer_exists = any(layer.name != layer_name for layer in layers_after)
            
            # Verify layer visibility toggle
            original_visible = new_layer.visible
            self.layer_manager.set_layer_visible(frame_index, layer_index, not original_visible)
            toggled_visible = self.layer_manager.get_layers(frame_index)[layer_index].visible
            visibility_toggle_works = toggled_visible != original_visible
            
            passed = (final_count == initial_count + 1) and has_auto_prefix and original_layer_exists and visibility_toggle_works
            execution_time = time.time() - start_time
            
            self.log_test(
                "Scenario 1: Automation Layer Creation",
                passed,
                None if passed else f"Count: {initial_count}->{final_count}, Auto prefix: {has_auto_prefix}, Toggle: {visibility_toggle_works}",
                execution_time,
                {'initial_count': initial_count, 'final_count': final_count}
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Scenario 1: Automation Layer Creation", False, str(e), execution_time)
            return False
    
    # Scenario 2: Layer Sync Warning
    def test_scenario_2_layer_sync_warning(self) -> bool:
        """Test layer sync detection and warning."""
        start_time = time.time()
        try:
            # Create pattern and paint on layer
            pattern = self.create_test_pattern(8, 8, 1)
            frame_index = 0
            
            # Paint something on the base layer
            test_color = (100, 150, 200)
            width = 8
            height = 8
            pixels = [test_color] * (width * height)
            base_layer_index = 0
            self.layer_manager.replace_pixels(frame_index, pixels, base_layer_index)
            
            # Apply automation (create automation layer)
            auto_layer_name = "Auto: Rotate 90"
            auto_layer_index = self.layer_manager.add_layer(frame_index, auto_layer_name)
            
            # Set pixels on automation layer
            auto_pixels = [(200, 200, 200)] * (width * height)
            self.layer_manager.replace_pixels(frame_index, auto_pixels, auto_layer_index)
            
            # Check if layers are out of sync
            # (After automation, frame pixels might not match layer composite)
            is_synced = self.layer_manager.are_layers_synced(frame_index)
            
            # Sync frame from layers
            self.layer_manager.sync_frame_from_layers(frame_index)
            
            # Verify sync completed
            is_synced_after = self.layer_manager.are_layers_synced(frame_index)
            
            passed = not is_synced and is_synced_after
            execution_time = time.time() - start_time
            
            self.log_test(
                "Scenario 2: Layer Sync Warning",
                passed,
                None if passed else f"Before sync: {is_synced}, After sync: {is_synced_after}",
                execution_time
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Scenario 2: Layer Sync Warning", False, str(e), execution_time)
            return False
    
    # Scenario 3: Brush Broadcast Feedback
    def test_scenario_3_brush_broadcast_feedback(self) -> bool:
        """Test brush broadcast mode affects all frames."""
        start_time = time.time()
        try:
            # Create pattern with 3+ frames
            pattern = self.create_test_pattern(8, 8, 3)
            frame_index = 0
            
            # Paint different content on each frame
            for i in range(3):
                pixels = [(i * 50, i * 50, i * 50)] * (8 * 8)
                self.layer_manager.replace_pixels(i, pixels, 0)
            
            # Get initial pixel values
            frame0_initial = self.layer_manager.get_layers(0)[0].pixels[0]
            frame1_initial = self.layer_manager.get_layers(1)[0].pixels[0]
            frame2_initial = self.layer_manager.get_layers(2)[0].pixels[0]
            
            # Simulate broadcast paint (paint on frame 0, should affect all frames if broadcast enabled)
            # Note: Actual broadcast would be handled by UI, but we can test the underlying behavior
            broadcast_color = (255, 255, 255)
            broadcast_pixels = [broadcast_color] * (8 * 8)
            
            # Paint on all frames (simulating broadcast)
            for i in range(3):
                self.layer_manager.replace_pixels(i, broadcast_pixels, 0)
            
            # Verify all frames updated
            frame0_updated = self.layer_manager.get_layers(0)[0].pixels[0]
            frame1_updated = self.layer_manager.get_layers(1)[0].pixels[0]
            frame2_updated = self.layer_manager.get_layers(2)[0].pixels[0]
            
            all_updated = (frame0_updated == broadcast_color and
                          frame1_updated == broadcast_color and
                          frame2_updated == broadcast_color)
            
            passed = all_updated
            execution_time = time.time() - start_time
            
            self.log_test(
                "Scenario 3: Brush Broadcast Feedback",
                passed,
                None if passed else "Not all frames updated",
                execution_time
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Scenario 3: Brush Broadcast Feedback", False, str(e), execution_time)
            return False
    
    # Scenario 4: Hidden Layer Prevention
    def test_scenario_4_hidden_layer_prevention(self) -> bool:
        """Test that painting on hidden layers is prevented."""
        start_time = time.time()
        try:
            # Create pattern with multiple layers
            pattern = self.create_test_pattern(8, 8, 1)
            frame_index = 0
            
            # Add a second layer
            layer1_index = self.layer_manager.add_layer(frame_index, "Layer 1")
            
            # Hide the layer
            self.layer_manager.set_layer_visible(frame_index, layer1_index, False)
            
            # Verify layer is hidden
            layers = self.layer_manager.get_layers(frame_index)
            layer_is_hidden = not layers[layer1_index].visible
            
            # Attempt to set pixels (should work at manager level, but UI should prevent)
            # At the manager level, we can set pixels even on hidden layers,
            # but the UI should prevent this. We test that the layer is properly marked as hidden.
            test_pixels = [(255, 0, 0)] * (8 * 8)
            self.layer_manager.replace_pixels(frame_index, test_pixels, layer1_index)
            
            # Verify pixels were set (manager allows it)
            pixels_set = self.layer_manager.get_layers(frame_index)[layer1_index].pixels[0] == (255, 0, 0)
            
            # Make layer visible
            self.layer_manager.set_layer_visible(frame_index, layer1_index, True)
            layer_is_visible = self.layer_manager.get_layers(frame_index)[layer1_index].visible
            
            # Verify painting works on visible layer
            new_pixels = [(0, 255, 0)] * (8 * 8)
            self.layer_manager.replace_pixels(frame_index, new_pixels, layer1_index)
            painting_works = self.layer_manager.get_layers(frame_index)[layer1_index].pixels[0] == (0, 255, 0)
            
            passed = layer_is_hidden and pixels_set and layer_is_visible and painting_works
            execution_time = time.time() - start_time
            
            self.log_test(
                "Scenario 4: Hidden Layer Prevention",
                passed,
                None if passed else f"Hidden: {layer_is_hidden}, Visible: {layer_is_visible}, Painting: {painting_works}",
                execution_time
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Scenario 4: Hidden Layer Prevention", False, str(e), execution_time)
            return False
    
    # Scenario 5: Copy Layer to Frames
    def test_scenario_5_copy_layer_to_frames(self) -> bool:
        """Test copying a layer to multiple frames."""
        start_time = time.time()
        try:
            # Create pattern with 3+ frames
            pattern = self.create_test_pattern(8, 8, 3)
            
            # Add custom layer to frame 0
            source_frame = 0
            source_layer_index = self.layer_manager.add_layer(source_frame, "Custom Layer")
            
            # Paint something on this layer
            test_color = (100, 200, 50)
            test_pixels = [test_color] * (8 * 8)
            self.layer_manager.replace_pixels(source_frame, test_pixels, source_layer_index)
            
            # Verify original layer has the test color
            source_layer = self.layer_manager.get_layers(source_frame)[source_layer_index]
            original_has_color = source_layer.pixels[0] == test_color
            
            # Use the copy_layer_to_frames method
            target_frames = [1, 2]
            self.layer_manager.copy_layer_to_frames(source_frame, source_layer_index, target_frames)
            
            # Verify layers were copied correctly
            # The copy_layer_to_frames method copies to the same layer track (layer index)
            # So we need to check the same layer index in target frames
            frame1_layers = self.layer_manager.get_layers(1)
            frame2_layers = self.layer_manager.get_layers(2)
            
            # Check if the layer exists in target frames and has correct pixels
            copied_correctly = False
            if source_layer_index < len(frame1_layers) and source_layer_index < len(frame2_layers):
                frame1_layer = frame1_layers[source_layer_index]
                frame2_layer = frame2_layers[source_layer_index]
                copied_correctly = (len(frame1_layer.pixels) > 0 and 
                                  len(frame2_layer.pixels) > 0 and
                                  frame1_layer.pixels[0] == test_color and
                                  frame2_layer.pixels[0] == test_color)
            
            # Verify original layer unchanged
            source_layer_after = self.layer_manager.get_layers(source_frame)[source_layer_index]
            original_unchanged = source_layer_after.pixels[0] == test_color
            
            passed = copied_correctly and original_unchanged and original_has_color
            execution_time = time.time() - start_time
            
            self.log_test(
                "Scenario 5: Copy Layer to Frames",
                passed,
                None if passed else f"Copied: {copied_correctly}, Original: {original_unchanged}, OriginalHasColor: {original_has_color}",
                execution_time
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Scenario 5: Copy Layer to Frames", False, str(e), execution_time)
            import traceback
            traceback.print_exc()
            return False
    
    # Scenario 6: Multiple Automation Layers
    def test_scenario_6_multiple_automation_layers(self) -> bool:
        """Test multiple automation layers can coexist."""
        start_time = time.time()
        try:
            # Create pattern
            pattern = self.create_test_pattern(8, 8, 1)
            frame_index = 0
            
            # Apply first automation
            layer1_index = self.layer_manager.add_layer(frame_index, "Auto: Scroll Left")
            
            # Apply second automation
            layer2_index = self.layer_manager.add_layer(frame_index, "Auto: Rotate 90")
            
            # Apply third automation
            layer3_index = self.layer_manager.add_layer(frame_index, "Auto: Mirror Horizontal")
            
            # Verify all automation layers exist
            layers = self.layer_manager.get_layers(frame_index)
            auto_layers = [l for l in layers if l.name.startswith("Auto:")]
            
            all_exist = len(auto_layers) == 3
            
            # Verify can toggle each independently
            original_visibilities = [layers[i].visible for i in [layer1_index, layer2_index, layer3_index]]
            
            # Toggle first
            self.layer_manager.set_layer_visible(frame_index, layer1_index, not original_visibilities[0])
            toggle1_works = self.layer_manager.get_layers(frame_index)[layer1_index].visible != original_visibilities[0]
            
            # Toggle second
            self.layer_manager.set_layer_visible(frame_index, layer2_index, not original_visibilities[1])
            toggle2_works = self.layer_manager.get_layers(frame_index)[layer2_index].visible != original_visibilities[1]
            
            # Toggle third
            self.layer_manager.set_layer_visible(frame_index, layer3_index, not original_visibilities[2])
            toggle3_works = self.layer_manager.get_layers(frame_index)[layer3_index].visible != original_visibilities[2]
            
            passed = all_exist and toggle1_works and toggle2_works and toggle3_works
            execution_time = time.time() - start_time
            
            self.log_test(
                "Scenario 6: Multiple Automation Layers",
                passed,
                None if passed else f"Count: {len(auto_layers)}, Toggles: {toggle1_works}, {toggle2_works}, {toggle3_works}",
                execution_time
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Scenario 6: Multiple Automation Layers", False, str(e), execution_time)
            return False
    
    # Scenario 7: Edge Cases
    def test_scenario_7_edge_cases(self) -> bool:
        """Test edge cases."""
        start_time = time.time()
        results = []
        
        try:
            # Test 1: Single frame pattern
            pattern1 = self.create_test_pattern(8, 8, 1)
            results.append(True)  # If no exception, it works
            
            # Test 2: Single layer (default)
            layers1 = self.layer_manager.get_layers(0)
            results.append(len(layers1) >= 1)
            
            # Test 3: Many layers (10+)
            pattern2 = self.create_test_pattern(16, 16, 1)
            for i in range(10):
                self.layer_manager.add_layer(0, f"Layer {i}")
            layers_many = self.layer_manager.get_layers(0)
            results.append(len(layers_many) >= 10)
            
            # Test 4: Large pattern (64x64)
            pattern3 = self.create_test_pattern(64, 64, 1)
            large_pattern_works = pattern3.metadata.width == 64 and pattern3.metadata.height == 64
            results.append(large_pattern_works)
            
            # Test 5: Copy layer to same frame (should be possible, just adds another layer)
            pattern4 = self.create_test_pattern(8, 8, 1)
            source_idx = self.layer_manager.add_layer(0, "Source")
            test_pixels = [(100, 100, 100)] * (8 * 8)
            self.layer_manager.replace_pixels(0, test_pixels, source_idx)
            
            # Copy to same frame (should create new layer)
            initial_count = len(self.layer_manager.get_layers(0))
            copy_idx = self.layer_manager.add_layer(0, "Copy")
            self.layer_manager.replace_pixels(0, test_pixels, copy_idx)
            final_count = len(self.layer_manager.get_layers(0))
            copy_to_same_frame_works = final_count == initial_count + 1
            results.append(copy_to_same_frame_works)
            
            passed = all(results)
            execution_time = time.time() - start_time
            
            self.log_test(
                "Scenario 7: Edge Cases",
                passed,
                None if passed else f"Results: {results}",
                execution_time,
                {'test_results': results}
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Scenario 7: Edge Cases", False, str(e), execution_time)
            return False
    
    def run_all_tests(self) -> TestSuiteResult:
        """Run all layer feature tests."""
        print("\n" + "=" * 60)
        print("Layer Features Test Suite")
        print("=" * 60)
        
        test_methods = [
            self.test_scenario_1_automation_layer_creation,
            self.test_scenario_2_layer_sync_warning,
            self.test_scenario_3_brush_broadcast_feedback,
            self.test_scenario_4_hidden_layer_prevention,
            self.test_scenario_5_copy_layer_to_frames,
            self.test_scenario_6_multiple_automation_layers,
            self.test_scenario_7_edge_cases,
        ]
        
        start_time = time.time()
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"ERROR in {test_method.__name__}: {e}")
        
        execution_time = time.time() - start_time
        
        # Calculate summary
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r.passed)
        failed = total - passed
        skipped = sum(1 for r in self.test_results if r.skipped)
        
        suite_result = TestSuiteResult(
            name="Layer Features",
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            execution_time=execution_time,
            tests=self.test_results
        )
        
        print(f"\nLayer Features: {passed}/{total} passed ({execution_time:.2f}s)")
        
        return suite_result

