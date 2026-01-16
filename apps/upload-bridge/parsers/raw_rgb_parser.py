"""
Raw RGB Parser - Parses headerless RGB data
Real implementation - handles your p1.bin format!
"""

from typing import Optional
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.pattern import Pattern, Frame, PatternMetadata
from core.dimension_scorer import (
    pick_best_layout,
    infer_leds_and_frames,
    COMMON_LED_COUNTS,
)
from .base_parser import ParserBase


class RawRGBParser(ParserBase):
    """
    Parser for raw RGB data with no header
    
    Format:
    -------
    Pure RGB bytes: R G B R G B R G B ...
    No header, no frame delimiters
    
    Requires:
    - User to specify LED count AND frame count OR
    - Auto-detection based on file size
    """
    
    def get_format_name(self) -> str:
        return "Raw RGB Binary"
    
    def get_format_description(self) -> str:
        return (
            "Pure RGB data with no header. "
            "File size must be divisible by 3. "
            "Requires LED count and frame count to be specified."
        )
    
    def detect(self, data: bytes, filename: str = "",
               suggested_leds: Optional[int] = None,
               suggested_frames: Optional[int] = None) -> bool:
        """Detect if data is raw RGB"""
        
        # Must be divisible by 3
        if len(data) % 3 != 0:
            return False
        
        # If we have suggestions, validate them
        if suggested_leds and suggested_frames:
            total_pixels = len(data) // 3
            expected_pixels = suggested_leds * suggested_frames
            
            if total_pixels == expected_pixels:
                return True
        
        # Without suggestions, we can only check if it's plausible
        # Look for some variation in the data (not all zeros/all 255)
        if len(data) >= 300:
            sample = data[:300]
            unique_values = len(set(sample))
            
            # If we see at least 10 different byte values, probably RGB data
            if unique_values >= 10:
                return True
        
        return False
    
    def get_confidence(self, data: bytes) -> float:
        """Calculate confidence for raw RGB detection"""
        if not self.detect(data, ""):
            return 0.0
        
        # Raw RGB is low confidence without explicit user confirmation
        # because many formats could match
        
        # Check data variation
        if len(data) >= 300:
            sample = data[:300]
            unique_values = len(set(sample))
            
            # More variation = higher confidence it's actual image data
            if unique_values > 50:
                return 0.4  # Medium-low confidence
            elif unique_values > 20:
                return 0.3
            else:
                return 0.1  # Very low confidence
        
        return 0.2  # Default low confidence
    
    def parse(self, data: bytes,
              suggested_leds: Optional[int] = None,
              suggested_frames: Optional[int] = None) -> Pattern:
        """Parse raw RGB data into Pattern"""
        
        # Check if divisible by 3
        if len(data) % 3 != 0:
            raise ValueError(
                f"File size ({len(data)} bytes) not divisible by 3. "
                "Not valid RGB data."
            )
        
        total_pixels = len(data) // 3
        
        # Determine LED count and frame count
        num_leds = None
        num_frames = None
        
        if suggested_leds and suggested_frames:
            # Both specified - validate
            if suggested_leds * suggested_frames == total_pixels:
                num_leds = suggested_leds
                num_frames = suggested_frames
            else:
                raise ValueError(
                    f"Specified {suggested_leds} LEDs × {suggested_frames} frames "
                    f"= {suggested_leds * suggested_frames} pixels, "
                    f"but file has {total_pixels} pixels"
                )
        
        elif suggested_leds:
            # Only LEDs specified - calculate frames
            if total_pixels % suggested_leds == 0:
                num_leds = suggested_leds
                num_frames = total_pixels // suggested_leds
            else:
                raise ValueError(
                    f"Total pixels ({total_pixels}) not divisible by "
                    f"LED count ({suggested_leds})"
                )
        
        elif suggested_frames:
            # Only frames specified - calculate LEDs
            if total_pixels % suggested_frames == 0:
                num_frames = suggested_frames
                num_leds = total_pixels // suggested_frames
            else:
                raise ValueError(
                    f"Total pixels ({total_pixels}) not divisible by "
                    f"frame count ({suggested_frames})"
                )
        
        else:
            # No suggestions - try common LED counts
            num_leds, num_frames = self._auto_detect_dimensions(total_pixels)
            
            if not num_leds or not num_frames:
                raise ValueError(
                    f"Cannot auto-detect dimensions for {total_pixels} pixels. "
                    "Please specify LED count and/or frame count."
                )
        
        # Parse frames
        frames = []
        bytes_per_frame = num_leds * 3
        
        for frame_idx in range(num_frames):
            offset = frame_idx * bytes_per_frame
            if offset + bytes_per_frame > len(data):
                raise ValueError(
                    f"Raw RGB data truncated before frame {frame_idx}; "
                    "provide correct LED/frame counts or verify file integrity."
                )
            pixels = []
            
            for led_idx in range(num_leds):
                pixel_offset = offset + led_idx * 3
                r = data[pixel_offset]
                g = data[pixel_offset + 1]
                b = data[pixel_offset + 2]
                pixels.append((r, g, b))
            
            # Default 20ms per frame (50 FPS)
            frames.append(Frame(pixels=pixels, duration_ms=20))
        
        # Infer a plausible matrix layout for display (e.g., 12×6 instead of 72×1)
        first_pixels = frames[0].pixels if frames else None
        guess = pick_best_layout(
            num_leds,
            first_pixels,
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
            name="Raw RGB Import",
            metadata=metadata,
            frames=frames
        )
        
        return pattern
    
    def _auto_detect_dimensions(self, total_pixels: int) -> tuple[Optional[int], Optional[int]]:
        """
        Try to auto-detect LED count and frame count
        
        Returns:
            Tuple of (num_leds, num_frames) or (None, None) if can't detect
        """
        
        resolution = infer_leds_and_frames(
            total_pixels,
            include_strips=True,
            preferred_led_counts=COMMON_LED_COUNTS,
        )
        if resolution:
            return (resolution.led_count, resolution.frames)
        return (None, None)

