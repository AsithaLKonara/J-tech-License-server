"""
Export Service - Business logic for pattern export operations.

This service provides a clean interface for exporting patterns to various formats,
decoupling the UI layer from export logic.
"""

from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import logging
import time

from core.pattern import Pattern
from core.export.exporters import PatternExporter
from core.export.validator import ExportPreview, ExportValidationError, generate_export_preview
from core.export_options import ExportOptions
from core.events import get_event_bus
from core.events.export_events import ExportStartedEvent, ExportCompletedEvent, ExportFailedEvent
from core.errors import get_error_handler

logger = logging.getLogger(__name__)


def _get_enterprise_logger():
    """Get enterprise logger for audit and performance logging."""
    try:
        from core.logging import EnterpriseLogger
        return EnterpriseLogger.instance()
    except Exception:
        return None


class ExportService:
    """
    Service for pattern export operations.
    
    This service encapsulates business logic for exporting patterns
    to various formats (BIN, HEX, DAT, LEDS, JSON, etc.).
    """
    
    # Supported export formats
    SUPPORTED_FORMATS = ['bin', 'hex', 'dat', 'leds', 'json', 'csv', 'txt', 'ledproj', 'h', 'png_sprite', 'gif', 'wled']
    
    def __init__(self, options: Optional[ExportOptions] = None):
        """
        Initialize the export service.
        
        Args:
            options: Optional export options
        """
        self.exporter = PatternExporter(options or ExportOptions())
        self.options = options or ExportOptions()
        self.event_bus = get_event_bus()
        self.error_handler = get_error_handler()
    
    def export_pattern(
        self,
        pattern: Pattern,
        output_path: str,
        format: str,
        generate_manifest: bool = True,
        **kwargs
    ) -> Path:
        """
        Export a pattern to a file.
        
        Args:
            pattern: The pattern to export
            output_path: Path where to save the exported file
            format: Export format (bin, hex, dat, leds, json, etc.)
            generate_manifest: Whether to generate build manifest
        
        Returns:
            Path to the exported file
        
        Raises:
            ValueError: If format is not supported
            IOError: If file cannot be written
        """
        format_lower = format.lower()
        
        if format_lower not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported export format: {format}. Supported: {self.SUPPORTED_FORMATS}")
        
        logger.info(f"Exporting pattern '{pattern.name}' to {format} format: {output_path}")
        start_time = time.time()
        
        # Publish export started event
        self.event_bus.publish(ExportStartedEvent(pattern, format_lower, output_path, source="ExportService"))
        
        output_path_obj = Path(output_path)
        
        try:
            # Export based on format
            if format_lower == 'bin':
                result_path = self.exporter.export_binary(pattern, output_path_obj, generate_manifest)
            elif format_lower == 'hex':
                result_path = self.exporter.export_hex(pattern, output_path_obj, generate_manifest)
            elif format_lower == 'dat':
                result_path = self.exporter.export_dat(pattern, output_path_obj, generate_manifest)
            elif format_lower == 'leds':
                result_path = self.exporter.export_leds(pattern, output_path_obj, generate_manifest)
            elif format_lower == 'json':
                result_path = self.exporter.export_json(pattern, output_path_obj, generate_manifest)
            elif format_lower == 'csv':
                result_path = self.exporter.export_csv(pattern, output_path_obj, generate_manifest)
            elif format_lower == 'txt':
                result_path = self.exporter.export_txt(pattern, output_path_obj, generate_manifest)
            elif format_lower == 'ledproj':
                result_path = self.exporter.export_ledproj(pattern, output_path_obj, generate_manifest)
            elif format_lower == 'h':
                result_path = self.exporter.export_header(pattern, output_path_obj, generate_manifest)
            elif format_lower == 'png_sprite':
                # Get options from kwargs or use defaults
                orientation = kwargs.get('orientation', 'horizontal') if 'orientation' in kwargs else 'horizontal'
                spacing = kwargs.get('spacing', 0) if 'spacing' in kwargs else 0
                scale_factor = kwargs.get('scale_factor', 1) if 'scale_factor' in kwargs else 1
                result_path = self.exporter.export_sprite_sheet(
                    pattern,
                    output_path_obj,
                    orientation=orientation,
                    spacing=spacing,
                    scale_factor=scale_factor,
                    generate_manifest=generate_manifest
                )
            elif format_lower == 'gif':
                # Get options from kwargs or use defaults
                frame_delay_ms = kwargs.get('frame_delay_ms', 0) if 'frame_delay_ms' in kwargs else 0
                loop = kwargs.get('loop', True) if 'loop' in kwargs else True
                scale_factor = kwargs.get('scale_factor', 1) if 'scale_factor' in kwargs else 1
                result_path = self.exporter.export_gif(
                    pattern,
                    output_path_obj,
                    frame_delay_ms=frame_delay_ms,
                    loop=loop,
                    scale_factor=scale_factor,
                    generate_manifest=generate_manifest
                )
            elif format_lower == 'wled':
                result_path = self.exporter.export_wled(pattern, output_path_obj, generate_manifest)
            else:
                raise ValueError(f"Format '{format}' not yet implemented")
            
            # Audit and performance logging
            duration_ms = (time.time() - start_time) * 1000
            enterprise_logger = _get_enterprise_logger()
            if enterprise_logger:
                enterprise_logger.log_audit("pattern_exported", details={
                    'output_path': str(result_path),
                    'format': format_lower,
                    'pattern_name': pattern.name,
                    'led_count': pattern.led_count,
                    'frame_count': pattern.frame_count
                })
                enterprise_logger.log_performance("pattern_export", duration_ms, details={
                    'format': format_lower,
                    'output_path': str(result_path)
                })
            
            # Publish export completed event
            self.event_bus.publish(ExportCompletedEvent(pattern, format_lower, str(result_path), duration_ms, source="ExportService"))
            
            logger.info(f"Pattern exported successfully: {result_path}")
            return result_path
            
        except Exception as e:
            # Handle error
            duration_ms = (time.time() - start_time) * 1000
            self.error_handler.handle_export_error(e, format_lower)
            
            # Publish export failed event
            self.event_bus.publish(ExportFailedEvent(pattern, format_lower, output_path, e, source="ExportService"))
            
            # Re-raise to maintain original exception behavior
            raise
    
    def validate_export(
        self,
        pattern: Pattern,
        format: str
    ) -> Tuple[bool, Optional[str], Optional[ExportPreview]]:
        """
        Validate that a pattern can be exported in the given format.
        
        Args:
            pattern: The pattern to validate
            format: Export format to validate
        
        Returns:
            Tuple of (is_valid, error_message, export_preview)
        """
        format_lower = format.lower()
        
        if format_lower not in self.SUPPORTED_FORMATS:
            return False, f"Unsupported format: {format}", None
        
        try:
            preview = generate_export_preview(pattern, self.options, format_lower)
            return True, None, preview
        except ExportValidationError as e:
            return False, str(e), None
        except Exception as e:
            logger.error(f"Export validation error: {e}", exc_info=True)
            return False, f"Validation failed: {str(e)}", None
    
    def get_available_formats(self) -> List[str]:
        """
        Get list of available export formats.
        
        Returns:
            List of format names
        """
        return self.SUPPORTED_FORMATS.copy()
    
    def get_export_preview(
        self,
        pattern: Pattern,
        format: str
    ) -> Optional[ExportPreview]:
        """
        Get export preview for a pattern.
        
        Args:
            pattern: The pattern to preview
            format: Export format
        
        Returns:
            ExportPreview or None if preview cannot be generated
        """
        try:
            return generate_export_preview(pattern, self.options, format.lower())
        except Exception as e:
            logger.error(f"Failed to generate export preview: {e}", exc_info=True)
            return None
    
    def set_export_options(self, options: ExportOptions) -> None:
        """
        Update export options.
        
        Args:
            options: New export options
        """
        self.options = options
        self.exporter = PatternExporter(options)

