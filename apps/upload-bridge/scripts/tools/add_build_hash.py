#!/usr/bin/env python3
"""
Add Build Hash Recording Script

Records build hash/checksum to build artifacts for verification.
"""

import hashlib
import sys
import json
from pathlib import Path
from datetime import datetime


def calculate_file_hash(file_path: Path, algorithm='sha256') -> str:
    """Calculate hash of a file."""
    hash_obj = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def record_build_hash(build_dir: Path, artifact_patterns: list = None):
    """
    Record build hash for build artifacts.
    
    Args:
        build_dir: Directory containing build artifacts
        artifact_patterns: List of glob patterns for artifacts to hash
    """
    if artifact_patterns is None:
        artifact_patterns = [
            "*.exe",
            "*.msi",
            "*.dmg",
            "*.pkg",
            "*.deb",
            "*.rpm",
            "*.tar.gz",
            "*.zip",
        ]
    
    build_dir = Path(build_dir)
    if not build_dir.exists():
        print(f"Error: Build directory not found: {build_dir}", file=sys.stderr)
        return False
    
    # Find all artifacts
    artifacts = []
    for pattern in artifact_patterns:
        artifacts.extend(build_dir.glob(pattern))
    
    if not artifacts:
        print(f"No artifacts found in {build_dir}", file=sys.stderr)
        return False
    
    # Calculate hashes
    build_info = {
        "build_time": datetime.utcnow().isoformat() + "Z",
        "artifacts": {}
    }
    
    for artifact in artifacts:
        if artifact.is_file():
            file_hash = calculate_file_hash(artifact)
            file_size = artifact.stat().st_size
            build_info["artifacts"][artifact.name] = {
                "hash_sha256": file_hash,
                "size_bytes": file_size,
                "path": str(artifact.relative_to(build_dir))
            }
            print(f"Recorded hash for: {artifact.name} ({file_size} bytes)")
    
    # Write build info to JSON file
    build_info_file = build_dir / "build_info.json"
    with open(build_info_file, 'w') as f:
        json.dump(build_info, f, indent=2)
    
    print(f"\nBuild info written to: {build_info_file}")
    
    # Also create a text file with hashes (for easy viewing)
    hash_file = build_dir / "build_hashes.txt"
    with open(hash_file, 'w') as f:
        f.write(f"Build Time: {build_info['build_time']}\n")
        f.write("=" * 60 + "\n\n")
        for artifact_name, info in build_info["artifacts"].items():
            f.write(f"{artifact_name}\n")
            f.write(f"  SHA256: {info['hash_sha256']}\n")
            f.write(f"  Size:   {info['size_bytes']:,} bytes\n")
            f.write("\n")
    
    print(f"Hash summary written to: {hash_file}")
    
    return True


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        build_dir = Path(sys.argv[1])
    else:
        # Default to dist directory
        script_dir = Path(__file__).resolve().parent
        build_dir = script_dir.parent.parent.parent / "apps" / "upload-bridge" / "dist"
    
    print(f"Recording build hashes for artifacts in: {build_dir}\n")
    
    success = record_build_hash(build_dir)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

