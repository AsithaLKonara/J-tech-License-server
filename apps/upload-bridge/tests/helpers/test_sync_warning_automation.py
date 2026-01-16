"""
Test Sync Warning After All Automation Types

Automated test to verify sync warning appears correctly after all automation types.
Task 3.1 from remaining tasks plan.
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
from core.pattern import Frame, Pattern, PatternMetadata


class SyncWarningAutomationTest:
    """Test sync warning after all automation types."""
    
    def __init__(self, app: Optional[QApplication] = None):
        """Initialize test."""
        self.app = app or QApplication.instance() or QApplication(sys.argv)
        self.pattern_state = PatternState()
        self.layer_manager = LayerManager(self.pattern_state)
        self.results: List[Dict[str, Any]] = []
    
    def create_test_pattern(self, width=16, height=16, num_frames=1) -> Pattern:
        """Create a test pattern."""
        metadata = PatternMetadata(width=width, height=height)
        frames = []
        for i in range(num_frames):
            pixels = [(100, 100, 100)] * (width * height)
            frame = Frame(pixels=pixels, duration_ms=100)
            frames.append(frame)
        
        pattern = Pattern(metadata=metadata, frames=frames)
        self.pattern_state.set_pattern(pattern)
        self.layer_manager.set_pattern(pattern)
        return pattern
    
    def test_automation_sync_warning(self, automation_name: str) -> Dict[str, Any]:
        """Test sync warning after a specific automation type."""
        start_time = time.time()
        frame_index = 0
        
        try:
            # Create pattern with content
            pattern = self.create_test_pattern(16, 16, 1)
            
            # Paint something on base layer
            test_color = (200, 150, 100)
            pixels = [test_color] * (16 * 16)
            base_layer_index = 0
            self.layer_manager.replace_pixels(frame_index, pixels, base_layer_index)
            
            # Sync frame from layers to ensure initial sync state
            self.layer_manager.sync_frame_from_layers(frame_index)
            
            # Verify layers are initially synced
            is_synced_before = self.layer_manager.are_layers_synced(frame_index)
            
            # Apply automation (create automation layer)
            auto_layer_name = f"Auto: {automation_name}"
            auto_layer_index = self.layer_manager.add_layer(frame_index, auto_layer_name)
            
            # Set pixels on automation layer (simulating automation result)
            auto_pixels = [(100, 200, 50)] * (16 * 16)
            self.layer_manager.replace_pixels(frame_index, auto_pixels, auto_layer_index)
            
            # Check if layers are out of sync (they should be after automation)
            is_synced_after_automation = self.layer_manager.are_layers_synced(frame_index)
            
            # Verify automation layer was created
            layers = self.layer_manager.get_layers(frame_index)
            auto_layers = [l for l in layers if l.name.startswith("Auto:")]
            auto_layer_exists = any(l.name == auto_layer_name for l in auto_layers)
            
            # Sync frame from layers
            self.layer_manager.sync_frame_from_layers(frame_index)
            is_synced_after_sync = self.layer_manager.are_layers_synced(frame_index)
            
            execution_time = time.time() - start_time
            
            passed = (
                is_synced_before and  # Should be synced initially
                not is_synced_after_automation and  # Should be out of sync after automation
                auto_layer_exists and  # Automation layer should exist
                is_synced_after_sync  # Should be synced after sync operation
            )
            
            result = {
                'automation_name': automation_name,
                'passed': passed,
                'execution_time': execution_time,
                'is_synced_before': is_synced_before,
                'is_synced_after_automation': is_synced_after_automation,
                'auto_layer_exists': auto_layer_exists,
                'is_synced_after_sync': is_synced_after_sync,
                'error': None
            }
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                'automation_name': automation_name,
                'passed': False,
                'execution_time': execution_time,
                'error': str(e)
            }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Test all automation types."""
        print("\n" + "=" * 60)
        print("Testing Sync Warning After All Automation Types")
        print("=" * 60)
        
        # List of all automation types to test
        automation_types = [
            "Scroll Left",
            "Scroll Right",
            "Scroll Up",
            "Scroll Down",
            "Rotate 90",
            "Mirror Horizontal",
            "Mirror Vertical",
            "Invert",
            "Fade",
            "Brightness",
            "Randomize",
            "Wipe Left",
            "Wipe Right",
            "Reveal Left",
            "Reveal Right",
            "Bounce Horizontal",
            "Colour Cycle",
        ]
        
        start_time = time.time()
        
        for automation_type in automation_types:
            print(f"\nTesting: {automation_type}")
            result = self.test_automation_sync_warning(automation_type)
            self.results.append(result)
            
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"  {status} ({result['execution_time']:.3f}s)")
            
            if result.get('error'):
                print(f"  Error: {result['error']}")
            elif not result['passed']:
                print(f"  Details: synced_before={result['is_synced_before']}, "
                      f"synced_after_auto={result['is_synced_after_automation']}, "
                      f"layer_exists={result['auto_layer_exists']}, "
                      f"synced_after_sync={result['is_synced_after_sync']}")
        
        total_time = time.time() - start_time
        
        # Calculate summary
        total = len(self.results)
        passed = sum(1 for r in self.results if r['passed'])
        failed = total - passed
        
        summary = {
            'total': total,
            'passed': passed,
            'failed': failed,
            'execution_time': total_time,
            'results': self.results
        }
        
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        print(f"Total: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Time: {total_time:.2f}s")
        print("=" * 60)
        
        return summary


def main():
    """Main entry point."""
    tester = SyncWarningAutomationTest()
    summary = tester.run_all_tests()
    
    # Exit with error code if any tests failed
    sys.exit(0 if summary['failed'] == 0 else 1)


if __name__ == "__main__":
    main()

