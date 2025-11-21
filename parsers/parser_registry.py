"""
Parser Registry - Auto-detects and dispatches to correct parser
Real implementation with confidence scoring
"""

from typing import Optional, List, Tuple
from pathlib import Path
import sys
sys.path.insert(0, str(__file__ + "/../../.."))
import logging

logger = logging.getLogger(__name__)

from core.pattern import Pattern
from .base_parser import ParserBase
from .standard_format_parser import StandardFormatParser
from .raw_rgb_parser import RawRGBParser
from .intel_hex_parser import IntelHexParser
from .enhanced_binary_parser import EnhancedBinaryParser


class ParserRegistry:
    """
    Registry of all available parsers with auto-detection
    """
    
    def __init__(self):
        """Initialize with all available parsers"""
        self.parsers: List[ParserBase] = [
            StandardFormatParser(),
            IntelHexParser(),
            EnhancedBinaryParser(),  # Enhanced binary parser for large files
            RawRGBParser()  # Last because it's least specific
        ]
    
    def detect_format(self, data: bytes, filename: str = "",
                     suggested_leds: Optional[int] = None,
                     suggested_frames: Optional[int] = None) -> Optional[ParserBase]:
        """
        Auto-detect which parser can handle this data
        
        Args:
            data: Raw file bytes
            filename: Original filename (for hint)
            suggested_leds: User-provided LED count
            suggested_frames: User-provided frame count
        
        Returns:
            Best matching parser or None
        """
        
        # Score all parsers
        scores = []
        
        for parser in self.parsers:
            try:
                if parser.detect(data, filename, suggested_leds, suggested_frames):
                    confidence = parser.get_confidence(data)
                    scores.append((parser, confidence))
            except:
                pass
        
        if not scores:
            return None
        
        # Return parser with highest confidence
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[0][0]
    
    def parse_file(self, filepath: str,
                   suggested_leds: Optional[int] = None,
                   suggested_frames: Optional[int] = None) -> Tuple[Pattern, str]:
        """
        Parse pattern file with auto-detection
        
        Args:
            filepath: Path to pattern file
            suggested_leds: User-provided LED count
            suggested_frames: User-provided frame count
        
        Returns:
            Tuple of (Pattern, format_name)
        
        Raises:
            ValueError: If file cannot be parsed
        """
        
        # Read file
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        with open(filepath, 'rb') as f:
            data = f.read()
        
        if not data:
            raise ValueError("File is empty")
        
        # Detect format
        parser = self.detect_format(data, path.name, suggested_leds, suggested_frames)
        
        if not parser:
            raise ValueError(
                f"Unknown format: {path.name}\n"
                f"File size: {len(data)} bytes\n"
                "Try specifying LED count and frame count manually."
            )
        
        # Parse
        try:
            pattern = parser.parse(data, suggested_leds, suggested_frames)
            format_name = parser.get_format_name()
            
            # Set pattern name from filename
            pattern.name = path.stem
            
            # Extract wiring hints from filename and set on pattern metadata
            from core.filename_hints import extract_wiring_hints
            wiring_hint, corner_hint, hint_confidence = extract_wiring_hints(path.name)
            if wiring_hint:
                pattern.metadata.wiring_mode_hint = wiring_hint
            if corner_hint:
                pattern.metadata.data_in_corner_hint = corner_hint
            if hint_confidence > 0:
                pattern.metadata.hint_confidence = hint_confidence
            
            # Set source path for debugging
            pattern.metadata.source_path = str(path)
            pattern.metadata.source_format = format_name.lower()
            
            return (pattern, format_name)
        
        except Exception as e:
            raise ValueError(
                f"Failed to parse as {parser.get_format_name()}: {str(e)}"
            )
    
    def list_supported_formats(self) -> List[Tuple[str, str]]:
        """
        Get list of supported formats
        
        Returns:
            List of (format_name, description) tuples
        """
        return [
            (parser.get_format_name(), parser.get_format_description())
            for parser in self.parsers
        ]
    
    def validate_file(self, filepath: str) -> Tuple[bool, str, dict]:
        """
        Validate pattern file without fully parsing
        
        Args:
            filepath: Path to pattern file
        
        Returns:
            Tuple of (is_valid, message, info_dict)
        """
        
        try:
            path = Path(filepath)
            
            if not path.exists():
                return (False, "File not found", {})
            
            with open(filepath, 'rb') as f:
                data = f.read()
            
            if not data:
                return (False, "File is empty", {})
            
            # Try to detect format
            parser = self.detect_format(data, path.name)
            
            if not parser:
                return (False, "Unknown format", {
                    "file_size": len(data),
                    "filename": path.name
                })
            
            info = {
                "file_size": len(data),
                "format": parser.get_format_name(),
                "confidence": parser.get_confidence(data),
                "filename": path.name
            }
            
            # Try to extract dimensions if possible
            try:
                # Quick parse attempt
                pattern = parser.parse(data)
                info["leds"] = pattern.led_count
                info["frames"] = pattern.frame_count
                info["duration_ms"] = pattern.duration_ms
                info["fps"] = round(pattern.average_fps, 1)
            except:
                pass
            
            message = f"Valid {parser.get_format_name()}"
            if "leds" in info:
                message += f" - {info['leds']} LEDs, {info['frames']} frames"
            
            return (True, message, info)
        
        except Exception as e:
            return (False, f"Validation error: {str(e)}", {})


# Global registry instance
_registry = None

def get_registry() -> ParserRegistry:
    """Get global parser registry instance"""
    global _registry
    if _registry is None:
        _registry = ParserRegistry()
    return _registry


def parse_pattern_file(filepath: str,
                      suggested_leds: Optional[int] = None,
                      suggested_frames: Optional[int] = None) -> Pattern:
    """
    Convenience function to parse pattern file
    
    Args:
        filepath: Path to pattern file
        suggested_leds: Optional LED count
        suggested_frames: Optional frame count
    
    Returns:
        Pattern object
    """
    registry = get_registry()
    pattern, format_name = registry.parse_file(filepath, suggested_leds, suggested_frames)
    logger.info("Loaded pattern from %s", format_name)
    return pattern

