#!/usr/bin/env python3
"""
Verify Build Hash Script

Verifies build hashes recorded by add_build_hash.py.
Can verify:
- Build artifacts against recorded hashes
- Executable integrity
- Build consistency
"""

import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple


def calculate_file_hash(file_path: Path, algorithm='sha256') -> str:
    """Calculate hash of a file."""
    hash_obj = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def verify_build_hash(build_dir: Path, build_info_file: str = "build_info.json") -> Tuple[bool, List[str]]:
    """
    Verify build hashes against recorded hashes.
    
    Args:
        build_dir: Directory containing build artifacts
        build_info_file: Name of build info JSON file
    
    Returns:
        (is_valid, list_of_issues)
    """
    build_dir = Path(build_dir)
    build_info_path = build_dir / build_info_file
    
    if not build_info_path.exists():
        return False, [f"Build info file not found: {build_info_path}"]
    
    try:
        with open(build_info_path, 'r') as f:
            build_info = json.load(f)
    except Exception as e:
        return False, [f"Failed to load build info: {e}"]
    
    issues = []
    artifacts = build_info.get('artifacts', {})
    
    if not artifacts:
        return False, ["No artifacts recorded in build info"]
    
    print(f"Verifying {len(artifacts)} build artifacts...")
    print()
    
    all_valid = True
    for artifact_name, artifact_info in artifacts.items():
        artifact_path = build_dir / artifact_name
        
        if not artifact_path.exists():
            issues.append(f"Artifact not found: {artifact_name}")
            all_valid = False
            continue
        
        expected_hash = artifact_info.get('hash_sha256')
        if not expected_hash:
            issues.append(f"No hash recorded for: {artifact_name}")
            all_valid = False
            continue
        
        # Calculate current hash
        current_hash = calculate_file_hash(artifact_path)
        
        if current_hash != expected_hash:
            issues.append(
                f"Hash mismatch for {artifact_name}:\n"
                f"  Expected: {expected_hash}\n"
                f"  Current:  {current_hash}"
            )
            all_valid = False
        else:
            expected_size = artifact_info.get('size_bytes', 0)
            current_size = artifact_path.stat().st_size
            if current_size != expected_size:
                issues.append(
                    f"Size mismatch for {artifact_name}:\n"
                    f"  Expected: {expected_size:,} bytes\n"
                    f"  Current:  {current_size:,} bytes"
                )
                all_valid = False
            else:
                print(f"  ✓ {artifact_name} - Hash and size match")
    
    return all_valid, issues


def verify_executable_integrity(exe_path: Path) -> Tuple[bool, str]:
    """
    Verify executable integrity by checking if it can be read and has valid structure.
    
    Args:
        exe_path: Path to executable
    
    Returns:
        (is_valid, message)
    """
    if not exe_path.exists():
        return False, f"Executable not found: {exe_path}"
    
    try:
        # Check file is readable
        with open(exe_path, 'rb') as f:
            header = f.read(2)
        
        # Check for common executable signatures
        if exe_path.suffix == '.exe':
            # Windows PE signature: MZ
            if header != b'MZ':
                return False, "Invalid Windows executable signature"
        elif exe_path.suffix == '' or 'linux' in str(exe_path).lower():
            # Linux ELF signature
            if header != b'\x7fELF':
                return False, "Invalid ELF executable signature"
        
        # Calculate hash for reference
        file_hash = calculate_file_hash(exe_path)
        file_size = exe_path.stat().st_size
        
        return True, f"Executable valid (SHA256: {file_hash[:16]}..., Size: {file_size:,} bytes)"
    
    except Exception as e:
        return False, f"Error verifying executable: {e}"


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify build hashes")
    parser.add_argument('build_dir', nargs='?', help='Build directory (default: dist/)')
    parser.add_argument('--exe', help='Verify specific executable file')
    parser.add_argument('--info-file', default='build_info.json', help='Build info file name')
    args = parser.parse_args()
    
    if args.exe:
        # Verify single executable
        exe_path = Path(args.exe)
        is_valid, message = verify_executable_integrity(exe_path)
        if is_valid:
            print(f"✓ {exe_path.name}: {message}")
            return 0
        else:
            print(f"✗ {exe_path.name}: {message}")
            return 1
    
    # Verify build directory
    if args.build_dir:
        build_dir = Path(args.build_dir)
    else:
        # Default to dist directory
        script_dir = Path(__file__).resolve().parent
        build_dir = script_dir.parent.parent.parent / "apps" / "upload-bridge" / "dist"
    
    if not build_dir.exists():
        print(f"Error: Build directory not found: {build_dir}", file=sys.stderr)
        return 1
    
    print(f"Verifying build hashes in: {build_dir}\n")
    
    is_valid, issues = verify_build_hash(build_dir, args.info_file)
    
    if is_valid:
        print("\n✓ All build artifacts verified successfully")
        return 0
    else:
        print(f"\n✗ Verification failed ({len(issues)} issue(s)):\n")
        for issue in issues:
            print(f"  {issue}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
