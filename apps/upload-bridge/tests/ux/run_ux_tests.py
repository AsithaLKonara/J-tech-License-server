#!/usr/bin/env python3
"""
Test Execution Script for UX Test Suite
Runs all UX tests and generates a report
"""

import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime


def run_tests():
    """Run all UX tests and collect results"""
    print("=" * 70)
    print("🧪 Running UX Test Suite")
    print("=" * 70)
    print()
    
    test_files = [
        "test_pattern_loading_errors.py",
        "test_brush_broadcast_warning.py",
        "test_delete_frame_validation.py",
        "test_undo_redo_states.py",
        "test_unsaved_changes_warning.py",
        "test_export_validation.py",
    ]
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {},
        "summary": {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
        }
    }
    
    for test_file in test_files:
        print(f"Running {test_file}...")
        try:
            result = subprocess.run(
                ["pytest", f"tests/ux/{test_file}", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Parse results (simplified)
            passed = result.stdout.count("PASSED")
            failed = result.stdout.count("FAILED")
            skipped = result.stdout.count("SKIPPED")
            
            results["tests"][test_file] = {
                "status": "passed" if result.returncode == 0 else "failed",
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "output": result.stdout,
                "errors": result.stderr if result.returncode != 0 else None,
            }
            
            results["summary"]["total"] += passed + failed + skipped
            results["summary"]["passed"] += passed
            results["summary"]["failed"] += failed
            results["summary"]["skipped"] += skipped
            
            if result.returncode == 0:
                print(f"  ✅ {test_file}: PASSED")
            else:
                print(f"  ❌ {test_file}: FAILED")
                print(f"     {failed} test(s) failed")
            
        except subprocess.TimeoutExpired:
            print(f"  ⏱️  {test_file}: TIMEOUT")
            results["tests"][test_file] = {
                "status": "timeout",
                "error": "Test execution exceeded 5 minutes"
            }
        except Exception as e:
            print(f"  ❌ {test_file}: ERROR - {e}")
            results["tests"][test_file] = {
                "status": "error",
                "error": str(e)
            }
        
        print()
    
    # Print summary
    print("=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    print(f"Total Tests: {results['summary']['total']}")
    print(f"Passed: {results['summary']['passed']} ✅")
    print(f"Failed: {results['summary']['failed']} ❌")
    print(f"Skipped: {results['summary']['skipped']} ⏭️")
    print()
    
    # Save results to JSON
    output_file = Path("test_results_ux.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"📄 Detailed results saved to: {output_file}")
    print()
    
    # Return exit code
    return 0 if results["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(run_tests())

