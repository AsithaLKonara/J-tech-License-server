#!/usr/bin/env python3
"""Code Quality Audit Script"""

import re
from pathlib import Path
from collections import defaultdict

def find_code_quality_issues():
    """Find TODO, FIXME, XXX, HACK, BUG comments"""
    issues = defaultdict(list)
    
    # Exclude certain directories
    exclude_dirs = {'__pycache__', '.git', 'node_modules', 'venv', 'env', '.pytest_cache', 'build', 'dist'}
    
    for py_file in Path('.').rglob('*.py'):
        # Skip excluded directories
        if any(excluded in str(py_file) for excluded in exclude_dirs):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    # Check for TODO, FIXME, XXX, HACK, BUG
                    for marker in ['TODO', 'FIXME', 'XXX', 'HACK', 'BUG']:
                        if marker in line.upper():
                            issues[marker].append({
                                'file': str(py_file),
                                'line': line_num,
                                'content': line.strip()
                            })
        except Exception as e:
            pass  # Skip files that can't be read
    
    return issues

def main():
    print("=" * 80)
    print("Code Quality Audit")
    print("=" * 80)
    
    issues = find_code_quality_issues()
    
    total = sum(len(items) for items in issues.values())
    print(f"\n📊 Total Issues Found: {total}")
    
    print("\n📈 Breakdown by Type:")
    for marker, items in sorted(issues.items()):
        print(f"  {marker}: {len(items)}")
    
    # Show some examples
    print("\n⚠️  Sample Issues (first 10):")
    count = 0
    for marker, items in sorted(issues.items()):
        for item in items[:3]:  # Show first 3 of each type
            if count >= 10:
                break
            print(f"    {marker} in {item['file']}:{item['line']}")
            print(f"      {item['content'][:80]}")
            count += 1
        if count >= 10:
            break
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()

