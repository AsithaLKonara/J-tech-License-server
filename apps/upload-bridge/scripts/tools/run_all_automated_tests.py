#!/usr/bin/env python3
"""
Run All Automated Production Readiness Tests

This script executes all automated tests that can be run programmatically
without requiring manual intervention (Windows VMs, hardware devices, etc.).
"""

import sys
import subprocess
import time
from pathlib import Path
from typing import List, Tuple, Dict
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


class TestRunner:
    """Runner for automated production readiness tests."""
    
    def __init__(self):
        self.results: List[Dict[str, any]] = []
        self.start_time = datetime.now()
    
    def run_command(self, name: str, command: List[str], cwd: Path = None) -> Tuple[bool, str]:
        """Run a test command and return (success, output)."""
        print(f"\n{'='*60}")
        print(f"Running: {name}")
        print(f"Command: {' '.join(command)}")
        print(f"{'='*60}\n")
        
        try:
            result = subprocess.run(
                command,
                cwd=cwd or project_root,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            success = result.returncode == 0
            output = result.stdout + result.stderr
            
            print(output)
            
            self.results.append({
                'name': name,
                'success': success,
                'returncode': result.returncode,
                'output': output,
                'timestamp': datetime.now().isoformat()
            })
            
            return success, output
            
        except subprocess.TimeoutExpired:
            error_msg = f"Test timed out after 1 hour"
            print(f"ERROR: {error_msg}")
            self.results.append({
                'name': name,
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            })
            return False, error_msg
        except Exception as e:
            error_msg = f"Test failed with exception: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.results.append({
                'name': name,
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            })
            return False, error_msg
    
    def run_version_consistency_check(self) -> bool:
        """Run version consistency verification."""
        script_path = project_root / "scripts" / "tools" / "verify_version_consistency.py"
        success, _ = self.run_command(
            "Version Consistency Check",
            [sys.executable, str(script_path), str(project_root)]
        )
        return success
    
    def run_firmware_validation_tests(self) -> bool:
        """Run firmware validation unit tests."""
        test_file = project_root / "tests" / "unit" / "test_firmware_validation.py"
        if not test_file.exists():
            print(f"WARNING: Test file not found: {test_file}")
            return False
        
        success, _ = self.run_command(
            "Firmware Validation Unit Tests",
            [sys.executable, "-m", "pytest", str(test_file), "-v"]
        )
        return success
    
    def run_performance_tests(self) -> bool:
        """Run performance test suite."""
        test_file = project_root / "tests" / "helpers" / "test_performance.py"
        if not test_file.exists():
            print(f"WARNING: Test file not found: {test_file}")
            return False
        
        # Run as module to ensure imports work
        success, _ = self.run_command(
            "Performance Test Suite",
            [sys.executable, str(test_file)]
        )
        return success
    
    def run_fps_tests(self) -> bool:
        """Run FPS measurement test suite."""
        test_file = project_root / "tests" / "helpers" / "test_fps_measurement.py"
        if not test_file.exists():
            print(f"WARNING: Test file not found: {test_file}")
            return False
        
        success, _ = self.run_command(
            "FPS Measurement Test Suite",
            [sys.executable, str(test_file)]
        )
        return success
    
    def generate_report(self) -> str:
        """Generate test execution report."""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.get('success', False))
        failed = total - passed
        
        report = f"""
{'='*60}
Automated Production Readiness Tests - Execution Report
{'='*60}

Start Time: {self.start_time.isoformat()}
End Time: {end_time.isoformat()}
Duration: {duration}

Results Summary:
  Total Tests: {total}
  Passed: {passed}
  Failed: {failed}
  Success Rate: {(passed/total*100) if total > 0 else 0:.1f}%

{'='*60}
Detailed Results:
{'='*60}
"""
        
        for i, result in enumerate(self.results, 1):
            status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
            report += f"\n{i}. {result['name']}: {status}\n"
            if 'error' in result:
                report += f"   Error: {result['error']}\n"
            if 'returncode' in result:
                report += f"   Return Code: {result['returncode']}\n"
            report += f"   Timestamp: {result.get('timestamp', 'N/A')}\n"
        
        report += f"\n{'='*60}\n"
        
        return report
    
    def run_all_automated_tests(self):
        """Run all automated tests."""
        print("\n" + "="*60)
        print("Automated Production Readiness Test Suite")
        print("="*60)
        print(f"Started: {self.start_time.isoformat()}")
        print("="*60)
        
        # Tests that can be run automatically
        tests = [
            ("Version Consistency Check", self.run_version_consistency_check),
            ("Firmware Validation Tests", self.run_firmware_validation_tests),
            ("Performance Tests", self.run_performance_tests),
            ("FPS Measurement Tests", self.run_fps_tests),
        ]
        
        for name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                print(f"ERROR running {name}: {e}")
                self.results.append({
                    'name': name,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        # Generate and print report
        report = self.generate_report()
        print(report)
        
        # Save report to file
        report_file = project_root / "docs" / "AUTOMATED_TEST_RESULTS.md"
        report_file.write_text(report)
        print(f"\nReport saved to: {report_file}")
        
        # Return exit code based on results
        all_passed = all(r.get('success', False) for r in self.results)
        return 0 if all_passed else 1


def main():
    """Main entry point."""
    runner = TestRunner()
    exit_code = runner.run_all_automated_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

