"""
Enhanced Binary Parser - Handles large binary pattern files
Supports multiple binary formats with auto-detection
"""

from typing import Optional, Tuple, List
import struct
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

        # Check for dimension-first header (width/height before frame data)
        if self._detect_dimension_header_format(data):
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

        # Stronger confidence when explicit dimensions are present
        if self._detect_dimension_header_format(data):
            confidence += 0.4
        
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

        # Then dimension-first width/height header
        dimension_info = self._detect_dimension_header_format(data)
        if dimension_info:
            return self._parse_dimension_header_format(data, dimension_info)
        
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
                remaining_data = len(data) - 2
                if remaining_data <= 0:
                    return False
                if remaining_data % 3 == 0:
                    return True
                if remaining_data % frame_count == 0:
                    per_frame = remaining_data // frame_count
                    if per_frame >= 3:
                        return True
        except:
            pass
        
        return False

    def _detect_dimension_header_format(self, data: bytes) -> Optional[Tuple[int, int, int]]:
        """
        Detect files that start with explicit width/height/frame count header.

        Layout:
            uint16 width
            uint16 height
            uint16 frame_count
            repeated frame_count times:
                uint16 duration_ms
                RGB payload (width*height*3 bytes)
        """
        minimum_header = 6
        if len(data) < minimum_header:
            return None

        try:
            width, height, frame_count = struct.unpack_from('<HHH', data, 0)
        except struct.error:
            return None

        if not (1 <= width <= 4096 and 1 <= height <= 4096):
            return None
        if width * height > 4096 * 4096:
            return None
        if not (1 <= frame_count <= 20000):
            return None

        rgb_per_frame = width * height * 3
        frame_record = 2 + rgb_per_frame  # duration + payload
        remaining = len(data) - minimum_header
        if remaining <= 0:
            return None
        if frame_record == 0:
            return None

        if remaining % frame_record != 0:
            return None

        computed_frames = remaining // frame_record
        if computed_frames != frame_count:
            return None

        return (width, height, frame_count)

    def _parse_dimension_header_format(
        self,
        data: bytes,
        header: Tuple[int, int, int]
    ) -> Pattern:
        """Parse width/height/header format with per-frame durations."""
        width, height, frame_count = header
        rgb_per_frame = width * height * 3
        frame_stride = 2 + rgb_per_frame

        offset = 6
        frames: List[Frame] = []

        for frame_idx in range(frame_count):
            if offset + 2 > len(data):
                raise ValueError(
                    f"Incomplete duration header for frame {frame_idx}"
                )
            duration_ms = struct.unpack_from('<H', data, offset)[0]
            offset += 2

            payload = data[offset:offset + rgb_per_frame]
            if len(payload) != rgb_per_frame:
                raise ValueError(
                    f"Frame {frame_idx} payload truncated; "
                    f"expected {rgb_per_frame} bytes, got {len(payload)}"
                )
            offset += rgb_per_frame

            pixels = [
                (payload[i], payload[i + 1], payload[i + 2])
                for i in range(0, len(payload), 3)
            ]
            frames.append(Frame(
                pixels=pixels,
                duration_ms=max(1, duration_ms or 20)
            ))

        metadata = PatternMetadata(
            width=width,
            height=height,
            color_order="RGB",
            dimension_source="header",
            dimension_confidence=1.0
        )

        return Pattern(
            name="Dimension-Header Binary Import",
            metadata=metadata,
            frames=frames
        )
    
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
            dimension_source = "led_count"
            dimension_confidence = 0.6
            offset = 10
            # Try extended header (width, height)
            if len(data) >= 14:
                try:
                    ext_w, ext_h = struct.unpack('<HH', data[10:14])
                    if ext_w > 0 and ext_h > 0 and ext_w * ext_h == led_count:
                        width, height = ext_w, ext_h
                        dimension_source = "header"
                        dimension_confidence = 1.0
                        offset = 14
                except Exception:
                    pass

            # Parse frames
            frames = []
            
            for frame_idx in range(frame_count):
                # Each frame: [duration_ms][rgb_data...]
                if offset + 2 > len(data):
                    raise ValueError(
                        f"Incomplete frame header at index {frame_idx}; "
                        "file truncated or header malformed."
                    )

                duration_ms = struct.unpack('<H', data[offset:offset+2])[0]
                offset += 2
                
                # Read RGB data for this frame
                rgb_data_size = led_count * 3
                if offset + rgb_data_size > len(data):
                    raise ValueError(
                        f"Incomplete RGB data for frame {frame_idx}; "
                        "file truncated or payload corrupted."
                    )
                
                pixels = []
                for led_idx in range(led_count):
                    pixel_offset = offset + led_idx * 3
                    r = data[pixel_offset]
                    g = data[pixel_offset + 1]
                    b = data[pixel_offset + 2]
                    pixels.append((r, g, b))
                
                frames.append(Frame(pixels=pixels, duration_ms=duration_ms))
                offset += rgb_data_size
            
            if len(frames) != frame_count:
                raise ValueError(
                    f"Frame count mismatch: header reports {frame_count}, "
                    f"but only {len(frames)} frames were decoded."
                )

            if frames and (width == led_count and height == 1):
                guess = pick_best_layout(
                    led_count,
                    frames[0].pixels,
                    include_strips=True
                )
                if guess:
                    width, height, score = guess
                    dimension_source = "detector"
                    dimension_confidence = max(dimension_confidence, score)

            # Create metadata
            metadata = PatternMetadata(
                width=width,
                height=height,
                color_order="RGB",
                dimension_source=dimension_source,
                dimension_confidence=dimension_confidence
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
            
            # Calculate per-frame payload (header + RGB data)
            remaining_data = len(data) - 2
            if frame_count <= 0:
                raise ValueError("Invalid frame count")

            if remaining_data % frame_count != 0:
                raise ValueError(
                    "Binary payload size does not align with frame count. "
                    "Detected padding or truncated data."
                )

            per_frame_bytes = remaining_data // frame_count
            header_len, led_count = self._resolve_custom_frame_layout(per_frame_bytes)
            
            if led_count <= 0:
                raise ValueError("Invalid LED count")
            
            # Parse frames
            frames = []
            frame_stride = per_frame_bytes
            payload_bytes = led_count * 3
            
            for frame_idx in range(frame_count):
                if offset + frame_stride > len(data):
                    raise ValueError(
                        f"Incomplete frame payload for frame {frame_idx}; "
                        "file truncated or payload corrupted."
                    )

                frame_chunk = data[offset:offset + frame_stride]
                payload = frame_chunk[header_len:]
                if len(payload) != payload_bytes:
                    raise ValueError(
                        f"Frame {frame_idx} payload length mismatch; "
                        f"expected {payload_bytes} bytes after header, got {len(payload)}."
                    )
                
                pixels = []
                for led_idx in range(led_count):
                    pixel_offset = led_idx * 3
                    r = payload[pixel_offset]
                    g = payload[pixel_offset + 1]
                    b = payload[pixel_offset + 2]
                    pixels.append((r, g, b))
                
                # Default 20ms per frame (50 FPS)
                frames.append(Frame(pixels=pixels, duration_ms=20))
                offset += frame_stride
            
            if len(frames) != frame_count:
                raise ValueError(
                    f"Frame count mismatch: header reports {frame_count}, "
                    f"but only {len(frames)} frames were decoded."
                )

            width_guess, height_guess = led_count, 1
            dimension_source = "fallback"
            dimension_confidence = 0.2
            if frames:
                guess = pick_best_layout(
                    led_count,
                    frames[0].pixels,
                    include_strips=True
                )
            else:
                guess = pick_best_layout(
                    led_count,
                    include_strips=True
                )
            if guess:
                width_guess, height_guess, score = guess
                dimension_source = "detector"
                dimension_confidence = score

            # Create metadata
            metadata = PatternMetadata(
                width=width_guess,
                height=height_guess,
                color_order="RGB",
                dimension_source=dimension_source,
                dimension_confidence=dimension_confidence
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
            num_leds, num_frames = self._auto_detect_dimensions(total_pixels, data)
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
        metadata = PatternMetadata(
            width=width_guess,
            height=height_guess,
            color_order="RGB",
            dimension_source=dimension_source,
            dimension_confidence=dimension_confidence
        )
        
        return Pattern(
            name="Raw RGB Import",
            metadata=metadata,
            frames=frames
        )
    
    def _auto_detect_dimensions(self, total_pixels: int, pixel_data: Optional[bytes] = None) -> Tuple[Optional[int], Optional[int]]:
        """Auto-detect LED count and frame count with improved scoring.
        Prefers candidates that yield a realistic animation (more frames),
        and includes 72 LEDs as a common case (12×6 matrices).
        """

        resolution = infer_leds_and_frames(
            total_pixels,
            include_strips=True,
            preferred_led_counts=COMMON_LED_COUNTS,
            pixel_bytes=pixel_data,
        )
        if resolution:
            return resolution.led_count, resolution.frames
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

    def _resolve_custom_frame_layout(self, per_frame_bytes: int) -> Tuple[int, int]:
        """
        Determine header length and LED count for custom binary frames.
        Returns (header_len, led_count).
        """
        if per_frame_bytes <= 0:
            raise ValueError("Per-frame payload must be positive")

        best_header = None
        best_leds = None
        best_score = -1.0

        max_header = min(128, per_frame_bytes - 3)  # leave room for at least one LED
        for header_len in range(0, max_header + 1):
            payload = per_frame_bytes - header_len
            if payload <= 0 or payload % 3 != 0:
                continue
            leds = payload // 3
            if leds <= 0:
                continue

            guess = pick_best_layout(
                leds,
                include_strips=True
            )
            score = guess[2] if guess else 0.0

            # Small headers and familiar LED counts get slight preference
            if header_len == 0:
                score += 0.05
            elif header_len <= 16:
                score += 0.02

            if best_header is None or score > best_score or (
                abs(score - best_score) < 1e-6 and header_len < best_header
            ):
                best_header = header_len
                best_leds = leds
                best_score = score

        if best_header is None or best_leds is None:
            raise ValueError(
                "Unable to infer LED count from custom frame payload. "
                "Specify LED/frames manually or inspect file headers."
            )

        return best_header, best_leds

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

