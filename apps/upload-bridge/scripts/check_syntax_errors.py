#!/usr/bin/env python3
"""
Check for syntax errors in Python files.

This script scans the codebase for common syntax errors like:
- Missing indentation after else/if/try/except
- Incomplete statements
- Missing colons
"""

import os
import sys
import ast
from pathlib import Path
from typing import List, Tuple

def check_file_syntax(file_path: Path) -> Tuple[bool, List[str]]:
    """Check syntax of a Python file."""
    errors = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Try to parse the file
        try:
            ast.parse(source)
            return True, []
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
            if e.text:
                errors.append(f"  Text: {e.text.strip()}")
            return False, errors
    except Exception as e:
        errors.append(f"Error reading file: {e}")
        return False, errors

def find_python_files(directory: Path) -> List[Path]:
    """Find all Python files in directory."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip common directories
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'venv', 'env', 'build', 'dist']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    return python_files

def main():
    """Main function."""
    app_dir = Path(__file__).parent.parent
    
    print("=" * 80)
    print("SYNTAX ERROR CHECKER")
    print("=" * 80)
    print(f"Checking: {app_dir}")
    print()
    
    python_files = find_python_files(app_dir)
    print(f"Found {len(python_files)} Python files")
    print()
    
    errors_found = []
    files_checked = 0
    
    for file_path in python_files:
        files_checked += 1
        relative_path = file_path.relative_to(app_dir)
        
        is_valid, errors = check_file_syntax(file_path)
        
        if not is_valid:
            errors_found.append((relative_path, errors))
            print(f"❌ {relative_path}")
            for error in errors:
                print(f"   {error}")
        elif files_checked % 50 == 0:
            print(f"✓ Checked {files_checked}/{len(python_files)} files...")
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Files checked: {files_checked}")
    print(f"Files with errors: {len(errors_found)}")
    
    if errors_found:
        print("\n❌ ERRORS FOUND:")
        for file_path, errors in errors_found:
            print(f"\n{file_path}:")
            for error in errors:
                print(f"  - {error}")
        return 1
    else:
        print("\n✅ No syntax errors found!")
        return 0

if __name__ == '__main__':
    sys.exit(main())

