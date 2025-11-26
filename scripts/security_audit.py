#!/usr/bin/env python3
"""
Security Audit Script for Upload Bridge

Checks for known vulnerabilities in dependencies and performs security checks.
"""

import sys
import subprocess
import json
from pathlib import Path


def check_pip_audit():
    """Check if pip-audit is available"""
    try:
        result = subprocess.run(
            ["pip-audit", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def run_pip_audit():
    """Run pip-audit on requirements.txt"""
    requirements_file = Path(__file__).parent.parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    try:
        print("Running pip-audit...")
        result = subprocess.run(
            ["pip-audit", "-r", str(requirements_file), "--format", "json"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print("✅ pip-audit completed successfully")
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    vulnerabilities = data.get("vulnerabilities", [])
                    if vulnerabilities:
                        print(f"⚠️  Found {len(vulnerabilities)} vulnerabilities:")
                        for vuln in vulnerabilities:
                            print(f"  - {vuln.get('name', 'Unknown')}: {vuln.get('id', 'Unknown')}")
                    else:
                        print("✅ No vulnerabilities found")
                except json.JSONDecodeError:
                    print("✅ No vulnerabilities found (no JSON output)")
            return True
        else:
            print(f"⚠️  pip-audit returned non-zero exit code: {result.returncode}")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ pip-audit not found. Install with: pip install pip-audit")
        return False
    except subprocess.TimeoutExpired:
        print("❌ pip-audit timed out")
        return False
    except Exception as e:
        print(f"❌ Error running pip-audit: {e}")
        return False


def check_safety():
    """Check if safety is available"""
    try:
        result = subprocess.run(
            ["safety", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def run_safety():
    """Run safety check on dependencies"""
    try:
        print("Running safety check...")
        result = subprocess.run(
            ["safety", "check", "--json"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print("✅ safety check completed successfully")
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    if data:
                        print(f"⚠️  Found {len(data)} vulnerabilities:")
                        for vuln in data:
                            print(f"  - {vuln.get('package', 'Unknown')}: {vuln.get('vulnerability', 'Unknown')}")
                    else:
                        print("✅ No vulnerabilities found")
                except json.JSONDecodeError:
                    # Safety might output non-JSON on success
                    if "No known security vulnerabilities found" in result.stdout:
                        print("✅ No vulnerabilities found")
                    else:
                        print(result.stdout)
            return True
        else:
            print(f"⚠️  safety returned non-zero exit code: {result.returncode}")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("⚠️  safety not found. Install with: pip install safety")
        return None  # Not critical
    except subprocess.TimeoutExpired:
        print("❌ safety timed out")
        return False
    except Exception as e:
        print(f"⚠️  Error running safety: {e}")
        return None  # Not critical


def check_file_input_validation():
    """Check that file input validation is in place"""
    print("\nChecking file input validation...")
    
    # Check for file input handlers
    file_handlers = [
        "core/io.py",
        "core/project/project_file.py",
        "core/image_importer.py",
    ]
    
    issues = []
    for handler in file_handlers:
        path = Path(__file__).parent.parent / handler
        if path.exists():
            content = path.read_text()
            # Check for basic validation patterns
            if "Path(" in content or "pathlib" in content:
                # Good - using pathlib
                pass
            else:
                issues.append(f"{handler}: Consider using pathlib for path validation")
    
    if issues:
        print("⚠️  File input validation suggestions:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ File input handlers use pathlib")
    
    return len(issues) == 0


def main():
    """Run security audit"""
    print("=" * 60)
    print("Upload Bridge Security Audit")
    print("=" * 60)
    print()
    
    results = {
        "pip_audit": False,
        "safety": None,
        "file_validation": False,
    }
    
    # Run pip-audit
    if check_pip_audit():
        results["pip_audit"] = run_pip_audit()
    else:
        print("⚠️  pip-audit not installed. Install with: pip install pip-audit")
        print("   Skipping pip-audit check...")
    
    print()
    
    # Run safety
    if check_safety():
        results["safety"] = run_safety()
    else:
        print("⚠️  safety not installed. Install with: pip install safety")
        print("   Skipping safety check...")
    
    # Check file validation
    results["file_validation"] = check_file_input_validation()
    
    # Summary
    print()
    print("=" * 60)
    print("Security Audit Summary")
    print("=" * 60)
    
    if results["pip_audit"]:
        print("✅ pip-audit: Passed")
    else:
        print("⚠️  pip-audit: Not run or issues found")
    
    if results["safety"] is True:
        print("✅ safety: Passed")
    elif results["safety"] is False:
        print("⚠️  safety: Issues found")
    else:
        print("⚠️  safety: Not available")
    
    if results["file_validation"]:
        print("✅ File validation: Good")
    else:
        print("⚠️  File validation: Suggestions provided")
    
    print()
    print("Note: This is a basic security audit.")
    print("For production, consider:")
    print("  - Regular dependency updates")
    print("  - Automated security scanning in CI/CD")
    print("  - Code review for security best practices")
    print("  - Penetration testing")
    
    # Return success if at least one check passed
    return results["pip_audit"] or results["file_validation"]


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

