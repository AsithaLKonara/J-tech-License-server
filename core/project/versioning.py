"""
Project Version Management - Handle .ledproj version upgrades

Provides utilities for migrating project files between versions
and detecting project file versions.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import json


class ProjectVersion:
    """Project file version information"""
    
    SUPPORTED_VERSIONS = ["1.0", "1.1"]
    CURRENT_VERSION = "1.1"
    
    @staticmethod
    def get_project_version(data: Dict[str, Any]) -> Optional[str]:
        """
        Get project version from project file data.
        
        Args:
            data: Project file JSON data
            
        Returns:
            Version string or None if not present
        """
        # Check project_version in metadata
        if "metadata" in data:
            meta = data["metadata"]
            if isinstance(meta, dict):
                return meta.get("project_version")
        
        # Fallback: check top-level project_version
        return data.get("project_version")
    
    @staticmethod
    def needs_migration(data: Dict[str, Any]) -> bool:
        """
        Check if project file needs migration.
        
        Args:
            data: Project file JSON data
            
        Returns:
            True if migration is needed
        """
        version = ProjectVersion.get_project_version(data)
        if version is None:
            # Legacy format - needs migration
            return True
        return version != ProjectVersion.CURRENT_VERSION
    
    @staticmethod
    def migrate_project(
        data: Dict[str, Any],
        target_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Migrate project file to target version.
        
        Args:
            data: Project file JSON data
            target_version: Target version (defaults to current)
            
        Returns:
            Migrated project file data
        """
        if target_version is None:
            target_version = ProjectVersion.CURRENT_VERSION
        
        current_version = ProjectVersion.get_project_version(data)
        
        if current_version == target_version:
            return data
        
        # Migration chain: 1.0 -> 1.1
        if current_version == "1.0" and target_version == "1.1":
            return _migrate_1_0_to_1_1(data)
        
        if current_version is None:
            # Migrate from legacy to latest
            return _migrate_legacy_to_1_1(data)
        
        raise ValueError(f"Cannot migrate from {current_version} to {target_version}")


def _migrate_1_0_to_1_1(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate project from version 1.0 to 1.1.
    
    Changes in 1.1:
    - Added project settings structure
    - Enhanced metadata fields
    
    Args:
        data: Project file v1.0 data
        
    Returns:
        Migrated project file v1.1 data
    """
    migrated = data.copy()
    
    # Update top-level project_version
    migrated["project_version"] = "1.1"
    
    # Update metadata project_version
    if "metadata" in migrated:
        migrated["metadata"]["project_version"] = "1.1"
    else:
        migrated["metadata"] = {"project_version": "1.1"}
    
    # Ensure settings exist
    if "settings" not in migrated.get("metadata", {}):
        migrated.setdefault("metadata", {})["settings"] = {
            "auto_save": True,
            "auto_save_interval_seconds": 300,
            "undo_history_depth": 50,
            "default_zoom": 100,
            "grid_enabled": True,
            "snap_to_grid": False,
            "show_frame_numbers": True,
            "default_fps": 24.0,
            "default_color_order": "RGB",
        }
    
    return migrated


def _migrate_legacy_to_1_1(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate from legacy format to v1.1.
    
    Args:
        data: Legacy project data
        
    Returns:
        Migrated project file v1.1 data
    """
    now = datetime.utcnow().isoformat() + 'Z'
    
    migrated = {
        "project_version": "1.1",
        "schema_version": "1.0",
        "metadata": {
            "project_version": "1.1",
            "name": data.get("name", "Untitled Project"),
            "description": data.get("description", ""),
            "author": data.get("author", ""),
            "created_at": data.get("created_at", now),
            "modified_at": data.get("modified_at", now),
            "tags": data.get("tags", []),
            "category": data.get("category"),
            "license": data.get("license"),
            "settings": {
                "auto_save": True,
                "auto_save_interval_seconds": 300,
                "undo_history_depth": 50,
                "default_zoom": 100,
                "grid_enabled": True,
                "snap_to_grid": False,
                "show_frame_numbers": True,
                "default_fps": 24.0,
                "default_color_order": "RGB",
            }
        },
        "pattern": data.get("pattern", data)  # Pattern data
    }
    
    return migrated


def migrate_project(
    data: Dict[str, Any],
    target_version: Optional[str] = None
) -> Dict[str, Any]:
    """Migrate project file to target version"""
    return ProjectVersion.migrate_project(data, target_version)


def get_project_version(data: Dict[str, Any]) -> Optional[str]:
    """Get project version from project file data"""
    return ProjectVersion.get_project_version(data)


def needs_migration(data: Dict[str, Any]) -> bool:
    """Check if project file needs migration"""
    return ProjectVersion.needs_migration(data)

