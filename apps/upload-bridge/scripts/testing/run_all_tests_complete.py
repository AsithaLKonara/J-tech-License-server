#!/usr/bin/env python3
"""
Complete Test Runner - Runs all test suites and provides comprehensive report
"""

import sys
import subprocess
from pathlib import Path
import json
from datetime import datetime


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_pytest(path, name, maxfail=10):
    """Run pytest on a path and return results"""
    print(f"\n{'='*70}")
    print(f"Testing: {name}")
    print(f"Path: {path}")
    print(f"{'='*70}")
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(path),
        "-v",
        "--tb=line",
        f"--maxfail={maxfail}",
        "-q"
    ]
    
    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=300  # 5 minute timeout per suite
    )
    
    # Parse summary
    output = result.stdout
    passed = 0
    failed = 0
    error = 0
    
    for line in output.split('\n'):
        if 'passed' in line and 'failed' in line:
            # Parse: "X passed, Y failed in Zs"
            parts = line.split()
            for i, part in enumerate(parts):
                if part == 'passed':
                    passed = int(parts[i-1])
                elif part == 'failed':
                    failed = int(parts[i-1])
                elif part == 'error':
                    error = int(parts[i-1])
        elif 'passed' in line and 'failed' not in line:
            # Just passed
            parts = line.split()
            passed = int(parts[0])
    
    return {
        'name': name,
        'path': str(path),
        'returncode': result.returncode,
        'passed': passed,
        'failed': failed,
        'error': error,
        'summary': output.split('\n')[-3] if len(output.split('\n')) > 3 else 'No summary'
    }


def main():
    """Run all test suites"""
    
    test_suites = [
        # L0: Structural
        ("L0: Structural Tests", "tests/l0_structural/"),
        
        # L1: Unit
        ("L1: Unit Tests", "tests/unit/"),
        
        # L2: Comprehensive Feature Tests
        ("L2: Suite 1 - Design Tools Core", "tests/comprehensive/test_suite_1_design_tools_core.py"),
        ("L2: Suite 2 - Feature Overview", "tests/comprehensive/test_suite_2_feature_overview.py"),
        ("L2: Suite 3 - Tabs Integration", "tests/comprehensive/test_suite_3_all_tabs_integration.py"),
        ("L2: Suite 4 - Signal Connections", "tests/comprehensive/test_suite_4_signal_connections.py"),
        ("L2: Suite 5 - Error Handling", "tests/comprehensive/test_suite_5_error_handling.py"),
        ("L2: Suite 6 - UI Components", "tests/comprehensive/test_suite_6_ui_components.py"),
        ("L2: Suite 7 - Manager Interactions", "tests/comprehensive/test_suite_7_manager_interactions.py"),
        ("L2: Suite 8 - File I/O", "tests/comprehensive/test_suite_8_file_io.py"),
        
        # L3: Workflow
        ("L3: Workflow - Pattern Creation", "tests/l3_workflow/test_workflow_pattern_creation.py"),
        ("L3: Workflow - Automation", "tests/l3_workflow/test_workflow_automation.py"),
        ("L3: Workflow - Export", "tests/l3_workflow/test_workflow_export.py"),
        
        # L4: Non-functional
        ("L4: Performance Tests", "tests/l4_nonfunctional/test_performance.py"),
        ("L4: Stress Tests", "tests/l4_nonfunctional/test_stress.py"),
        
        # Meta
        ("Meta: Coverage Enforcer", "tests/meta/test_coverage_enforcer.py"),
        ("Meta: Documented Features", "tests/meta/test_documented_features_exist.py"),
        ("Meta: Suite Completeness", "tests/meta/test_suite_completeness.py"),
    ]
    
    print("\n" + "="*70)
    print("COMPLETE TEST RUNNER")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    results = []
    total_passed = 0
    total_failed = 0
    total_error = 0
    
    for suite_name, test_path in test_suites:
        full_path = PROJECT_ROOT / test_path
        if not full_path.exists():
            print(f"\n⚠️  SKIP: {suite_name} (not found)")
            results.append({
                'name': suite_name,
                'status': 'skipped',
                'reason': 'file not found'
            })
            continue
        
        try:
            result = run_pytest(full_path, suite_name)
            results.append(result)
            
            total_passed += result['passed']
            total_failed += result['failed']
            total_error += result['error']
            
            if result['returncode'] == 0:
                print(f"✅ PASS: {suite_name} ({result['passed']} tests)")
            else:
                print(f"❌ FAIL: {suite_name} ({result['failed']} failed, {result['error']} errors)")
        except subprocess.TimeoutExpired:
            print(f"⏱️  TIMEOUT: {suite_name}")
            results.append({
                'name': suite_name,
                'status': 'timeout'
            })
        except Exception as e:
            print(f"⚠️  ERROR: {suite_name} - {e}")
            results.append({
                'name': suite_name,
                'status': 'error',
                'error': str(e)
            })
    
    # Final summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    print(f"Total Test Suites: {len(test_suites)}")
    print(f"✅ Total Passed: {total_passed}")
    print(f"❌ Total Failed: {total_failed}")
    print(f"⚠️  Total Errors: {total_error}")
    print(f"⏭️  Skipped: {len([r for r in results if r.get('status') == 'skipped'])}")
    print("="*70)
    
    # Save results
    results_file = PROJECT_ROOT / "test_results_complete.json"
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_suites': len(test_suites),
                'total_passed': total_passed,
                'total_failed': total_failed,
                'total_error': total_error
            },
            'results': results
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: {results_file}")
    
    return 0 if total_failed == 0 and total_error == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

