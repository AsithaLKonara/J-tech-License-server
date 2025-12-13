#!/usr/bin/env python3
"""
Comprehensive Test Runner for LED Matrix Application
Runs all test flows from the comprehensive testing plan

Usage:
    python run_comprehensive_tests.py                    # Run all tests
    python run_comprehensive_tests.py --flow 1           # Run specific flow
    python run_comprehensive_tests.py --phase 1          # Run specific phase
    python run_comprehensive_tests.py --verbose          # Verbose output
    python run_comprehensive_tests.py --coverage         # With coverage
"""

import sys
import os
import argparse
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


class ComprehensiveTestRunner:
    """Runs comprehensive test suite with reporting"""
    
    def __init__(self):
        self.test_results: Dict[str, Dict] = {}
        self.start_time = None
        self.end_time = None
        
    def run_tests(self, flow: int = None, phase: int = None, verbose: bool = False, 
                  coverage: bool = False) -> Tuple[int, int, int]:
        """Run tests and return (passed, failed, total)"""
        self.start_time = datetime.now()
        
        # Build pytest command
        cmd = ["python", "-m", "pytest"]
        
        if flow:
            # Run specific flow
            test_file = f"tests/comprehensive/test_comprehensive_led_matrix_flows.py"
            flow_class = self._get_flow_class(flow)
            if flow_class:
                cmd.extend([test_file, f"-k", flow_class])
        elif phase:
            # Run specific phase
            flows = self._get_phase_flows(phase)
            test_file = f"tests/comprehensive/test_comprehensive_led_matrix_flows.py"
            if flows:
                flow_classes = " or ".join([self._get_flow_class(f) for f in flows])
                cmd.extend([test_file, "-k", flow_classes])
        else:
            # Run all tests
            cmd.append("tests/comprehensive/test_comprehensive_led_matrix_flows.py")
        
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")
        
        if coverage:
            cmd.extend(["--cov=core", "--cov=ui", "--cov=domain", 
                       "--cov-report=html", "--cov-report=term"])
        
        # Add test output options
        cmd.extend(["--tb=short", "--color=yes"])
        
        print(f"Running: {' '.join(cmd)}")
        print("=" * 70)
        
        # Run pytest
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        self.end_time = datetime.now()
        
        # Parse results
        passed = 0
        failed = 0
        total = 0
        
        # Try to parse pytest output
        output_lines = result.stdout.split('\n')
        for line in output_lines:
            if "passed" in line.lower() and "failed" in line.lower():
                # Parse pytest summary line
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed":
                        if i > 0:
                            try:
                                passed = int(parts[i-1])
                            except:
                                pass
                    elif part == "failed":
                        if i > 0:
                            try:
                                failed = int(parts[i-1])
                            except:
                                pass
        
        total = passed + failed
        
        return passed, failed, total
    
    def _get_flow_class(self, flow: int) -> str:
        """Get test class name for flow number"""
        flow_classes = {
            1: "TestFlow1_ApplicationLaunch",
            2: "TestFlow2_PatternCreation",
            3: "TestFlow3_DrawingTools",
            4: "TestFlow4_LayerSystem",
            5: "TestFlow5_FrameManagement",
            6: "TestFlow6_AutomationActions",
            7: "TestFlow7_EffectsLibrary",
            8: "TestFlow8_MediaUpload",
            9: "TestFlow9_PreviewTab",
            10: "TestFlow10_FlashTab",
            11: "TestFlow11_BatchFlash",
            12: "TestFlow12_PatternLibrary",
            13: "TestFlow13_AudioReactive",
            14: "TestFlow14_WiFiUpload",
            15: "TestFlow15_ArduinoIDE",
            16: "TestFlow16_ImportFormats",
            17: "TestFlow17_ExportFormats",
            18: "TestFlow18_CrossTabIntegration",
            19: "TestFlow19_CircularLayouts",
            20: "TestFlow20_ErrorHandling",
        }
        return flow_classes.get(flow, "")
    
    def _get_phase_flows(self, phase: int) -> List[int]:
        """Get flow numbers for phase"""
        phases = {
            1: [1, 2, 3, 9, 10, 16, 17],  # Core functionality
            2: [3, 4, 5, 6, 7, 8],        # Advanced features
            3: [18, 19, 20],               # Integration & edge cases
            4: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]  # UAT
        }
        return phases.get(phase, [])
    
    def generate_report(self, passed: int, failed: int, total: int, 
                       output_file: str = None) -> str:
        """Generate test execution report"""
        duration = (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0
        
        report = f"""
{'=' * 70}
COMPREHENSIVE TEST EXECUTION REPORT
{'=' * 70}

Execution Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_time else 'N/A'}
Duration: {duration:.2f} seconds

Test Results:
  Total Tests: {total}
  Passed: {passed} ({passed/total*100:.1f}% if total > 0 else 0)
  Failed: {failed} ({failed/total*100:.1f}% if total > 0 else 0)

Test Coverage:
  - Application Launch & Initialization: Flow 1
  - Pattern Creation: Flow 2
  - Drawing Tools: Flow 3
  - Layer System: Flow 4
  - Frame Management: Flow 5
  - Automation Actions: Flow 6
  - Effects Library: Flow 7
  - Media Upload: Flow 8
  - Preview Tab: Flow 9
  - Flash Tab: Flow 10
  - Batch Flash: Flow 11
  - Pattern Library: Flow 12
  - Audio Reactive: Flow 13
  - WiFi Upload: Flow 14
  - Arduino IDE: Flow 15
  - Import Formats: Flow 16
  - Export Formats: Flow 17
  - Cross-Tab Integration: Flow 18
  - Circular Layouts: Flow 19
  - Error Handling: Flow 20

{'=' * 70}
"""
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
            print(f"Report saved to: {output_file}")
        
        return report


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Comprehensive Test Runner")
    parser.add_argument("--flow", type=int, help="Run specific flow (1-20)")
    parser.add_argument("--phase", type=int, help="Run specific phase (1-4)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", "-c", action="store_true", help="Generate coverage report")
    parser.add_argument("--report", "-r", type=str, help="Save report to file")
    
    args = parser.parse_args()
    
    runner = ComprehensiveTestRunner()
    
    print("=" * 70)
    print("COMPREHENSIVE LED MATRIX APPLICATION TEST SUITE")
    print("=" * 70)
    print()
    
    passed, failed, total = runner.run_tests(
        flow=args.flow,
        phase=args.phase,
        verbose=args.verbose,
        coverage=args.coverage
    )
    
    print()
    report = runner.generate_report(passed, failed, total, args.report)
    print(report)
    
    # Exit with appropriate code
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()

