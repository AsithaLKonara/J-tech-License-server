"""
Pattern Service - Business logic for pattern operations.

This service provides a clean interface for pattern-related operations,
decoupling the UI layer from domain logic.
"""

from typing import Optional, Tuple
from pathlib import Path
import logging
import time

from core.pattern import Pattern, PatternMetadata, Frame
from parsers.parser_registry import ParserRegistry
from core.repositories.pattern_repository import PatternRepository
from core.events import get_event_bus
from core.events.pattern_events import (
    PatternCreatedEvent,
    PatternLoadedEvent,
    PatternSavedEvent,
    PatternDuplicatedEvent
)
from core.pattern_templates import TemplateLibrary

logger = logging.getLogger(__name__)


def _get_enterprise_logger():
    """Get enterprise logger for audit and performance logging."""
    try:
        from core.logging import EnterpriseLogger
        return EnterpriseLogger.instance()
    except Exception:
        return None


class PatternService:
    """
    Service for pattern operations.
    
    This service encapsulates business logic for pattern management,
    including loading, saving, creating, and validating patterns.
    """
    
    def __init__(self):
        """Initialize the pattern service."""
        self.parser_registry = ParserRegistry()
        self.repository = PatternRepository.instance()
        self.event_bus = get_event_bus()
        self.template_library = TemplateLibrary()
    
    def load_pattern(
        self,
        file_path: str,
        suggested_leds: Optional[int] = None,
        suggested_frames: Optional[int] = None
    ) -> Tuple[Pattern, str]:
        """
        Load a pattern from a file.
        
        Args:
            file_path: Path to the pattern file
            suggested_leds: Optional LED count hint
            suggested_frames: Optional frame count hint
        
        Returns:
            Tuple of (Pattern, format_name)
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file cannot be parsed
        """
        logger.info(f"Loading pattern from: {file_path}")
        start_time = time.time()
        
        # Parse file using registry
        pattern, format_name = self.parser_registry.parse_file(
            file_path,
            suggested_leds=suggested_leds,
            suggested_frames=suggested_frames
        )
        
        # Set pattern metadata
        try:
            pattern.metadata.source_format = format_name
            pattern.metadata.source_path = file_path
        except Exception:
            pass
        
        # Store in repository
        self.repository.set_current_pattern(pattern, file_path)
        
        # Publish event
        self.event_bus.publish(PatternLoadedEvent(pattern, file_path, source="PatternService"))
        
        # Audit and performance logging
        duration_ms = (time.time() - start_time) * 1000
        enterprise_logger = _get_enterprise_logger()
        if enterprise_logger:
            enterprise_logger.log_audit("pattern_loaded", details={
                'file_path': file_path,
                'format': format_name,
                'pattern_name': pattern.name,
                'led_count': pattern.led_count,
                'frame_count': pattern.frame_count
            })
            enterprise_logger.log_performance("pattern_load", duration_ms, details={
                'file_path': file_path,
                'format': format_name
            })
        
        logger.info(f"Pattern loaded: {pattern.name} ({pattern.led_count} LEDs, {pattern.frame_count} frames)")
        return pattern, format_name
    
    def save_pattern(self, pattern: Pattern, file_path: str) -> None:
        """
        Save a pattern to a file.
        
        Args:
            pattern: The pattern to save
            file_path: Path where to save the pattern
        
        Raises:
            IOError: If file cannot be written
        """
        logger.info(f"Saving pattern to: {file_path}")
        start_time = time.time()
        
        # Save pattern
        pattern.save_to_file(file_path)
        
        # Update repository
        self.repository.set_current_pattern(pattern, file_path)
        self.repository.set_dirty(False)
        
        # Publish event
        self.event_bus.publish(PatternSavedEvent(pattern, file_path, source="PatternService"))
        
        # Audit and performance logging
        duration_ms = (time.time() - start_time) * 1000
        enterprise_logger = _get_enterprise_logger()
        if enterprise_logger:
            enterprise_logger.log_audit("pattern_saved", details={
                'file_path': file_path,
                'pattern_name': pattern.name,
                'led_count': pattern.led_count,
                'frame_count': pattern.frame_count
            })
            enterprise_logger.log_performance("pattern_save", duration_ms, details={
                'file_path': file_path
            })
        
        logger.info(f"Pattern saved: {file_path}")
    
    def create_pattern(
        self,
        name: str = "Untitled Pattern",
        width: int = 72,
        height: int = 1,
        metadata: Optional[PatternMetadata] = None
    ) -> Pattern:
        """
        Create a new blank pattern.
        
        Args:
            name: Pattern name
            width: Matrix width (LEDs)
            height: Matrix height (LEDs)
            metadata: Optional metadata to use
        
        Returns:
            New Pattern instance
        """
        logger.info(f"Creating new pattern: {name} ({width}x{height})")
        
        # Create metadata if not provided
        if metadata is None:
            metadata = PatternMetadata(width=width, height=height)
        
        # Create pattern
        pattern = Pattern(name=name, metadata=metadata, frames=[])
        
        # Store in repository
        self.repository.set_current_pattern(pattern, None)
        
        # Publish event
        self.event_bus.publish(PatternCreatedEvent(pattern, source="PatternService"))
        
        # Audit logging
        enterprise_logger = _get_enterprise_logger()
        if enterprise_logger:
            enterprise_logger.log_audit("pattern_created", details={
                'pattern_name': name,
                'width': width,
                'height': height
            })
        
        logger.info(f"Pattern created: {pattern.name}")
        return pattern
    
    def duplicate_pattern(self, pattern: Pattern, new_name: Optional[str] = None) -> Pattern:
        """
        Create a duplicate of a pattern.
        
        Args:
            pattern: The pattern to duplicate
            new_name: Optional name for the duplicate
        
        Returns:
            Duplicated Pattern instance
        """
        logger.info(f"Duplicating pattern: {pattern.name}")
        
        # Create deep copy
        import copy
        duplicated = copy.deepcopy(pattern)
        
        # Set new name
        if new_name:
            duplicated.name = new_name
        else:
            duplicated.name = f"{pattern.name} (Copy)"
        
        # Generate new ID
        import uuid
        duplicated.id = str(uuid.uuid4())
        
        # Publish event
        self.event_bus.publish(PatternDuplicatedEvent(pattern, duplicated, source="PatternService"))
        
        # Audit logging
        enterprise_logger = _get_enterprise_logger()
        if enterprise_logger:
            enterprise_logger.log_audit("pattern_duplicated", details={
                'original_name': pattern.name,
                'new_name': duplicated.name,
                'led_count': pattern.led_count,
                'frame_count': pattern.frame_count
            })
        
        logger.info(f"Pattern duplicated: {duplicated.name}")
        return duplicated
    
    def validate_pattern(self, pattern: Pattern) -> Tuple[bool, Optional[str]]:
        """
        Validate a pattern.
        
        Args:
            pattern: The pattern to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check pattern has frames
        if not pattern.frames:
            return False, "Pattern has no frames"
        
        # Check all frames have correct LED count
        expected_leds = pattern.metadata.led_count
        for i, frame in enumerate(pattern.frames):
            if frame.led_count != expected_leds:
                return False, f"Frame {i} has {frame.led_count} LEDs, expected {expected_leds}"
        
        # Check metadata
        if pattern.metadata.width < 1 or pattern.metadata.height < 1:
            return False, "Invalid pattern dimensions"
        
        return True, None
    
    def get_current_pattern(self) -> Optional[Pattern]:
        """
        Get the current pattern from repository.
        
        Returns:
            Current pattern or None
        """
        return self.repository.get_current_pattern()
    
    def set_current_pattern(self, pattern: Pattern, file_path: Optional[str] = None) -> None:
        """
        Set the current pattern in repository.
        
        Args:
            pattern: The pattern to set
            file_path: Optional file path
        """
        self.repository.set_current_pattern(pattern, file_path)
    
    def clear_pattern(self) -> None:
        """
        Clear the current pattern.
        """
        self.repository.clear_pattern()
    
    def is_dirty(self) -> bool:
        """
        Check if current pattern has unsaved changes.
        
        Returns:
            True if pattern is dirty
        """
        return self.repository.is_dirty()
    
    def set_dirty(self, dirty: bool = True) -> None:
        """
        Mark current pattern as dirty.
        
        Args:
            dirty: True to mark as dirty
        """
        self.repository.set_dirty(dirty)
    
    def generate_from_template(
        self,
        template_name: str,
        width: int,
        height: int,
        **template_params
    ) -> Pattern:
        """
        Generate a pattern from a template.
        
        Args:
            template_name: Name of the template
            width: Matrix width
            height: Matrix height
            **template_params: Template-specific parameters
        
        Returns:
            Generated Pattern instance
        
        Raises:
            ValueError: If template not found or generation fails
        """
        logger.info(f"Generating pattern from template: {template_name} ({width}x{height})")
        start_time = time.time()
        
        try:
            # Generate pattern from template
            pattern = self.template_library.generate_pattern(
                template_name,
                width,
                height,
                **template_params
            )
            
            # Store in repository
            self.repository.set_current_pattern(pattern, None)
            
            # Publish event
            self.event_bus.publish(PatternCreatedEvent(pattern, source="PatternService.template"))
            
            # Audit and performance logging
            duration_ms = (time.time() - start_time) * 1000
            enterprise_logger = _get_enterprise_logger()
            if enterprise_logger:
                enterprise_logger.log_audit("pattern_generated_from_template", details={
                    'template_name': template_name,
                    'pattern_name': pattern.name,
                    'width': width,
                    'height': height,
                    'frame_count': pattern.frame_count
                })
                enterprise_logger.log_performance("template_generation", duration_ms, details={
                    'template_name': template_name
                })
            
            logger.info(f"Pattern generated from template: {pattern.name}")
            return pattern
            
        except Exception as e:
            logger.error(f"Failed to generate pattern from template: {e}", exc_info=True)
            raise ValueError(f"Failed to generate pattern from template '{template_name}': {str(e)}")
    
    def list_templates(self, category=None):
        """
        List available templates.
        
        Args:
            category: Optional category filter
        
        Returns:
            List of PatternTemplate instances
        """
        return self.template_library.list_templates(category)
    
    def get_template(self, name: str):
        """
        Get a template by name.
        
        Args:
            name: Template name
        
        Returns:
            PatternTemplate or None
        """
        return self.template_library.get_template(name)

