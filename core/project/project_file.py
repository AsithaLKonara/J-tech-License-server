"""
Project File Handler - Atomic save/load for .ledproj files

Provides utilities for saving and loading .ledproj project files with
atomic writes (write temp + rename) to prevent corruption.
"""

import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from core.pattern import Pattern
from core.schemas.pattern_converter import PatternConverter
from core.project.project_metadata import ProjectMetadata
from core.project.versioning import ProjectVersion, migrate_project, get_project_version


class ProjectFileError(Exception):
    """Raised when project file operations fail"""
    pass


class ProjectFile:
    """Represents a .ledproj project file"""
    
    FILE_EXTENSION = ".ledproj"
    CURRENT_VERSION = "1.1"
    
    def __init__(
        self,
        pattern: Pattern,
        metadata: Optional[ProjectMetadata] = None,
        file_path: Optional[Path] = None
    ):
        """
        Initialize project file.
        
        Args:
            pattern: Pattern object
            metadata: Project metadata (creates default if None)
            file_path: Optional file path for this project
        """
        self.pattern = pattern
        self.metadata = metadata or ProjectMetadata()
        self.file_path = file_path
    
    def to_dict(self, use_rle: bool = True) -> Dict[str, Any]:
        """
        Convert project to dictionary for JSON serialization.
        
        Args:
            use_rle: Whether to use RLE compression for pixel data
            
        Returns:
            Project file dictionary
        """
        # Ensure metadata has current timestamp
        self.metadata.update_modified_time()
        
        return {
            "project_version": self.CURRENT_VERSION,
            "schema_version": "1.0",
            "metadata": self.metadata.to_dict(),
            "pattern": PatternConverter.pattern_to_json(self.pattern, use_rle=use_rle)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectFile':
        """
        Create project file from dictionary.
        
        Args:
            data: Project file dictionary
            
        Returns:
            ProjectFile object
        """
        # Migrate if needed
        if ProjectVersion.needs_migration(data):
            data = migrate_project(data)
        
        # Extract metadata
        metadata_dict = data.get("metadata", {})
        metadata = ProjectMetadata.from_dict(metadata_dict)
        
        # Extract pattern
        pattern_data = data.get("pattern", data)  # Fallback to entire data if no pattern key
        pattern = PatternConverter.pattern_from_json(pattern_data)
        
        # Ensure mapping table exists for circular layouts (regenerate if missing or invalid)
        if pattern.metadata.layout_type != "rectangular" and pattern.metadata.layout_type != "irregular":
            from core.mapping.circular_mapper import CircularMapper
            is_valid, error_msg = CircularMapper.validate_mapping_table(pattern.metadata)
            if not is_valid:
                import logging
                logging.info(
                    f"Mapping table missing or invalid for circular layout (type: {pattern.metadata.layout_type}). "
                    f"Regenerating mapping table. Error: {error_msg}"
                )
                # Regenerate mapping table
                if CircularMapper.ensure_mapping_table(pattern.metadata):
                    logging.info("Mapping table successfully regenerated.")
                else:
                    logging.warning(
                        f"Failed to regenerate mapping table for circular layout. "
                        f"Pattern may not work correctly."
                    )
        
        # Ensure active cells are initialized for irregular shapes
        if pattern.metadata.layout_type == "irregular" and getattr(pattern.metadata, 'irregular_shape_enabled', False):
            from core.mapping.irregular_shape_mapper import IrregularShapeMapper
            import logging
            import os
            
            # Initialize active cells if not set
            IrregularShapeMapper.ensure_active_cells_initialized(pattern.metadata)
            
            # Validate background image path if set
            bg_path = getattr(pattern.metadata, 'background_image_path', None)
            if bg_path and not os.path.exists(bg_path):
                logging.warning(
                    f"Background image not found for irregular shape: {bg_path}. "
                    f"Image will not be displayed."
                )
                # Clear invalid path
                pattern.metadata.background_image_path = None
        
        return cls(pattern=pattern, metadata=metadata)
    
    def save(self, file_path: Optional[Path] = None, use_rle: bool = True) -> None:
        """
        Save project to file with atomic write (write temp + rename).
        
        Args:
            file_path: Path to save file (uses self.file_path if None)
            use_rle: Whether to use RLE compression
            
        Raises:
            ProjectFileError: If save fails
        """
        if file_path is None:
            if self.file_path is None:
                raise ProjectFileError("No file path specified")
            file_path = self.file_path
        
        file_path = Path(file_path)
        
        # Ensure .ledproj extension
        if file_path.suffix != self.FILE_EXTENSION:
            file_path = file_path.with_suffix(self.FILE_EXTENSION)
        
        try:
            # Atomic save: write to temp file then rename
            temp_path = file_path.with_suffix(file_path.suffix + '.tmp')
            
            # Convert to JSON
            project_dict = self.to_dict(use_rle=use_rle)
            
            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(project_dict, f, indent=2, ensure_ascii=False)
            
            # Atomic rename (replaces existing file)
            temp_path.replace(file_path)
            
            # Update file path
            self.file_path = file_path
            
        except Exception as e:
            # Clean up temp file on error
            temp_path = file_path.with_suffix(file_path.suffix + '.tmp')
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except:
                    pass
            raise ProjectFileError(f"Failed to save project file: {e}") from e
    
    @classmethod
    def load(cls, file_path: Path) -> 'ProjectFile':
        """
        Load project from file.
        
        Args:
            file_path: Path to project file
            
        Returns:
            ProjectFile object
            
        Raises:
            ProjectFileError: If load fails
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise ProjectFileError(f"Project file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            project = cls.from_dict(data)
            project.file_path = file_path
            
            return project
            
        except json.JSONDecodeError as e:
            raise ProjectFileError(f"Invalid JSON in project file: {e}") from e
        except Exception as e:
            raise ProjectFileError(f"Failed to load project file: {e}") from e


def save_project(
    pattern: Pattern,
    file_path: Path,
    metadata: Optional[ProjectMetadata] = None,
    use_rle: bool = True
) -> None:
    """
    Save pattern as project file.
    
    Convenience function for saving a pattern as a .ledproj file.
    
    Args:
        pattern: Pattern to save
        file_path: Path to save project file
        metadata: Optional project metadata
        use_rle: Whether to use RLE compression
    """
    project = ProjectFile(pattern=pattern, metadata=metadata, file_path=file_path)
    project.save(use_rle=use_rle)


def load_project(file_path: Path) -> Tuple[Pattern, ProjectMetadata]:
    """
    Load pattern and metadata from project file.
    
    Convenience function for loading a .ledproj file.
    
    Args:
        file_path: Path to project file
        
    Returns:
        Tuple of (Pattern, ProjectMetadata)
    """
    project = ProjectFile.load(file_path)
    return project.pattern, project.metadata

