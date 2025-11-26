"""
Pattern Versioning - Track pattern versions and changes
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
import json
import logging

from core.pattern import Pattern

logger = logging.getLogger(__name__)


@dataclass
class PatternVersion:
    """Represents a version of a pattern."""
    version_id: str
    timestamp: str
    description: str
    pattern_snapshot: Dict[str, Any]  # Serialized pattern data
    metadata: Dict[str, Any]  # Additional metadata (author, notes, etc.)


class PatternVersionManager:
    """Manages pattern versions and history."""
    
    def __init__(self, max_versions: int = 50):
        """
        Initialize version manager.
        
        Args:
            max_versions: Maximum number of versions to keep (default: 50)
        """
        self._versions: List[PatternVersion] = []
        self._max_versions = max_versions
    
    def create_version(self, pattern: Pattern, description: str = "", metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new version from a pattern.
        
        Args:
            pattern: Pattern to version
            description: Optional description of changes
            metadata: Optional additional metadata
            
        Returns:
            Version ID
        """
        version_id = f"v{len(self._versions) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        timestamp = datetime.now().isoformat()
        
        # Serialize pattern
        pattern_snapshot = self._serialize_pattern(pattern)
        
        version = PatternVersion(
            version_id=version_id,
            timestamp=timestamp,
            description=description or f"Version {len(self._versions) + 1}",
            pattern_snapshot=pattern_snapshot,
            metadata=metadata or {}
        )
        
        self._versions.append(version)
        
        # Trim old versions if exceeding max
        if len(self._versions) > self._max_versions:
            self._versions = self._versions[-self._max_versions:]
        
        return version_id
    
    def get_versions(self) -> List[PatternVersion]:
        """Get all versions."""
        return self._versions.copy()
    
    def get_version(self, version_id: str) -> Optional[PatternVersion]:
        """Get a specific version by ID."""
        for version in self._versions:
            if version.version_id == version_id:
                return version
        return None
    
    def restore_version(self, version_id: str) -> Optional[Pattern]:
        """
        Restore a pattern from a version.
        
        Args:
            version_id: Version ID to restore
            
        Returns:
            Restored Pattern or None if version not found
        """
        version = self.get_version(version_id)
        if version is None:
            return None
        
        return self._deserialize_pattern(version.pattern_snapshot)
    
    def get_latest_version(self) -> Optional[PatternVersion]:
        """Get the latest version."""
        if not self._versions:
            return None
        return self._versions[-1]
    
    def clear_versions(self):
        """Clear all versions."""
        self._versions.clear()
    
    def _serialize_pattern(self, pattern: Pattern) -> Dict[str, Any]:
        """
        Serialize pattern to dictionary using Pattern's built-in serialization.
        
        This preserves ALL metadata including:
        - Dimension detection metadata (dimension_source, dimension_confidence)
        - Wiring hints (wiring_mode_hint, data_in_corner_hint, hint_confidence)
        - Source information (source_format, source_path)
        - All frame pixel data
        - Scratchpads
        - LMS instructions
        """
        # Use Pattern's built-in to_dict() method which preserves all metadata
        return pattern.to_dict()
    
    def _deserialize_pattern(self, snapshot: Dict[str, Any]) -> Optional[Pattern]:
        """
        Deserialize pattern from dictionary using Pattern's built-in deserialization.
        
        This restores the full pattern including all metadata fields.
        """
        try:
            # Use Pattern's built-in from_dict() method which handles all metadata
            # This preserves dimension_source, dimension_confidence, wiring hints, etc.
            # The from_dict() method carefully reconstructs all metadata fields
            pattern = Pattern.from_dict(snapshot)
            
            # Verify critical metadata was preserved
            if not hasattr(pattern, 'metadata'):
                logger.warning("Restored pattern missing metadata")
                return None
            
            # Verify dimension metadata is preserved
            if not hasattr(pattern.metadata, 'dimension_source'):
                logger.warning("Restored pattern missing dimension_source")
            if not hasattr(pattern.metadata, 'dimension_confidence'):
                logger.warning("Restored pattern missing dimension_confidence")
            
            return pattern
        except KeyError as e:
            # Missing required field in snapshot
            logger.error(f"Pattern version snapshot missing required field: {e}")
            return None
        except ValueError as e:
            # Invalid data in snapshot
            logger.error(f"Pattern version snapshot contains invalid data: {e}")
            return None
        except Exception as e:
            # Unexpected error
            logger.error(f"Failed to deserialize pattern version: {e}", exc_info=True)
            return None


class AutoVersionManager:
    """Automatic version manager that creates versions on pattern changes."""
    
    def __init__(self, version_manager: PatternVersionManager, auto_save_interval_seconds: int = 300):
        """
        Initialize auto version manager.
        
        Args:
            version_manager: PatternVersionManager instance
            auto_save_interval_seconds: Interval between auto-saves (default: 5 minutes)
        """
        self._version_manager = version_manager
        self._auto_save_interval = auto_save_interval_seconds
        self._last_auto_save: Optional[datetime] = None
        self._pattern_hash: Optional[str] = None
    
    def should_auto_save(self, pattern: Pattern) -> bool:
        """
        Check if pattern should be auto-saved.
        
        Args:
            pattern: Current pattern
            
        Returns:
            True if auto-save should occur
        """
        if self._last_auto_save is None:
            return True
        
        # Check time interval
        elapsed = (datetime.now() - self._last_auto_save).total_seconds()
        if elapsed < self._auto_save_interval:
            return False
        
        # Check if pattern has changed (simple hash comparison)
        current_hash = self._hash_pattern(pattern)
        if current_hash == self._pattern_hash:
            return False
        
        return True
    
    def auto_save(self, pattern: Pattern) -> Optional[str]:
        """
        Auto-save pattern version if needed.
        
        Args:
            pattern: Pattern to save
            
        Returns:
            Version ID if saved, None otherwise
        """
        if not self.should_auto_save(pattern):
            return None
        
        version_id = self._version_manager.create_version(
            pattern,
            description="Auto-saved version",
            metadata={"auto_save": True}
        )
        
        self._last_auto_save = datetime.now()
        self._pattern_hash = self._hash_pattern(pattern)
        
        return version_id
    
    def _hash_pattern(self, pattern: Pattern) -> str:
        """Generate a simple hash for pattern (for change detection)."""
        # Simple hash based on frame count and dimensions
        # In production, use proper hash of pattern content
        return f"{pattern.metadata.width}x{pattern.metadata.height}_{len(pattern.frames)}"

