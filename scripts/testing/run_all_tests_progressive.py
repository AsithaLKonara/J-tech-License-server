#!/usr/bin/env python3
"""
Progressive Test Runner

Runs all test suites one by one and reports results.
"""

import sys
import subprocess
from pathlib import Path
import json
from datetime import datetime


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_test_suite(suite_name, test_path):
    """Run a test suite and return results"""
    print(f"\n{'='*60}")
    print(f"Running: {suite_name}")
    print(f"Path: {test_path}")
    print(f"{'='*60}")
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_path),
        "-v",
        "--tb=line",
        "--maxfail=5",  # Stop after 5 failures per suite
        "-q"
    ]
    
    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    # Parse output
    output_lines = result.stdout.split('\n')
    summary_line = [line for line in output_lines if 'passed' in line or 'failed' in line]
    
    return {
        'suite': suite_name,
        'path': str(test_path),
        'returncode': result.returncode,
        'summary': summary_line[-1] if summary_line else 'No summary',
        'stdout': result.stdout,
        'stderr': result.stderr
    }


def main():
    """Run all test suites progressively"""
    
    test_suites = [
        # L0: Structural
        ("L0: Structural - Imports", "tests/l0_structural/test_imports.py"),
        ("L0: Structural - Signals", "tests/l0_structural/test_signals.py"),
        ("L0: Structural - Class Attributes", "tests/l0_structural/test_class_attributes.py"),
        
        # L1: Unit (sample)
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
        ("L4: Performance", "tests/l4_nonfunctional/test_performance.py"),
        ("L4: Stress", "tests/l4_nonfunctional/test_stress.py"),
        
        # Meta
        ("Meta: Coverage Enforcer", "tests/meta/test_coverage_enforcer.py"),
        ("Meta: Documented Features", "tests/meta/test_documented_features_exist.py"),
        ("Meta: Suite Completeness", "tests/meta/test_suite_completeness.py"),
    ]
    
    results = []
    total_passed = 0
    total_failed = 0
    
    print("\n" + "="*60)
    print("PROGRESSIVE TEST RUNNER")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    for suite_name, test_path in test_suites:
        full_path = PROJECT_ROOT / test_path
        if not full_path.exists():
            print(f"\n⚠️  SKIP: {suite_name} (file not found: {test_path})")
            results.append({
                'suite': suite_name,
                'status': 'skipped',
                'reason': 'file not found'
            })
            continue
        
        result = run_test_suite(suite_name, test_path)
        results.append(result)
        
        if result['returncode'] == 0:
            print(f"✅ PASS: {suite_name}")
            total_passed += 1
        else:
            print(f"❌ FAIL: {suite_name}")
            total_failed += 1
            print(f"   Summary: {result['summary']}")
    
    # Final summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    print(f"Total Suites: {len(test_suites)}")
    print(f"✅ Passed: {total_passed}")
    print(f"❌ Failed: {total_failed}")
    print(f"⏭️  Skipped: {len(test_suites) - total_passed - total_failed}")
    print("="*60)
    
    # Save results to JSON
    results_file = PROJECT_ROOT / "test_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total': len(test_suites),
                'passed': total_passed,
                'failed': total_failed,
                'skipped': len(test_suites) - total_passed - total_failed
            },
            'results': results
        }, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

