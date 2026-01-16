#!/usr/bin/env python3
"""
Comprehensive Automated Test Suite

Single script that runs all remaining tasks tests including:
- Layer features (7 scenarios)
- License system
- Integration tests
- Performance tests
- GUI interactions

Usage:
    python tests/test_complete_system_automated.py
    python tests/test_complete_system_automated.py --no-gui
    python tests/test_complete_system_automated.py --layer-only
    python tests/test_complete_system_automated.py --license-only
"""

import sys
import os
import argparse
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set offscreen platform for GUI tests (prevents windows from appearing)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from tests.helpers.test_layer_features import LayerFeaturesTestSuite
from tests.helpers.test_license_system import LicenseSystemTestSuite
from tests.helpers.test_integration import IntegrationTestSuite
from tests.helpers.test_performance import PerformanceTestSuite
from tests.helpers.test_gui_interactions import GUITestSuite
from tests.helpers.report_generator import ReportGenerator


class CompleteSystemTester:
    """Main test orchestrator."""
    
    def __init__(self, options: argparse.Namespace):
        """Initialize test orchestrator."""
        self.options = options
        self.app = None
        self.report_generator = ReportGenerator()
        self.start_time = time.time()
        
        # Initialize QApplication if needed
        if options.run_gui or not options.no_gui:
            self.app = QApplication.instance()
            if self.app is None:
                self.app = QApplication(sys.argv if sys.argv else [])
    
    def run_layer_features_tests(self) -> bool:
        """Run layer features test suite."""
        if self.options.layer_only or not self.options.license_only:
            print("\n" + "=" * 80)
            print("RUNNING: Layer Features Test Suite")
            print("=" * 80)
            
            suite = LayerFeaturesTestSuite(self.app)
            suite_result = suite.run_all_tests()
            self.report_generator.add_suite_result(suite_result)
            
            return suite_result.failed == 0
        return True
    
    def run_license_system_tests(self) -> bool:
        """Run license system test suite."""
        if self.options.license_only or not self.options.layer_only:
            print("\n" + "=" * 80)
            print("RUNNING: License System Test Suite")
            print("=" * 80)
            
            suite = LicenseSystemTestSuite(self.app)
            suite_result = suite.run_all_tests()
            self.report_generator.add_suite_result(suite_result)
            
            return suite_result.failed == 0
    
    def run_integration_tests(self) -> bool:
        """Run integration test suite."""
        if not (self.options.layer_only or self.options.license_only):
            print("\n" + "=" * 80)
            print("RUNNING: Integration Test Suite")
            print("=" * 80)
            
            suite = IntegrationTestSuite(self.app)
            suite_result = suite.run_all_tests()
            self.report_generator.add_suite_result(suite_result)
            
            return suite_result.failed == 0
        return True
    
    def run_performance_tests(self) -> bool:
        """Run performance test suite."""
        if self.options.performance and not (self.options.layer_only or self.options.license_only):
            print("\n" + "=" * 80)
            print("RUNNING: Performance Test Suite")
            print("=" * 80)
            
            suite = PerformanceTestSuite(self.app)
            suite_result = suite.run_all_tests()
            self.report_generator.add_suite_result(suite_result)
            
            return suite_result.failed == 0
        return True
    
    def run_gui_tests(self) -> bool:
        """Run GUI test suite."""
        if self.options.run_gui and not self.options.no_gui:
            print("\n" + "=" * 80)
            print("RUNNING: GUI Interactions Test Suite")
            print("=" * 80)
            
            suite = GUITestSuite(self.app)
            suite_result = suite.run_all_tests()
            self.report_generator.add_suite_result(suite_result)
            
            return suite_result.failed == 0
        return True
    
    def run_all_tests(self) -> dict:
        """Run all test suites."""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE AUTOMATED TEST SUITE")
        print("=" * 80)
        print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Options: GUI={not self.options.no_gui}, Performance={self.options.performance}")
        print("=" * 80)
        
        results = {
            'layer_features': True,
            'license_system': True,
            'integration': True,
            'performance': True,
            'gui': True,
        }
        
        # Run test suites
        try:
            results['layer_features'] = self.run_layer_features_tests()
        except Exception as e:
            print(f"\nERROR in layer features tests: {e}")
            results['layer_features'] = False
        
        try:
            results['license_system'] = self.run_license_system_tests()
        except Exception as e:
            print(f"\nERROR in license system tests: {e}")
            results['license_system'] = False
        
        try:
            results['integration'] = self.run_integration_tests()
        except Exception as e:
            print(f"\nERROR in integration tests: {e}")
            results['integration'] = False
        
        try:
            results['performance'] = self.run_performance_tests()
        except Exception as e:
            print(f"\nERROR in performance tests: {e}")
            results['performance'] = False
        
        try:
            results['gui'] = self.run_gui_tests()
        except Exception as e:
            print(f"\nERROR in GUI tests: {e}")
            results['gui'] = False
        
        return results
    
    def generate_reports(self) -> dict:
        """Generate test reports."""
        print("\n" + "=" * 80)
        print("GENERATING REPORTS")
        print("=" * 80)
        
        report_paths = self.report_generator.generate_all()
        
        print(f"\nReports generated:")
        print(f"  HTML: {report_paths['html']}")
        print(f"  JSON: {report_paths['json']}")
        
        return report_paths
    
    def print_summary(self, results: dict):
        """Print test execution summary."""
        total_time = time.time() - self.start_time
        
        print("\n" + "=" * 80)
        print("TEST EXECUTION SUMMARY")
        print("=" * 80)
        
        all_passed = all(results.values())
        
        for suite_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {suite_name:20s} {status}")
        
        print("=" * 80)
        print(f"Total execution time: {total_time:.2f} seconds")
        print(f"Overall status: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        print("=" * 80)
        
        return all_passed


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Comprehensive automated test suite for Upload Bridge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python tests/test_complete_system_automated.py
  
  # Run without GUI tests (backend only)
  python tests/test_complete_system_automated.py --no-gui
  
  # Run only layer features tests
  python tests/test_complete_system_automated.py --layer-only
  
  # Run only license system tests
  python tests/test_complete_system_automated.py --license-only
  
  # Run without performance tests
  python tests/test_complete_system_automated.py --no-performance
        """
    )
    
    parser.add_argument(
        '--no-gui',
        action='store_true',
        help='Skip GUI tests (backend only)'
    )
    
    parser.add_argument(
        '--gui',
        action='store_true',
        dest='run_gui',
        help='Include GUI tests (default: True unless --no-gui)'
    )
    
    parser.add_argument(
        '--layer-only',
        action='store_true',
        help='Run only layer features tests'
    )
    
    parser.add_argument(
        '--license-only',
        action='store_true',
        help='Run only license system tests'
    )
    
    parser.add_argument(
        '--performance',
        action='store_true',
        default=True,
        help='Include performance tests (default: True)'
    )
    
    parser.add_argument(
        '--no-performance',
        action='store_false',
        dest='performance',
        help='Skip performance tests'
    )
    
    parser.add_argument(
        '--report-dir',
        type=str,
        help='Custom report directory (default: tests/reports)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    options = parse_arguments()
    
    # Ensure report directory exists
    if options.report_dir:
        report_dir = Path(options.report_dir)
        report_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Create test orchestrator
        tester = CompleteSystemTester(options)
        
        # Run all tests
        results = tester.run_all_tests()
        
        # Generate reports
        report_paths = tester.generate_reports()
        
        # Print summary
        all_passed = tester.print_summary(results)
        
        # Exit with appropriate code
        sys.exit(0 if all_passed else 1)
        
    except KeyboardInterrupt:
        print("\n\nTest execution interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

