"""
Enhanced Binary Parser - Handles large binary pattern files
Supports multiple binary formats with auto-detection
"""

from typing import Optional, Tuple, List
import struct
import sys
sys.path.insert(0, str(__file__ + "/../../.."))

from core.pattern import Pattern, Frame, PatternMetadata
from .base_parser import ParserBase


class EnhancedBinaryParser(ParserBase):
    """
    Enhanced parser for binary pattern files with multiple format support
    
    Supported formats:
    - Raw RGB binary (no header)
    - LED Matrix Studio binary format
    - Custom binary with frame headers
    - Large pattern files (450KB+)
    """
    
    def get_format_name(self) -> str:
        return "Enhanced Binary"
    
    def get_format_description(self) -> str:
        return (
            "Enhanced binary parser supporting multiple formats:\n"
            "- Raw RGB data (no header)\n"
            "- LED Matrix Studio binary format\n"
            "- Custom binary with frame headers\n"
            "- Large pattern files (450KB+)"
        )
    
    def detect(self, data: bytes, filename: str = "",
               suggested_leds: Optional[int] = None,
               suggested_frames: Optional[int] = None) -> bool:
        """Detect if this is a binary pattern file"""
        
        # Must be binary data
        if len(data) < 100:  # Too small to be a meaningful pattern
            return False
        
        # Check for common binary patterns
        # Look for RGB data patterns
        if len(data) % 3 == 0:
            # Could be raw RGB data
            return True
        
        # Check for LED Matrix Studio format
        if self._detect_led_matrix_studio_format(data):
            return True
        
        # Check for custom binary format
        if self._detect_custom_binary_format(data):
            return True
        
        return False
    
    def get_confidence(self, data: bytes) -> float:
        """Calculate confidence for binary detection"""
        if not self.detect(data, ""):
            return 0.0
        
        confidence = 0.3  # Base confidence for binary files
        
        # Higher confidence for larger files (more likely to be patterns)
        if len(data) > 100000:  # 100KB+
            confidence += 0.2
        elif len(data) > 10000:  # 10KB+
            confidence += 0.1
        
        # Check for LED Matrix Studio format
        if self._detect_led_matrix_studio_format(data):
            confidence += 0.3
        
        # Check for RGB data variation
        if len(data) >= 1000:
            sample = data[:1000]
            unique_values = len(set(sample))
            if unique_values > 50:
                confidence += 0.2
        
        return min(1.0, confidence)
    
    def parse(self, data: bytes,
              suggested_leds: Optional[int] = None,
              suggested_frames: Optional[int] = None) -> Pattern:
        """Parse binary data into Pattern"""
        
        # Try to normalize data: if it looks like per-frame headers exist,
        # detect repeating frame period and strip a constant header.
        try:
            data = self._try_strip_repeating_headers(data)
        except Exception:
            pass

        # Try LED Matrix Studio format first
        if self._detect_led_matrix_studio_format(data):
            return self._parse_led_matrix_studio_format(data, suggested_leds, suggested_frames)
        
        # Try custom binary format
        if self._detect_custom_binary_format(data):
            return self._parse_custom_binary_format(data, suggested_leds, suggested_frames)
        
        # Fall back to raw RGB parsing
        return self._parse_raw_rgb_format(data, suggested_leds, suggested_frames)
    
    def _detect_led_matrix_studio_format(self, data: bytes) -> bool:
        """Detect LED Matrix Studio binary format (supports extended header)."""
        if len(data) < 10:
            return False
        try:
            # Basic header
            magic, version, led_count, frame_count = struct.unpack('<4sHHH', data[:10])
            if magic != b'LEDM' or version > 5:
                return False
            # Optional extended header (width, height) may follow
            if len(data) >= 14:
                try:
                    width, height = struct.unpack('<HH', data[10:14])
                    if width > 0 and height > 0 and width * height == led_count:
                        # Looks like extended header; treat as valid
                        return True
                except Exception:
                    # Ignore, fall back to basic header validation below
                    pass
            # Fallback: basic header only
            return True
        except Exception:
            return False
    
    def _detect_custom_binary_format(self, data: bytes) -> bool:
        """Detect custom binary format with frame headers"""
        if len(data) < 20:
            return False
        
        # Look for frame header pattern
        # Format: [frame_header][rgb_data][frame_header][rgb_data]...
        try:
            # Check if data starts with a reasonable frame count
            frame_count = struct.unpack('<H', data[:2])[0]
            if 1 <= frame_count <= 10000:
                # Check if the rest of the data makes sense
                remaining_data = len(data) - 2
                if remaining_data > 0 and remaining_data % 3 == 0:
                    return True
        except:
            pass
        
        return False
    
    def _parse_led_matrix_studio_format(self, data: bytes, 
                                      suggested_leds: Optional[int] = None,
                                      suggested_frames: Optional[int] = None) -> Pattern:
        """Parse LED Matrix Studio binary format"""
        try:
            # Parse header (with optional width/height)
            magic, version, led_count, frame_count = struct.unpack('<4sHHH', data[:10])
            if magic != b'LEDM':
                raise ValueError("Invalid LED Matrix Studio format")
            
            width = led_count
            height = 1
            offset = 10
            # Try extended header (width, height)
            if len(data) >= 14:
                try:
                    ext_w, ext_h = struct.unpack('<HH', data[10:14])
                    if ext_w > 0 and ext_h > 0 and ext_w * ext_h == led_count:
                        width, height = ext_w, ext_h
                        offset = 14
                except Exception:
                    pass

            # Parse frames
            frames = []
            
            for frame_idx in range(frame_count):
                # Each frame: [duration_ms][rgb_data...]
                if offset + 2 > len(data):
                    break
                
                duration_ms = struct.unpack('<H', data[offset:offset+2])[0]
                offset += 2
                
                # Read RGB data for this frame
                rgb_data_size = led_count * 3
                if offset + rgb_data_size > len(data):
                    break
                
                pixels = []
                for led_idx in range(led_count):
                    pixel_offset = offset + led_idx * 3
                    r = data[pixel_offset]
                    g = data[pixel_offset + 1]
                    b = data[pixel_offset + 2]
                    pixels.append((r, g, b))
                
                frames.append(Frame(pixels=pixels, duration_ms=duration_ms))
                offset += rgb_data_size
            
            # Create metadata
            metadata = PatternMetadata(
                width=width,
                height=height,
                color_order="RGB"
            )
            
            return Pattern(
                name="LED Matrix Studio Import",
                metadata=metadata,
                frames=frames
            )
            
        except Exception as e:
            raise ValueError(f"Failed to parse LED Matrix Studio format: {e}")
    
    def _parse_custom_binary_format(self, data: bytes,
                                  suggested_leds: Optional[int] = None,
                                  suggested_frames: Optional[int] = None) -> Pattern:
        """Parse custom binary format with frame headers"""
        try:
            # Parse frame count from header
            frame_count = struct.unpack('<H', data[:2])[0]
            offset = 2
            
            # Calculate LED count from remaining data
            remaining_data = len(data) - 2
            led_count = remaining_data // (frame_count * 3)
            
            if led_count <= 0:
                raise ValueError("Invalid LED count")
            
            # Parse frames
            frames = []
            bytes_per_frame = led_count * 3
            
            for frame_idx in range(frame_count):
                if offset + bytes_per_frame > len(data):
                    break
                
                pixels = []
                for led_idx in range(led_count):
                    pixel_offset = offset + led_idx * 3
                    r = data[pixel_offset]
                    g = data[pixel_offset + 1]
                    b = data[pixel_offset + 2]
                    pixels.append((r, g, b))
                
                # Default 20ms per frame (50 FPS)
                frames.append(Frame(pixels=pixels, duration_ms=20))
                offset += bytes_per_frame
            
            # Create metadata
            metadata = PatternMetadata(
                width=led_count,
                height=1,
                color_order="RGB"
            )
            
            return Pattern(
                name="Custom Binary Import",
                metadata=metadata,
                frames=frames
            )
            
        except Exception as e:
            raise ValueError(f"Failed to parse custom binary format: {e}")
    
    def _parse_raw_rgb_format(self, data: bytes,
                             suggested_leds: Optional[int] = None,
                             suggested_frames: Optional[int] = None) -> Pattern:
        """Parse raw RGB format (fallback)"""
        if len(data) % 3 != 0:
            raise ValueError("Data size not divisible by 3 (RGB)")
        
        total_pixels = len(data) // 3
        
        # Determine LED count and frame count
        num_leds = None
        num_frames = None
        
        if suggested_leds and suggested_frames:
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
            if total_pixels % suggested_leds == 0:
                num_leds = suggested_leds
                num_frames = total_pixels // suggested_leds
            else:
                raise ValueError(
                    f"Total pixels ({total_pixels}) not divisible by "
                    f"LED count ({suggested_leds})"
                )
        elif suggested_frames:
            if total_pixels % suggested_frames == 0:
                num_frames = suggested_frames
                num_leds = total_pixels // suggested_frames
            else:
                raise ValueError(
                    f"Total pixels ({total_pixels}) not divisible by "
                    f"frame count ({suggested_frames})"
                )
        else:
            # Auto-detect dimensions
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
        
        # Create metadata with a friendly matrix guess (e.g., 12×6 for 72 LEDs)
        width_guess, height_guess = self._choose_matrix_dimensions(num_leds)
        metadata = PatternMetadata(
            width=width_guess,
            height=height_guess,
            color_order="RGB"
        )
        
        return Pattern(
            name="Raw RGB Import",
            metadata=metadata,
            frames=frames
        )
    
    def _auto_detect_dimensions(self, total_pixels: int) -> Tuple[Optional[int], Optional[int]]:
        """Auto-detect LED count and frame count with improved scoring.
        Prefers candidates that yield a realistic animation (more frames),
        and includes 72 LEDs as a common case (12×6 matrices).
        """

        import math

        common_led_counts = [
            64,   # 8×8 matrix
            72,   # 12×6 matrix (common)
            76,   # user-specific/common
            96,   # 12×8 matrix
            100,  # common strip
            120,  # 12×10 matrix
            144,  # 12×12 matrix
            150,  # strip
            160,  # 16×10
            192,  # 16×12
            256,  # 16×16
            300, 320, 400, 512, 600, 800, 1024, 2048
        ]

        candidates: List[Tuple[int, int, int]] = []  # (leds, frames, score)
        for leds in common_led_counts:
            if total_pixels % leds == 0:
                frames = total_pixels // leds
                if frames >= 2:
                    score = 0
                    if 10 <= frames <= 240:
                        score += 3
                    elif 5 <= frames <= 480:
                        score += 2
                    else:
                        score += 1
                    candidates.append((leds, frames, score))

        if candidates:
            candidates.sort(key=lambda x: (x[2], x[1]), reverse=True)
            best_leds, best_frames, _ = candidates[0]
            return (best_leds, best_frames)

        # Factorization fallback
        divisors: List[int] = []
        sqrt = int(math.sqrt(total_pixels))
        for i in range(1, min(sqrt + 1, 5000)):
            if total_pixels % i == 0:
                divisors.append(i)
                j = total_pixels // i
                if j != i:
                    divisors.append(j)
        divisors.sort()
        best: Tuple[Optional[int], Optional[int], int] = (None, None, -1)
        for leds in divisors:
            if 50 <= leds <= 5000:
                frames = total_pixels // leds
                if 2 <= frames <= 100000:
                    score = 1 + (2 if 10 <= frames <= 240 else 0)
                    if score > best[2]:
                        best = (leds, frames, score)
        if best[0] is not None:
            return (best[0], best[1])

        # Perfect square → single frame
        sqrt = int(math.sqrt(total_pixels))
        if sqrt * sqrt == total_pixels and 50 <= sqrt <= 5000:
            return (total_pixels, 1)
        return (None, None)

    # --- Header detection/stripping helpers ---
    def _try_strip_repeating_headers(self, data: bytes) -> bytes:
        """If data appears to contain repeating per-frame headers, strip them.
        Strategy:
        - Find a likely period (frame size) by autocorrelation scoring
        - Estimate header length as the number of leading bytes identical across
          the first several frames
        - If header_len > 0 and period >= header_len and total size divides period,
          rebuild payload by removing header from each frame
        """
        # If already divisible by 3 (raw RGB), keep as-is
        if len(data) % 3 == 0:
            return data

        period = self._detect_repeating_period(data)
        # Require reasonable period and divisibility
        if not period or period < 24 or (len(data) % period) != 0:
            return data

        header_len = self._estimate_header_len(data, period)
        # If no meaningful header, return original
        if header_len <= 0 or header_len >= period:
            return data

        # Strip headers frame-by-frame
        out = bytearray()
        for i in range(0, len(data), period):
            frame = data[i:i+period]
            if len(frame) < period:
                break
            out.extend(frame[header_len:])

        # Only accept if new data matches RGB multiple
        return bytes(out) if (len(out) % 3 == 0) else data

    def _detect_repeating_period(self, data: bytes) -> Optional[int]:
        """Find a likely repeating period by simple autocorrelation scoring."""
        max_period = min(2048, len(data) // 2)
        best_score = -1
        best_period = None
        # Scan with step 2 for speed; start above tiny sizes to avoid noise
        for period in range(24, max_period, 2):
            # quick skip if not divisible (tends to be periodic)
            if (len(data) % period) not in (0, period // 2):
                pass
            score = 0
            limit = len(data) - period
            # sample every 8 bytes to reduce cost
            for i in range(0, limit, 8):
                if data[i] == data[i + period]:
                    score += 1
            if score > best_score:
                best_score = score
                best_period = period
        return best_period

    def _estimate_header_len(self, data: bytes, period: int) -> int:
        """Estimate constant header length at the start of each frame."""
        num_frames = len(data) // period
        if num_frames < 2:
            return 0
        # Compare first up to 6 frames
        frames = [data[i*period:(i+1)*period] for i in range(min(num_frames, 6))]
        header_len = 0
        for i in range(period):
            same = True
            base = frames[0][i]
            for f in frames[1:]:
                if f[i] != base:
                    same = False
                    break
            if same:
                header_len += 1
            else:
                break
        # Heuristic: cap header to a reasonable size (e.g., 4..64)
        if header_len < 4 or header_len > 128:
            return 0
        return header_len

    def _choose_matrix_dimensions(self, led_count: int) -> Tuple[int, int]:
        """Pick a friendly matrix width×height for a given LED count."""
        preferred = [12, 16, 8, 10, 20, 24, 32]
        for w in preferred:
            if led_count % w == 0:
                h = led_count // w
                if h >= 1:
                    return (w, h)
        # closest to square with width>=height
        best = (led_count, 1)
        best_diff = led_count
        import math
        for h in range(1, int(math.sqrt(led_count)) + 1):
            if led_count % h == 0:
                w = led_count // h
                if w < h:
                    w, h = h, w
                diff = abs(w - h)
                if diff < best_diff:
                    best = (w, h)
                    best_diff = diff
        return best

