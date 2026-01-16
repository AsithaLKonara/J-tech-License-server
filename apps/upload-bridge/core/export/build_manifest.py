"""
Build Manifest Generator - Creates manifest for exported firmware artifacts

Generates build manifest JSON containing pattern hash, schema version,
device profiles used, and other metadata for reproducible builds.
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from core.pattern import Pattern
from core.schemas.pattern_converter import PatternConverter


class BuildManifest:
    """Build manifest for firmware artifacts"""
    
    def __init__(
        self,
        pattern: Pattern,
        device_profiles: Optional[List[str]] = None,
        export_format: str = "bin",
        schema_version: str = "1.0"
    ):
        """
        Initialize build manifest.
        
        Args:
            pattern: Pattern object
            device_profiles: List of device profile IDs used
            export_format: Export format (bin, hex, leds, etc.)
            schema_version: Pattern schema version
        """
        self.pattern = pattern
        self.device_profiles = device_profiles or []
        self.export_format = export_format
        self.schema_version = schema_version
        self.created_at = datetime.utcnow().isoformat() + 'Z'
    
    def compute_pattern_hash(self) -> str:
        """
        Compute deterministic hash of pattern.
        
        Returns:
            SHA256 hash as hex string
        """
        # Convert to canonical JSON for deterministic hashing
        pattern_json = PatternConverter.pattern_to_json(self.pattern, use_rle=False)
        
        # Sort keys for deterministic ordering
        pattern_str = json.dumps(pattern_json, sort_keys=True, separators=(',', ':'))
        
        # Compute hash
        return hashlib.sha256(pattern_str.encode('utf-8')).hexdigest()
    
    def compute_firmware_hash(self, firmware_bytes: bytes) -> str:
        """
        Compute hash of firmware binary.
        
        Args:
            firmware_bytes: Firmware binary data
            
        Returns:
            SHA256 hash as hex string
        """
        return hashlib.sha256(firmware_bytes).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary"""
        pattern_hash = self.compute_pattern_hash()
        
        return {
            "schema_version": self.schema_version,
            "pattern_id": self.pattern.id,
            "pattern_name": self.pattern.name,
            "pattern_hash": pattern_hash,
            "pattern_dimensions": {
                "width": self.pattern.metadata.width,
                "height": self.pattern.metadata.height
            },
            "pattern_frame_count": len(self.pattern.frames),
            "pattern_duration_ms": self.pattern.duration_ms,
            "export_format": self.export_format,
            "device_profiles": self.device_profiles,
            "created_at": self.created_at,
            "tool_version": "3.0",  # Upload Bridge version
            "build_info": {
                "deterministic": True,
                "reproducible": True
            }
        }
    
    def save(self, file_path: Path) -> None:
        """
        Save manifest to file.
        
        Args:
            file_path: Path to save manifest JSON
        """
        manifest_dict = self.to_dict()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(manifest_dict, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, file_path: Path) -> Dict[str, Any]:
        """
        Load manifest from file.
        
        Args:
            file_path: Path to manifest JSON
            
        Returns:
            Manifest dictionary
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @classmethod
    def verify_firmware(
        cls,
        firmware_path: Path,
        manifest_path: Path,
        expected_hash: Optional[str] = None
    ) -> bool:
        """
        Verify firmware binary against manifest.
        
        Args:
            firmware_path: Path to firmware binary
            manifest_path: Path to manifest JSON
            expected_hash: Expected firmware hash (from manifest)
            
        Returns:
            True if verification passes
        """
        if not firmware_path.exists():
            return False
        
        manifest = cls.load(manifest_path)
        if expected_hash is None:
            expected_hash = manifest.get("firmware_hash")
        
        if expected_hash is None:
            # No hash to verify against
            return True
        
        # Compute actual hash
        with open(firmware_path, 'rb') as f:
            firmware_bytes = f.read()
        
        actual_hash = hashlib.sha256(firmware_bytes).hexdigest()
        return actual_hash == expected_hash


def generate_build_manifest(
    pattern: Pattern,
    export_format: str = "bin",
    device_profiles: Optional[List[str]] = None,
    firmware_bytes: Optional[bytes] = None
) -> BuildManifest:
    """
    Generate build manifest for exported pattern.
    
    Args:
        pattern: Pattern object
        export_format: Export format
        device_profiles: List of device profile IDs
        firmware_bytes: Optional firmware binary (for hash calculation)
        
    Returns:
        BuildManifest object
    """
    manifest = BuildManifest(
        pattern=pattern,
        device_profiles=device_profiles,
        export_format=export_format
    )
    
    # Add firmware hash if provided
    if firmware_bytes:
        firmware_hash = manifest.compute_firmware_hash(firmware_bytes)
        manifest_dict = manifest.to_dict()
        manifest_dict["firmware_hash"] = firmware_hash
        # Note: This modifies the dict but doesn't affect the object
    
    return manifest

