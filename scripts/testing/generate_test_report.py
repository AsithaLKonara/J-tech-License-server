#!/usr/bin/env python3
"""
Generate Test Report - Comprehensive test execution report

Runs all tests and generates a detailed report with pass/fail statistics.
"""

import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime


def run_tests(test_path: str, exclude: list = None) -> dict:
    """Run pytest and capture results."""
    cmd = [
        "python", "-m", "pytest",
        test_path,
        "-v",
        "--tb=line",
        "--json-report",
        "--json-report-file=test_report.json"
    ]
    
    if exclude:
        cmd.extend(["-k", f"not ({' or '.join(exclude)})"])
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        # Try to load JSON report
        report_data = {}
        if Path("test_report.json").exists():
            with open("test_report.json") as f:
                report_data = json.load(f)
        
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "report": report_data
        }
    except subprocess.TimeoutExpired:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": "Test timeout after 10 minutes",
            "report": {}
        }
    except Exception as e:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "report": {}
        }


def generate_summary():
    """Generate test summary report."""
    
    # Test categories
    categories = {
        "unit": {"path": "tests/unit/", "exclude": []},
        "integration": {"path": "tests/integration/", "exclude": []},
        "comprehensive": {"path": "tests/comprehensive/", "exclude": []},
        "e2e": {"path": "tests/e2e/", "exclude": []},
        "all_except_gui": {"path": "tests/", "exclude": ["gui", "test_design_tab"]}
    }
    
    results = {}
    
    print("=" * 80)
    print("TEST EXECUTION REPORT")
    print("=" * 80)
    print(f"Generated: {datetime.now().isoformat()}\n")
    
    for category, config in categories.items():
        print(f"\nRunning {category} tests...")
        print("-" * 80)
        
        result = run_tests(config["path"], config["exclude"])
        results[category] = result
        
        # Parse summary from stdout
        lines = result["stdout"].split("\n")
        summary_line = [l for l in lines if "passed" in l.lower() or "failed" in l.lower() or "error" in l.lower()]
        
        if summary_line:
            print(summary_line[-1])
        else:
            print(f"Exit code: {result['exit_code']}")
            if result["stderr"]:
                print(f"Error: {result['stderr'][:500]}")
    
    # Overall summary
    print("\n" + "=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)
    
    total_passed = 0
    total_failed = 0
    total_skipped = 0
    total_errors = 0
    
    for category, result in results.items():
        if "report" in result and "summary" in result["report"]:
            summary = result["report"]["summary"]
            passed = summary.get("passed", 0)
            failed = summary.get("failed", 0)
            skipped = summary.get("skipped", 0)
            error = summary.get("error", 0)
            
            total_passed += passed
            total_failed += failed
            total_skipped += skipped
            total_errors += error
            
            print(f"{category:20} | Passed: {passed:4} | Failed: {failed:4} | Skipped: {skipped:4} | Errors: {error:4}")
    
    print("-" * 80)
    print(f"{'TOTAL':20} | Passed: {total_passed:4} | Failed: {total_failed:4} | Skipped: {total_skipped:4} | Errors: {total_errors:4}")
    
    total_tests = total_passed + total_failed + total_skipped + total_errors
    if total_tests > 0:
        pass_rate = (total_passed / total_tests) * 100
        print(f"\nPass Rate: {pass_rate:.1f}%")
    
    # Save results
    report_file = Path("test_execution_report.json")
    with open(report_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "passed": total_passed,
                "failed": total_failed,
                "skipped": total_skipped,
                "errors": total_errors,
                "total": total_tests,
                "pass_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0
            },
            "categories": results
        }, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_file}")
    
    return total_failed == 0 and total_errors == 0


if __name__ == "__main__":
    success = generate_summary()
    sys.exit(0 if success else 1)

