"""
Project Metadata Model - Extended metadata for LED pattern projects

Defines metadata structures for .ledproj files including project settings,
tags, author information, and project-specific configurations.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from core.pattern import Frame
from core.schemas.pattern_converter import PatternConverter


@dataclass
class ProjectSettings:
    """Project-specific settings and preferences"""
    auto_save: bool = True
    auto_save_interval_seconds: int = 300  # 5 minutes
    undo_history_depth: int = 50
    default_zoom: int = 100  # Percentage
    grid_enabled: bool = True
    snap_to_grid: bool = False
    show_frame_numbers: bool = True
    default_fps: float = 24.0
    default_color_order: str = "RGB"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "auto_save": self.auto_save,
            "auto_save_interval_seconds": self.auto_save_interval_seconds,
            "undo_history_depth": self.undo_history_depth,
            "default_zoom": self.default_zoom,
            "grid_enabled": self.grid_enabled,
            "snap_to_grid": self.snap_to_grid,
            "show_frame_numbers": self.show_frame_numbers,
            "default_fps": self.default_fps,
            "default_color_order": self.default_color_order,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectSettings':
        """Create from dictionary"""
        return cls(
            auto_save=data.get("auto_save", True),
            auto_save_interval_seconds=data.get("auto_save_interval_seconds", 300),
            undo_history_depth=data.get("undo_history_depth", 50),
            default_zoom=data.get("default_zoom", 100),
            grid_enabled=data.get("grid_enabled", True),
            snap_to_grid=data.get("snap_to_grid", False),
            show_frame_numbers=data.get("show_frame_numbers", True),
            default_fps=data.get("default_fps", 24.0),
            default_color_order=data.get("default_color_order", "RGB"),
        )


@dataclass
class ProjectMetadata:
    """Project metadata for .ledproj files"""
    project_version: str = "1.0"
    name: str = "Untitled Project"
    description: str = ""
    author: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + 'Z')
    modified_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + 'Z')
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None
    license: Optional[str] = None
    thumbnail_path: Optional[str] = None
    settings: ProjectSettings = field(default_factory=ProjectSettings)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)
    frame_presets: List[Dict[str, Any]] = field(default_factory=list)  # Saved frame presets
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "project_version": self.project_version,
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "tags": self.tags,
            "category": self.category,
            "license": self.license,
            "thumbnail_path": self.thumbnail_path,
            "settings": self.settings.to_dict(),
            "custom_metadata": self.custom_metadata,
            "frame_presets": self.frame_presets,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectMetadata':
        """Create from dictionary"""
        settings_data = data.get("settings", {})
        return cls(
            project_version=data.get("project_version", "1.0"),
            name=data.get("name", "Untitled Project"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            created_at=data.get("created_at", datetime.utcnow().isoformat() + 'Z'),
            modified_at=data.get("modified_at", datetime.utcnow().isoformat() + 'Z'),
            tags=data.get("tags", []),
            category=data.get("category"),
            license=data.get("license"),
            thumbnail_path=data.get("thumbnail_path"),
            settings=ProjectSettings.from_dict(settings_data),
            custom_metadata=data.get("custom_metadata", {}),
            frame_presets=data.get("frame_presets", []),
        )
    
    def update_modified_time(self):
        """Update modified_at timestamp"""
        self.modified_at = datetime.utcnow().isoformat() + 'Z'

