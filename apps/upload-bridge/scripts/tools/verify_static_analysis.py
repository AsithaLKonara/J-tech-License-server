#!/usr/bin/env python3
"""
Verify Static Analysis Tools Setup

Checks that static analysis tools (ruff, black, mypy) are properly configured
in CI/CD workflows and can be run locally.
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent


def check_tool_installed(tool_name: str) -> Tuple[bool, str]:
    """Check if a tool is installed and return (is_installed, version_output)."""
    try:
        result = subprocess.run(
            [tool_name, "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, ""
    except FileNotFoundError:
        return False, ""
    except Exception as e:
        return False, str(e)


def check_ci_workflow_for_tool(tool_name: str) -> bool:
    """Check if tool is referenced in CI workflows."""
    workflows_dir = Path(__file__).resolve().parent.parent.parent.parent / ".github" / "workflows"
    
    if not workflows_dir.exists():
        return False
    
    for workflow_file in workflows_dir.glob("*.yml"):
        try:
            content = workflow_file.read_text()
            if tool_name.lower() in content.lower():
                return True
        except Exception:
            continue
    
    return False


def main():
    """Main entry point."""
    print("="*60)
    print("Static Analysis Tools Verification")
    print("="*60)
    
    tools_to_check = [
        ("black", "Code formatting"),
        ("mypy", "Type checking"),
        ("ruff", "Linting (optional - flake8 is currently used)"),
        ("flake8", "Linting (currently used in CI)")
    ]
    
    all_ok = True
    results = []
    
    for tool_name, description in tools_to_check:
        print(f"\nChecking {tool_name} ({description})...")
        
        # Check if installed
        is_installed, version = check_tool_installed(tool_name)
        if is_installed:
            print(f"  ✅ Installed: {version}")
        else:
            print(f"  ⚠️  Not installed locally (may be installed in CI)")
        
        # Check if in CI workflows
        in_ci = check_ci_workflow_for_tool(tool_name)
        if in_ci:
            print(f"  ✅ Found in CI workflows")
        else:
            if tool_name == "ruff":
                print(f"  ⚠️  Not in CI workflows (optional - flake8 is used instead)")
            else:
                print(f"  ❌ Not found in CI workflows")
                all_ok = False
        
        results.append({
            'tool': tool_name,
            'description': description,
            'installed': is_installed,
            'in_ci': in_ci
        })
    
    # Check CI workflow file directly
    print("\n" + "="*60)
    print("CI Workflow Analysis")
    print("="*60)
    
    ci_workflow = Path(__file__).resolve().parent.parent.parent.parent / ".github" / "workflows" / "ci.yml"
    if ci_workflow.exists():
        content = ci_workflow.read_text()
        print("\nCurrent CI setup:")
        if "black" in content:
            print("  ✅ black - configured")
        if "mypy" in content:
            print("  ✅ mypy - configured")
        if "flake8" in content:
            print("  ✅ flake8 - configured")
        if "ruff" in content:
            print("  ✅ ruff - configured")
        else:
            print("  ℹ️  ruff - not configured (flake8 used instead)")
    else:
        print("  ⚠️  CI workflow file not found")
        all_ok = False
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    if all_ok:
        print("✅ Static analysis tools are properly configured")
        print("\nNote: ruff is optional - flake8 is currently used in CI")
        return 0
    else:
        print("⚠️  Some tools may need configuration")
        return 1


if __name__ == "__main__":
    sys.exit(main())

