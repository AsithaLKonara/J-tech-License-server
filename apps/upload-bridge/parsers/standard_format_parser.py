"""
Standard Format Parser - Parses header-based binary format
Real implementation using new Pattern model
"""

import struct
from typing import Optional
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.pattern import Pattern, Frame, PatternMetadata
from core.dimension_scorer import pick_best_layout
from .base_parser import ParserBase


class StandardFormatParser(ParserBase):
    """
    Parser for standard binary format with header
    
    Format:
    -------
    Offset 0-1: num_leds (uint16, little-endian)
    Offset 2-3: num_frames (uint16, little-endian)
    
    Then for each frame:
      Offset 0-1: delay_ms (uint16, little-endian)
      Offset 2+: RGB data (3 bytes per LED)
    """
    
    def get_format_name(self) -> str:
        return "Standard Binary Format"
    
    def get_format_description(self) -> str:
        return (
            "Binary format with 4-byte header (num_leds, num_frames), "
            "followed by frames with 2-byte delay and RGB data"
        )
    
    def detect(self, data: bytes, filename: str = "",
               suggested_leds: Optional[int] = None,
               suggested_frames: Optional[int] = None) -> bool:
        """Detect if data matches standard format"""
        
        # Need at least header
        if len(data) < 4:
            return False
        
        try:
            # Read header
            num_leds = struct.unpack('<H', data[0:2])[0]
            num_frames = struct.unpack('<H', data[2:4])[0]

            # Sanity checks
            if num_leds == 0 or num_leds > 10000:
                return False
            if num_frames == 0 or num_frames > 100000:
                return False

            # Exact structure check: header (4) + frames * (2 + 3*leds)
            actual_size = len(data)
            bytes_per_frame = 2 + num_leds * 3
            payload_size = actual_size - 4

            if payload_size < 0:
                return False

            # Must divide evenly and match the header's frame count
            if payload_size % bytes_per_frame != 0:
                return False

            computed_frames = payload_size // bytes_per_frame
            if computed_frames != num_frames:
                return False

            # All checks passed: this is a valid standard binary file
            return True

        except (struct.error, IndexError, ValueError) as e:
            logging.debug(f"Failed to validate standard format: {e}")
        
        return False
    
    def get_confidence(self, data: bytes) -> float:
        """Calculate confidence score"""
        if not self.detect(data, ""):
            return 0.0
        
        try:
            num_leds = struct.unpack('<H', data[0:2])[0]
            num_frames = struct.unpack('<H', data[2:4])[0]
            bytes_per_frame = 2 + num_leds * 3
            payload = len(data) - 4
            if payload >= 0 and payload % bytes_per_frame == 0 and (payload // bytes_per_frame) == num_frames:
                return 1.0
            return 0.0
        except (struct.error, IndexError, ValueError) as e:
            logging.debug(f"Error calculating confidence: {e}")
    
    def parse(self, data: bytes,
              suggested_leds: Optional[int] = None,
              suggested_frames: Optional[int] = None) -> Pattern:
        """Parse standard format into Pattern"""
        
        if len(data) < 4:
            raise ValueError("File too small for standard format")
        
        # Read header
        num_leds = struct.unpack('<H', data[0:2])[0]
        num_frames = struct.unpack('<H', data[2:4])[0]
        
        if num_leds == 0 or num_leds > 10000:
            raise ValueError(f"Invalid LED count: {num_leds}")
        
        if num_frames == 0 or num_frames > 100000:
            raise ValueError(f"Invalid frame count: {num_frames}")
        
        # Parse frames
        frames = []
        offset = 4
        bytes_per_frame = 2 + num_leds * 3
        
        for frame_idx in range(num_frames):
            if offset + bytes_per_frame > len(data):
                # Incomplete frame - use what we have
                break
            
            # Read delay
            delay_ms = struct.unpack('<H', data[offset:offset+2])[0]
            offset += 2
            
            # Read RGB data
            pixels = []
            for led_idx in range(num_leds):
                if offset + 3 > len(data):
                    break
                
                r = data[offset]
                g = data[offset + 1]
                b = data[offset + 2]
                offset += 3
                
                pixels.append((r, g, b))
            
            # Only add frame if we got all LEDs
            if len(pixels) == num_leds:
                frames.append(Frame(pixels=pixels, duration_ms=max(1, delay_ms)))
        
        if not frames:
            raise ValueError("No valid frames found in file")
        
        guess = pick_best_layout(
            num_leds,
            frames[0].pixels,
            include_strips=True
        )
        dimension_source = "detector"
        dimension_confidence = 0.0
        if guess:
            width_guess, height_guess, score = guess
            dimension_confidence = score
        else:
            width_guess, height_guess = num_leds, 1
            dimension_source = "fallback"
            dimension_confidence = 0.2

        # Create Pattern
        metadata = PatternMetadata(
            width=width_guess,
            height=height_guess,
            color_order="RGB",
            dimension_source=dimension_source,
            dimension_confidence=dimension_confidence
        )
        
        pattern = Pattern(
            name="Imported Pattern",
            metadata=metadata,
            frames=frames
        )
        
        return pattern

