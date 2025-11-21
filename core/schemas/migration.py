"""
Schema Migration Utilities - Handle pattern schema version upgrades

Provides migration functions to convert pattern JSON between schema versions.
"""

import json
import uuid
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from core.schemas.pattern_schema_v1 import PATTERN_SCHEMA_V1, PatternSchemaError


class SchemaMigrator:
    """Handles migration between schema versions"""
    
    SUPPORTED_VERSIONS = ["1.0"]
    CURRENT_VERSION = "1.0"
    
    @staticmethod
    def get_schema_version(data: Dict[str, Any]) -> Optional[str]:
        """
        Get schema version from pattern JSON.
        
        Args:
            data: Pattern JSON data
            
        Returns:
            Schema version string or None if not present
        """
        return data.get("schema_version")
    
    @staticmethod
    def needs_migration(data: Dict[str, Any]) -> bool:
        """
        Check if pattern JSON needs migration.
        
        Args:
            data: Pattern JSON data
            
        Returns:
            True if migration is needed
        """
        version = SchemaMigrator.get_schema_version(data)
        if version is None:
            # Legacy format - needs migration
            return True
        return version != SchemaMigrator.CURRENT_VERSION
    
    @staticmethod
    def migrate_pattern_json(
        data: Dict[str, Any],
        target_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Migrate pattern JSON to target schema version.
        
        Args:
            data: Pattern JSON data
            target_version: Target version (defaults to current)
            
        Returns:
            Migrated pattern JSON
        """
        if target_version is None:
            target_version = SchemaMigrator.CURRENT_VERSION
        
        current_version = SchemaMigrator.get_schema_version(data)
        
        if current_version == target_version:
            # Already at target version
            return data
        
        if current_version is None:
            # Legacy format - migrate to v1.0
            return SchemaMigrator._migrate_from_legacy(data, target_version)
        
        # Version-to-version migration
        # For now, only v1.0 is supported
        if target_version == "1.0":
            return SchemaMigrator._migrate_to_v1_0(data, current_version)
        
        raise ValueError(f"Unsupported target version: {target_version}")
    
    @staticmethod
    def _migrate_from_legacy(data: Dict[str, Any], target_version: str) -> Dict[str, Any]:
        """
        Migrate from legacy pattern format to schema v1.0.
        
        This handles old pattern formats that don't have schema_version.
        
        Args:
            data: Legacy pattern data
            target_version: Target version
            
        Returns:
            Migrated pattern JSON
        """
        if target_version != "1.0":
            raise ValueError(f"Can only migrate legacy to v1.0, got {target_version}")
        
        now = datetime.utcnow().isoformat() + 'Z'
        
        # Try to detect legacy format and convert
        # Assume it might have: frames, metadata, name, etc.
        migrated = {
            "schema_version": "1.0",
            "id": data.get("id") or str(uuid.uuid4()),
            "name": data.get("name", "Untitled Pattern"),
            "description": data.get("description", ""),
            "tags": data.get("tags", []),
            "created_at": data.get("created_at", now),
            "modified_at": data.get("modified_at", now),
            "matrix": {
                "width": 1,
                "height": 1,
                "layout": "row_major",
                "wiring": "linear",
                "default_color_order": "RGB"
            },
            "frames": [],
            "effects": [],
            "metadata": {}
        }
        
        # Extract matrix info if available
        if "metadata" in data:
            meta = data["metadata"]
            if isinstance(meta, dict):
                migrated["matrix"]["width"] = meta.get("width", 1)
                migrated["matrix"]["height"] = meta.get("height", 1)
                migrated["matrix"]["default_color_order"] = meta.get("color_order", "RGB")
                migrated["metadata"]["source_file"] = meta.get("source_path", "")
        
        # Convert frames
        if "frames" in data:
            frames = data["frames"]
            for idx, frame in enumerate(frames):
                if isinstance(frame, dict):
                    pixels = frame.get("pixels", [])
                    duration = frame.get("duration_ms", 100)
                    
                    # Convert to layer format
                    layer = {
                        "id": str(uuid.uuid4()),
                        "name": "base",
                        "opacity": 1.0,
                        "blend_mode": "normal",
                        "visible": True,
                        "encoding": "raw+rgb8",
                        "pixels": pixels if isinstance(pixels, list) else []
                    }
                    
                    migrated["frames"].append({
                        "index": idx,
                        "duration_ms": duration,
                        "layers": [layer]
                    })
        
        return migrated
    
    @staticmethod
    def _migrate_to_v1_0(data: Dict[str, Any], source_version: str) -> Dict[str, Any]:
        """
        Migrate from source version to v1.0.
        
        Args:
            data: Pattern JSON data
            source_version: Source schema version
            
        Returns:
            Migrated pattern JSON (v1.0)
        """
        # For now, only v1.0 exists, so this is a no-op
        # Future versions would add migration logic here
        if source_version == "1.0":
            return data
        
        raise ValueError(f"Cannot migrate from {source_version} to 1.0 (not implemented)")


# Convenience functions
def get_schema_version(data: Dict[str, Any]) -> Optional[str]:
    """Get schema version from pattern JSON"""
    return SchemaMigrator.get_schema_version(data)


def migrate_pattern_json(
    data: Dict[str, Any],
    target_version: Optional[str] = None
) -> Dict[str, Any]:
    """Migrate pattern JSON to target schema version"""
    return SchemaMigrator.migrate_pattern_json(data, target_version)


def needs_migration(data: Dict[str, Any]) -> bool:
    """Check if pattern JSON needs migration"""
    return SchemaMigrator.needs_migration(data)

