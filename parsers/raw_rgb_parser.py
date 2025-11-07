"""
Raw RGB Parser - Parses headerless RGB data
Real implementation - handles your p1.bin format!
"""

from typing import Optional
import sys
sys.path.insert(0, str(__file__ + "/../../.."))

from core.pattern import Pattern, Frame, PatternMetadata
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
        width_guess, height_guess = self._choose_matrix_dimensions(num_leds)

        # Create Pattern
        metadata = PatternMetadata(
            width=width_guess,
            height=height_guess,
            color_order="RGB"
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
        
        # Common LED counts to try (include frequently used matrices/strips)
        common_led_counts = [
            64,   # 8×8 matrix
            72,   # 12×6 matrix (common)
            76,   # custom/common use case
            96,   # 12×8 matrix
            100,  # Common strip
            120,  # 12×10 matrix
            144,  # 12×12 matrix
            150,  # Common strip
            160,  # 16×10 matrix
            192,  # 16×12 matrix
            256,  # 16×16 matrix
            300,  # Large strip
            320,  # Common
            400,  # Very large
            512   # Max common
        ]

        # Collect all plausible candidates and prefer those with reasonable frame counts
        candidates = []  # (led_count, frames, score)
        for led_count in common_led_counts:
            if total_pixels % led_count == 0:
                frames = total_pixels // led_count
                if frames >= 2:
                    score = 0
                    # Prefer animations with more frames in a typical range
                    if 10 <= frames <= 240:
                        score += 3
                    elif 5 <= frames <= 480:
                        score += 2
                    else:
                        score += 1
                    candidates.append((led_count, frames, score))

        if candidates:
            # Prefer highest score, then more frames (to avoid misreading as fewer frames with larger LED count)
            candidates.sort(key=lambda x: (x[2], x[1]), reverse=True)
            best_leds, best_frames, _ = candidates[0]
            return (best_leds, best_frames)
        
        # Try factorization for square matrices
        import math
        sqrt = int(math.sqrt(total_pixels))
        if sqrt * sqrt == total_pixels:
            # Perfect square - could be a square matrix animation
            # Assume 1 frame
            return (total_pixels, 1)
        
        # No good match found
        return (None, None)

    def _choose_matrix_dimensions(self, led_count: int) -> tuple[int, int]:
        """Pick a friendly matrix width×height for a given LED count.
        Heuristics:
        - Prefer width 12, 16, 8, 10 when divisible
        - Otherwise choose the factor pair closest to square with width >= height
        - Fallback to strip (width=led_count, height=1)
        """
        preferred_widths = [12, 16, 8, 10, 20, 24, 32]
        for w in preferred_widths:
            if led_count % w == 0:
                h = led_count // w
                if h >= 1:
                    return (w, h)

        # Choose factor pair closest to square
        best = (led_count, 1)
        best_diff = led_count  # large
        for h in range(1, int(led_count ** 0.5) + 1):
            if led_count % h == 0:
                w = led_count // h
                # prefer w >= h
                if w < h:
                    w, h = h, w
                diff = abs(w - h)
                if diff < best_diff:
                    best = (w, h)
                    best_diff = diff
        return best

