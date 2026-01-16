"""
Integration Test Suite

Cross-feature integration tests.
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


class IntegrationTestSuite:
    """Test suite for integration tests."""
    
    def __init__(self, app: Optional[QApplication] = None):
        """Initialize test suite."""
        self.app = app or QApplication.instance() or QApplication(sys.argv)
        self.pattern_state = PatternState()
        self.layer_manager = LayerManager(self.pattern_state)
        self.test_results: List[TestResult] = []
    
    def create_test_pattern(self, width=8, height=8, num_frames=3) -> Pattern:
        """Create a test pattern."""
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
            suite="Integration",
            passed=passed,
            skipped=False,
            error_message=error_message,
            execution_time=execution_time,
            details=details or {}
        ))
    
    def test_automation_layer_integration(self) -> bool:
        """Test automation + layer integration."""
        start_time = time.time()
        try:
            pattern = self.create_test_pattern(8, 8, 1)
            frame_index = 0
            
            # Apply automation (create layer)
            auto_layer_index = self.layer_manager.add_layer(frame_index, "Auto: Scroll Left")
            
            # Verify layer created
            layers = self.layer_manager.get_layers(frame_index)
            auto_layer_exists = any(layer.name.startswith("Auto:") for layer in layers)
            
            # Check sync status
            is_synced = self.layer_manager.are_layers_synced(frame_index)
            
            # Sync
            self.layer_manager.sync_frame_from_layers(frame_index)
            is_synced_after = self.layer_manager.are_layers_synced(frame_index)
            
            passed = auto_layer_exists and is_synced_after
            execution_time = time.time() - start_time
            
            self.log_test(
                "Automation + Layer Integration",
                passed,
                None if passed else f"Auto layer: {auto_layer_exists}, Synced: {is_synced_after}",
                execution_time
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Automation + Layer Integration", False, str(e), execution_time)
            return False
    
    def test_broadcast_mode_multiple_frames(self) -> bool:
        """Test broadcast mode + multiple frames."""
        start_time = time.time()
        try:
            pattern = self.create_test_pattern(8, 8, 3)
            
            # Paint on all frames (simulating broadcast)
            broadcast_color = (255, 255, 255)
            broadcast_pixels = [broadcast_color] * (8 * 8)
            
            for i in range(3):
                self.layer_manager.replace_pixels(i, broadcast_pixels, 0)
            
            # Verify all frames updated
            all_updated = all(
                self.layer_manager.get_layers(i)[0].pixels[0] == broadcast_color
                for i in range(3)
            )
            
            passed = all_updated
            execution_time = time.time() - start_time
            
            self.log_test(
                "Broadcast Mode + Multiple Frames",
                passed,
                None if passed else "Not all frames updated",
                execution_time
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Broadcast Mode + Multiple Frames", False, str(e), execution_time)
            return False
    
    def test_copy_layer_undo_redo(self) -> bool:
        """Test copy layer + undo/redo integration."""
        start_time = time.time()
        try:
            pattern = self.create_test_pattern(8, 8, 2)
            
            # Add layer to frame 0
            source_layer_index = self.layer_manager.add_layer(0, "Source")
            test_pixels = [(100, 100, 100)] * (8 * 8)
            self.layer_manager.replace_pixels(0, test_pixels, source_layer_index)
            
            # Copy to frame 1
            target_layer_index = self.layer_manager.add_layer(1, "Copy")
            self.layer_manager.replace_pixels(1, test_pixels, target_layer_index)
            
            # Verify copy worked
            copied = self.layer_manager.get_layers(1)[target_layer_index].pixels[0] == test_pixels[0]
            
            passed = copied
            execution_time = time.time() - start_time
            
            self.log_test(
                "Copy Layer + Undo/Redo",
                passed,
                None if passed else "Copy failed",
                execution_time
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Copy Layer + Undo/Redo", False, str(e), execution_time)
            return False
    
    def test_hidden_layer_effects(self) -> bool:
        """Test hidden layer + effects integration."""
        start_time = time.time()
        try:
            pattern = self.create_test_pattern(8, 8, 1)
            frame_index = 0
            
            # Create layer and hide it
            layer_index = self.layer_manager.add_layer(frame_index, "Hidden Layer")
            self.layer_manager.set_layer_visible(frame_index, layer_index, False)
            
            # Verify layer is hidden
            layer_is_hidden = not self.layer_manager.get_layers(frame_index)[layer_index].visible
            
            # Make visible
            self.layer_manager.set_layer_visible(frame_index, layer_index, True)
            layer_is_visible = self.layer_manager.get_layers(frame_index)[layer_index].visible
            
            passed = layer_is_hidden and layer_is_visible
            execution_time = time.time() - start_time
            
            self.log_test(
                "Hidden Layer + Effects",
                passed,
                None if passed else f"Hidden: {layer_is_hidden}, Visible: {layer_is_visible}",
                execution_time
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Hidden Layer + Effects", False, str(e), execution_time)
            return False
    
    def run_all_tests(self) -> TestSuiteResult:
        """Run all integration tests."""
        print("\n" + "=" * 60)
        print("Integration Test Suite")
        print("=" * 60)
        
        test_methods = [
            self.test_automation_layer_integration,
            self.test_broadcast_mode_multiple_frames,
            self.test_copy_layer_undo_redo,
            self.test_hidden_layer_effects,
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
            name="Integration",
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            execution_time=execution_time,
            tests=self.test_results
        )
        
        print(f"\nIntegration: {passed}/{total} passed ({execution_time:.2f}s)")
        
        return suite_result

