#!/usr/bin/env python3
"""
Runner script for comprehensive feature testing

Usage:
    python run_all_features_comprehensive.py                    # Run all tests
    python run_all_features_comprehensive.py --phase 1          # Run specific phase
    python run_all_features_comprehensive.py --verbose           # Verbose output
"""

import sys
import os
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from PySide6.QtWidgets import QApplication
from tests.comprehensive.test_all_features_comprehensive import ComprehensiveFeatureTester
from ui.main_window import UploadBridgeMainWindow


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Run comprehensive feature tests')
    parser.add_argument('--phase', type=int, help='Run specific phase (1-14)')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    # Create QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    # Create main window
    main_window = UploadBridgeMainWindow()
    main_window.show()
    
    # Wait for initialization
    QApplication.processEvents()
    import time
    time.sleep(1)
    
    # Create tester
    tester = ComprehensiveFeatureTester(main_window)
    
    # Connect signals for progress reporting
    def on_test_started(test_name):
        if args.verbose:
            print(f"Starting: {test_name}")
    
    def on_test_completed(test_name, status):
        status_symbol = "✓" if status == "passed" else "✗"
        print(f"{status_symbol} {test_name}")
    
    def on_phase_started(phase, name):
        print(f"\n{'='*70}")
        print(f"Phase {phase}: {name}")
        print(f"{'='*70}")
    
    def on_phase_completed(phase, passed, failed):
        print(f"\nPhase {phase} completed: {passed} passed, {failed} failed")
    
    def on_progress_updated(current, total):
        if args.verbose:
            print(f"Progress: {current}/{total} ({current/total*100:.1f}%)")
    
    tester.test_started.connect(on_test_started)
    tester.test_completed.connect(on_test_completed)
    tester.phase_started.connect(on_phase_started)
    tester.phase_completed.connect(on_phase_completed)
    tester.progress_updated.connect(on_progress_updated)
    
    # Run tests
    if args.phase:
        # Run specific phase
        phase_methods = {
            1: tester.phase_1_basic_pattern_creation,
            2: tester.phase_2_drawing_tools,
            3: tester.phase_3_frame_management,
            4: tester.phase_4_layer_system,
            5: tester.phase_5_automation_actions,
            6: tester.phase_6_effects_library,
            7: tester.phase_7_canvas_features,
            8: tester.phase_8_timeline_features,
            9: tester.phase_9_import_export,
            10: tester.phase_10_options_settings,
            11: tester.phase_11_undo_redo,
            12: tester.phase_12_integration,
            13: tester.phase_13_stress_testing,
            14: tester.phase_14_error_handling,
        }
        if args.phase in phase_methods:
            phase_methods[args.phase]()
            tester._generate_report()
        else:
            print(f"Invalid phase: {args.phase}. Must be 1-14")
    else:
        # Run all tests
        tester.run_all_tests()
    
    # Cleanup
    main_window.close()
    app.quit()
    
    # Exit with appropriate code
    failed = sum(1 for r in tester.test_results if r.status == "failed")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()

