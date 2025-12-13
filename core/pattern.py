"""
Pattern Data Model - Canonical representation of LED patterns
Complete implementation with validation and transformations
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
from pathlib import Path
import json
import uuid
import enum


@dataclass
class Frame:
    """Single animation frame with RGB pixel data"""
    pixels: List[Tuple[int, int, int]]  # [(R, G, B), ...]
    duration_ms: int  # Milliseconds to display this frame
    
    def __post_init__(self):
        """Validate RGB values and duration"""
        for i, (r, g, b) in enumerate(self.pixels):
            if not (0 <= r <= 255):
                raise ValueError(f"Frame pixel {i} invalid R value: {r}")
            if not (0 <= g <= 255):
                raise ValueError(f"Frame pixel {i} invalid G value: {g}")
            if not (0 <= b <= 255):
                raise ValueError(f"Frame pixel {i} invalid B value: {b}")
        
        if self.duration_ms < 0:
            raise ValueError(f"Frame duration cannot be negative: {self.duration_ms}")
    
    @property
    def led_count(self) -> int:
        """Number of LEDs in this frame"""
        return len(self.pixels)
    
    def to_bytes(self) -> bytes:
        """Convert frame to raw RGB bytes"""
        return bytes([c for pixel in self.pixels for c in pixel])
    
    def copy(self) -> 'Frame':
        """Create a deep copy of this frame"""
        return Frame(
            pixels=[tuple(p) for p in self.pixels],
            duration_ms=self.duration_ms
        )


@dataclass
class PatternMetadata:
    """Pattern configuration and layout information"""
    width: int  # LEDs wide (or total count for strip)
    height: int = 1  # LEDs tall (1 for linear strip)
    color_order: str = "RGB"  # RGB, GRB, BRG, BGR, RBG, GBR
    fps: Optional[float] = None  # Average FPS (calculated)
    total_ms: Optional[int] = None  # Total duration (calculated)
    brightness: float = 1.0  # Global brightness (0.0-1.0)
    brightness_curve: str = "gamma_corrected"  # Brightness curve type
    led_type: str = "ws2812"  # LED chip type
    per_channel_brightness: bool = False  # Enable per-channel brightness
    red_brightness: float = 1.0  # Red channel brightness multiplier
    green_brightness: float = 1.0  # Green channel brightness multiplier
    blue_brightness: float = 1.0  # Blue channel brightness multiplier
    speed_curve: str = "linear"  # Speed curve type
    variable_speed: bool = False  # Enable variable speed
    interpolation_enabled: bool = False  # Enable frame interpolation
    interpolation_factor: float = 1.0  # Interpolation factor
    speed_keyframes: list = field(default_factory=list)  # Speed keyframes
    target_fps: Optional[float] = None  # Target FPS for firmware generation (overrides frame delays)
    # Display/export mapping (LAYERED ARCHITECTURE)
    # Layer 4: Firmware generation uses these for hardware mapping
    wiring_mode: str = "Row-major"  # "Row-major", "Serpentine", "Column-major", "Column-serpentine"
    data_in_corner: str = "LT"  # LT, LB, RT, RB
    # Removed: orientation_deg, mirror_h, mirror_v (using layered architecture)
    custom_mapping: Optional[List[int]] = None  # Optional explicit 0..N-1 order
    already_unwrapped: bool = False  # Flag to prevent double-mapping during flash
    original_wiring_mode: Optional[str] = None  # File's original wiring format (for conversion)
    original_data_in_corner: Optional[str] = None  # File's original data-in corner (for conversion)
    dimension_source: str = "unknown"  # 'header', 'detector', 'fallback', etc.
    dimension_confidence: float = 0.0  # 0.0 - 1.0 confidence in width/height
    source_format: Optional[str] = None  # Original file format (bin, dat, hex, leds, etc.)
    source_path: Optional[str] = None  # Original file path (if known)
    # User override for dimensions
    dimension_override: bool = False  # True if dimensions were manually overridden
    dimension_override_source: Optional[str] = None  # 'user' when manually set
    # Detection hints from parser/filename (weak hints adjust scores, strong hints override)
    wiring_mode_hint: Optional[str] = None  # Detected wiring mode hint from filename/metadata
    data_in_corner_hint: Optional[str] = None  # Detected data-in corner hint from filename/metadata
    hint_confidence: float = 0.0  # Confidence in hints (0.0-1.0), 0.9+ = strong hint
    # Circular layout support
    layout_type: str = "rectangular"  # "rectangular", "circle", "ring", "arc", "radial", "multi_ring", "radial_rays"
    circular_led_count: Optional[int] = None  # Number of LEDs in circular layout
    circular_radius: Optional[float] = None  # Outer radius (for ring/circle)
    circular_inner_radius: Optional[float] = None  # Inner radius (for ring)
    circular_start_angle: float = 0.0  # Start angle in degrees (for arc)
    circular_end_angle: float = 360.0  # End angle in degrees (for arc)
    circular_led_spacing: Optional[float] = None  # Optional custom LED spacing
    circular_mapping_table: Optional[List[Tuple[int, int]]] = None  # Precomputed (x,y) → LED index mapping
    # Multi-ring support (Budurasmala)
    multi_ring_count: Optional[int] = None  # Number of concentric rings (1-5)
    ring_led_counts: List[int] = field(default_factory=list)  # LEDs per ring
    ring_radii: List[float] = field(default_factory=list)  # Radius for each ring
    ring_spacing: Optional[float] = None  # Spacing between rings
    # Radial ray support (Budurasmala)
    ray_count: Optional[int] = None  # Number of rays extending from center
    leds_per_ray: Optional[int] = None  # LEDs along each ray
    ray_spacing_angle: Optional[float] = None  # Angle between rays in degrees
    # Custom LED positions (for custom PCBs - Budurasmala)
    custom_led_positions: Optional[List[Tuple[float, float]]] = None  # (x, y) positions in mm or units
    led_position_units: str = "grid"  # "grid", "mm", "inches"
    custom_position_center_x: Optional[float] = None  # Center X for custom positions
    custom_position_center_y: Optional[float] = None  # Center Y for custom positions
    # Matrix-style Budurasmala (curved matrix, text rendering)
    matrix_style: Optional[str] = None  # "curved", "hybrid_ring_matrix", None for standard
    text_content: Optional[str] = None  # Text to render on circular matrix
    text_font_size: Optional[int] = None  # Font size for text rendering
    text_color: Optional[Tuple[int, int, int]] = None  # RGB color for text
    # Irregular/custom shape support (LED Build-style)
    irregular_shape_enabled: bool = False  # Enable irregular shape mode
    active_cell_coordinates: Optional[List[Tuple[int, int]]] = None  # Sparse list of (x, y) active cell coordinates
    background_image_path: Optional[str] = None  # Path to imported background template image
    background_image_scale: float = 1.0  # Scale factor for background image
    background_image_offset_x: float = 0.0  # X offset for background image
    background_image_offset_y: float = 0.0  # Y offset for background image
    
    def __post_init__(self):
        """Validate metadata"""
        if self.width < 1:
            raise ValueError(f"Width must be >= 1: {self.width}")
        if self.height < 1:
            raise ValueError(f"Height must be >= 1: {self.height}")
        if self.color_order not in ["RGB", "GRB", "BRG", "BGR", "RBG", "GBR"]:
            raise ValueError(f"Invalid color order: {self.color_order}")
        if not (0.0 <= self.brightness <= 1.0):
            raise ValueError(f"Brightness must be 0.0-1.0: {self.brightness}")
        if not (0.0 <= self.dimension_confidence <= 1.0):
            raise ValueError(f"Dimension confidence must be 0.0-1.0: {self.dimension_confidence}")
        # Validate circular layout fields
        valid_layouts = ["rectangular", "circle", "ring", "arc", "radial", "multi_ring", "radial_rays", "custom_positions", "irregular"]
        if self.layout_type not in valid_layouts:
            raise ValueError(f"Invalid layout_type: {self.layout_type}, must be one of {valid_layouts}")
        if self.layout_type != "rectangular" and self.layout_type != "irregular":
            # For radial layouts, circular_led_count can be calculated from grid (height * width)
            # For multi_ring layouts, circular_led_count can be calculated from ring_led_counts
            # For radial_rays layouts, circular_led_count can be calculated from ray_count * leds_per_ray
            
            # CRITICAL: Ensure mapping table exists for circular layouts
            # This is the single source of truth - must be present
            if self.circular_mapping_table is None:
                try:
                    from core.mapping.circular_mapper import CircularMapper
                    self.circular_mapping_table = CircularMapper.generate_mapping_table(self)
                    
                    # Validate the generated mapping
                    is_valid, error_msg = CircularMapper.validate_mapping_table(self)
                    if not is_valid:
                        import logging
                        logging.warning(
                            f"Auto-generated mapping table is invalid: {error_msg}. "
                            f"Layout type: {self.layout_type}"
                        )
                except Exception as e:
                    import logging
                    logging.warning(
                        f"Failed to auto-generate mapping table for circular layout: {e}. "
                        f"Layout type: {self.layout_type}. "
                        f"Pattern may not work correctly until mapping is generated."
                    )
            # It will be set during mapping table generation if not provided
            if self.layout_type == "radial":
                # Radial layouts can calculate from grid
                if self.circular_led_count is not None and self.circular_led_count < 1:
                    raise ValueError(f"circular_led_count must be >= 1 for {self.layout_type} layout")
            elif self.layout_type == "multi_ring":
                # Multi-ring layouts: calculate from ring_led_counts if not provided
                if self.circular_led_count is None:
                    if self.ring_led_counts:
                        # Will be calculated during mapping table generation
                        pass
                    else:
                        raise ValueError(f"Either circular_led_count or ring_led_counts must be provided for {self.layout_type} layout")
                elif self.circular_led_count < 1:
                    raise ValueError(f"circular_led_count must be >= 1 for {self.layout_type} layout")
            elif self.layout_type == "radial_rays":
                # Radial rays layouts: calculate from ray_count * leds_per_ray if not provided
                if self.circular_led_count is None:
                    if self.ray_count and self.leds_per_ray:
                        # Will be calculated during mapping table generation
                        pass
                    else:
                        raise ValueError(f"Either circular_led_count or (ray_count and leds_per_ray) must be provided for {self.layout_type} layout")
                elif self.circular_led_count < 1:
                    raise ValueError(f"circular_led_count must be >= 1 for {self.layout_type} layout")
            elif self.layout_type == "custom_positions":
                # Custom positions layouts: calculate from custom_led_positions if not provided
                if self.circular_led_count is None:
                    if self.custom_led_positions:
                        # Will be calculated during mapping table generation
                        pass
                    else:
                        raise ValueError(f"Either circular_led_count or custom_led_positions must be provided for {self.layout_type} layout")
                elif self.circular_led_count < 1:
                    raise ValueError(f"circular_led_count must be >= 1 for {self.layout_type} layout")
            elif self.layout_type != "irregular":
                # Standard circular/ring/arc layouts require circular_led_count
                # Irregular shapes don't use circular_led_count
                if self.circular_led_count is None or self.circular_led_count < 1:
                    raise ValueError(f"circular_led_count must be >= 1 for {self.layout_type} layout")
            if self.circular_radius is not None and self.circular_radius <= 0:
                raise ValueError(f"circular_radius must be > 0: {self.circular_radius}")
            if self.layout_type == "ring":
                if self.circular_inner_radius is not None:
                    if self.circular_radius is None:
                        raise ValueError("circular_radius required when circular_inner_radius is set")
                    if self.circular_inner_radius >= self.circular_radius:
                        raise ValueError("circular_inner_radius must be < circular_radius")
            if self.circular_start_angle < 0 or self.circular_start_angle >= 360:
                raise ValueError(f"circular_start_angle must be 0-360: {self.circular_start_angle}")
            if self.circular_end_angle < 0 or self.circular_end_angle > 360:
                raise ValueError(f"circular_end_angle must be 0-360: {self.circular_end_angle}")
            if self.circular_end_angle <= self.circular_start_angle:
                raise ValueError("circular_end_angle must be > circular_start_angle")
        
        # Validate multi-ring layout fields
        if self.layout_type == "multi_ring":
            if self.multi_ring_count is None or not (1 <= self.multi_ring_count <= 5):
                raise ValueError(f"multi_ring_count must be 1-5 for multi_ring layout, got {self.multi_ring_count}")
            if len(self.ring_led_counts) != self.multi_ring_count:
                raise ValueError(f"ring_led_counts length ({len(self.ring_led_counts)}) must match multi_ring_count ({self.multi_ring_count})")
            if len(self.ring_radii) != self.multi_ring_count:
                raise ValueError(f"ring_radii length ({len(self.ring_radii)}) must match multi_ring_count ({self.multi_ring_count})")
            for i, count in enumerate(self.ring_led_counts):
                if count < 1:
                    raise ValueError(f"ring_led_counts[{i}] must be >= 1, got {count}")
            for i, radius in enumerate(self.ring_radii):
                if radius <= 0:
                    raise ValueError(f"ring_radii[{i}] must be > 0, got {radius}")
            if self.ring_spacing is not None and self.ring_spacing < 0:
                raise ValueError(f"ring_spacing must be >= 0, got {self.ring_spacing}")
        
        # Validate radial ray layout fields
        if self.layout_type == "radial_rays":
            if self.ray_count is None or self.ray_count < 1:
                raise ValueError(f"ray_count must be >= 1 for radial_rays layout, got {self.ray_count}")
            if self.leds_per_ray is None or self.leds_per_ray < 1:
                raise ValueError(f"leds_per_ray must be >= 1 for radial_rays layout, got {self.leds_per_ray}")
            if self.ray_spacing_angle is not None:
                if self.ray_spacing_angle <= 0 or self.ray_spacing_angle > 360:
                    raise ValueError(f"ray_spacing_angle must be 0-360 degrees, got {self.ray_spacing_angle}")
    
    @property
    def led_count(self) -> int:
        """Total number of LEDs"""
        return self.width * self.height
    
    @property
    def is_matrix(self) -> bool:
        """True if 2D matrix, False if linear strip"""
        return self.height > 1


@dataclass
class Pattern:
    """Complete LED pattern with metadata and frames"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Untitled Pattern"
    metadata: PatternMetadata = field(default_factory=lambda: PatternMetadata(width=1))
    frames: List[Frame] = field(default_factory=list)
    lms_pattern_instructions: List[Dict[str, object]] = field(default_factory=list)
    scratchpads: Dict[str, List[Tuple[int, int, int]]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate pattern consistency"""
        # Check all frames have same LED count
        if self.frames:
            expected_leds = self.metadata.led_count
            for i, frame in enumerate(self.frames):
                if frame.led_count != expected_leds:
                    raise ValueError(
                        f"Frame {i} has {frame.led_count} LEDs, "
                        f"expected {expected_leds}"
                    )
    
    @property
    def led_count(self) -> int:
        """Number of LEDs in pattern"""
        return self.metadata.led_count
    
    @property
    def frame_count(self) -> int:
        """Number of frames in pattern"""
        return len(self.frames)
    
    @property
    def duration_ms(self) -> int:
        """Total pattern duration in milliseconds"""
        return sum(f.duration_ms for f in self.frames)
    
    @property
    def average_fps(self) -> float:
        """Calculate average FPS across all frames"""
        if self.duration_ms == 0 or self.frame_count == 0:
            return 0.0
        return (self.frame_count * 1000.0) / self.duration_ms
    
    def set_global_fps(self, fps: float):
        """Set all frames to same duration for target FPS"""
        if fps <= 0:
            raise ValueError(f"FPS must be > 0: {fps}")
        
        duration_ms = int(1000.0 / fps)
        for frame in self.frames:
            frame.duration_ms = max(1, duration_ms)  # At least 1ms
    
    def scale_speed(self, multiplier: float):
        """
        Scale all frame durations by multiplier
        multiplier > 1.0 = slower (more ms per frame)
        multiplier < 1.0 = faster (less ms per frame)
        """
        if multiplier <= 0:
            raise ValueError(f"Multiplier must be > 0: {multiplier}")
        
        for frame in self.frames:
            new_duration = int(frame.duration_ms * multiplier)
            frame.duration_ms = max(1, new_duration)
    
    def fit_to_duration(self, target_ms: int):
        """Adjust frame durations to fit exact total duration"""
        if self.frame_count == 0:
            return
        
        if target_ms < self.frame_count:
            target_ms = self.frame_count  # At least 1ms per frame
        
        duration_per_frame = target_ms // self.frame_count
        remainder = target_ms % self.frame_count
        
        for i, frame in enumerate(self.frames):
            frame.duration_ms = duration_per_frame
            if i < remainder:
                frame.duration_ms += 1
    
    def apply_brightness(self, brightness: int):
        """
        Apply brightness scaling to all pixels (destructive)
        brightness: 0-255
        """
        if not (0 <= brightness <= 255):
            raise ValueError(f"Brightness must be 0-255: {brightness}")
        
        scale = brightness / 255.0
        
        for frame in self.frames:
            frame.pixels = [
                (
                    int(r * scale),
                    int(g * scale),
                    int(b * scale)
                )
                for r, g, b in frame.pixels
            ]
        
        self.metadata.brightness = brightness
    
    def reorder_colors(self, new_order: str):
        """
        Convert color order (e.g., RGB → GRB for WS2812)
        new_order: "RGB", "GRB", "BRG", "BGR", "RBG", "GBR"
        """
        if new_order not in ["RGB", "GRB", "BRG", "BGR", "RBG", "GBR"]:
            raise ValueError(f"Invalid color order: {new_order}")
        
        old_order = self.metadata.color_order
        if old_order == new_order:
            return  # No change needed
        
        # Build index mapping: old position -> new position
        old_indices = {c: i for i, c in enumerate(old_order)}
        new_indices = {c: i for i, c in enumerate(new_order)}
        
        # Create reordering map
        reorder_map = [
            old_indices['R'] if i == new_indices['R'] else
            old_indices['G'] if i == new_indices['G'] else
            old_indices['B']
            for i in range(3)
        ]
        
        # Apply to all pixels
        for frame in self.frames:
            frame.pixels = [
                tuple([pixel[reorder_map[i]] for i in range(3)])
                for pixel in frame.pixels
            ]
        
        self.metadata.color_order = new_order
    
    def duplicate_frame(self, frame_idx: int) -> int:
        """Duplicate frame at index, returns new frame index"""
        if not (0 <= frame_idx < self.frame_count):
            raise IndexError(f"Frame index out of range: {frame_idx}")
        
        new_frame = self.frames[frame_idx].copy()
        self.frames.insert(frame_idx + 1, new_frame)
        return frame_idx + 1
    
    def delete_frame(self, frame_idx: int):
        """Delete frame at index"""
        if not (0 <= frame_idx < self.frame_count):
            raise IndexError(f"Frame index out of range: {frame_idx}")
        
        if self.frame_count == 1:
            raise ValueError("Cannot delete last frame")
        
        del self.frames[frame_idx]
    
    def apply_advanced_brightness(self, brightness: float, curve_type: str = "gamma_corrected", 
                                 per_channel: Optional[Dict[str, float]] = None, led_type: str = "ws2812"):
        """
        Apply advanced brightness control to the pattern
        
        Args:
            brightness: Global brightness (0.0-1.0)
            curve_type: Brightness curve type
            per_channel: Per-channel brightness multipliers
            led_type: LED chip type
        """
        # Update metadata
        self.metadata.brightness = brightness
        self.metadata.brightness_curve = curve_type
        self.metadata.led_type = led_type
        
        # Create brightness mapper
        curve_enum = BrightnessCurve(curve_type) if hasattr(BrightnessCurve, curve_type.upper()) else BrightnessCurve.GAMMA_CORRECTED
        mapper = HardwareBrightnessMapper(curve_enum)
        
        # Apply brightness to all frames
        for frame in self.frames:
            new_pixels = []
            for r, g, b in frame.pixels:
                # Apply global brightness using hardware mapping
                mapped_brightness = mapper.map_brightness(brightness) / 255.0  # Convert to 0.0-1.0
                
                # Apply per-channel brightness if specified
                if per_channel and isinstance(per_channel, dict):
                    r_mult = per_channel.get('red', 1.0)
                    g_mult = per_channel.get('green', 1.0)
                    b_mult = per_channel.get('blue', 1.0)
                    
                    new_r = int(r * mapped_brightness * r_mult)
                    new_g = int(g * mapped_brightness * g_mult)
                    new_b = int(b * mapped_brightness * b_mult)
                else:
                    new_r = int(r * mapped_brightness)
                    new_g = int(g * mapped_brightness)
                    new_b = int(b * mapped_brightness)
                
                # Clamp values to 0-255
                new_r = max(0, min(255, new_r))
                new_g = max(0, min(255, new_g))
                new_b = max(0, min(255, new_b))
                
                new_pixels.append((new_r, new_g, new_b))
            
            frame.pixels = new_pixels
    
    def set_per_channel_brightness(self, red: float, green: float, blue: float):
        """Set per-channel brightness multipliers"""
        self.metadata.per_channel_brightness = True
        self.metadata.red_brightness = red
        self.metadata.green_brightness = green
        self.metadata.blue_brightness = blue
    
    def set_led_type(self, led_type: str):
        """Set LED chip type"""
        self.metadata.led_type = led_type
    
    def set_brightness_curve(self, curve_type: str):
        """Set brightness curve type"""
        self.metadata.brightness_curve = curve_type
    
    def set_speed_curve(self, curve_type: str):
        """Set speed curve type"""
        self.metadata.speed_curve = curve_type
    
    def set_variable_speed(self, enabled: bool):
        """Enable/disable variable speed"""
        self.metadata.variable_speed = enabled
    
    def set_interpolation(self, enabled: bool, factor: float = 1.0):
        """Enable/disable frame interpolation"""
        self.metadata.interpolation_enabled = enabled
        self.metadata.interpolation_factor = factor
    
    def set_speed_keyframes(self, keyframes: list):
        """Set speed keyframes"""
        self.metadata.speed_keyframes = keyframes
    
    def interpolate_frames(self, factor: float):
        """Interpolate frames to increase frame count"""
        if factor <= 1.0:
            return
        
        new_frames = []
        for i in range(len(self.frames) - 1):
            current_frame = self.frames[i]
            next_frame = self.frames[i + 1]
            
            # Add original frame
            new_frames.append(current_frame)
            
            # Add interpolated frames
            for j in range(1, int(factor)):
                t = j / factor
                interpolated_pixels = []
                
                for k in range(len(current_frame.pixels)):
                    r1, g1, b1 = current_frame.pixels[k]
                    r2, g2, b2 = next_frame.pixels[k]
                    
                    r = int(r1 + (r2 - r1) * t)
                    g = int(g1 + (g2 - g1) * t)
                    b = int(b1 + (b2 - b1) * t)
                    
                    interpolated_pixels.append((r, g, b))
                
                # Create interpolated frame with proportional duration
                duration = int(current_frame.duration_ms / factor)
                new_frames.append(Frame(pixels=interpolated_pixels, duration_ms=max(1, duration)))
        
        # Add last frame
        new_frames.append(self.frames[-1])
        
        self.frames = new_frames
    
    def apply_variable_speed(self, keyframes: list):
        """Apply variable speed using keyframes"""
        if not keyframes:
            return
        
        # Sort keyframes by frame
        keyframes.sort(key=lambda x: x[0])
        
        # Apply speed changes to all frames between keyframes
        for i in range(len(keyframes) - 1):
            start_frame, start_speed = keyframes[i]
            end_frame, end_speed = keyframes[i + 1]
            
            # Apply speed to frames in this range
            for frame_idx in range(start_frame, min(end_frame, len(self.frames))):
                if frame_idx < len(self.frames):
                    # Interpolate speed between keyframes
                    if end_frame > start_frame:
                        t = (frame_idx - start_frame) / (end_frame - start_frame)
                        speed_mult = start_speed + (end_speed - start_speed) * t
                    else:
                        speed_mult = start_speed
                    
                    # Scale duration by speed multiplier
                    if speed_mult > 0:
                        new_duration = int(self.frames[frame_idx].duration_ms / speed_mult)
                        self.frames[frame_idx].duration_ms = max(1, new_duration)
    
    def apply_speed_curve(self, curve_type: str):
        """Apply speed curve to pattern"""
        self.metadata.speed_curve = curve_type
        
        # Map curve type to function
        curve_functions = {
            'linear': SpeedController.linear_easing,
            'ease_in_quad': SpeedController.ease_in_quad,
            'ease_out_quad': SpeedController.ease_out_quad,
            'ease_in_out_quad': SpeedController.ease_in_out_quad,
            'ease_in_cubic': SpeedController.ease_in_cubic,
            'ease_out_cubic': SpeedController.ease_out_cubic,
            'ease_in_out_cubic': SpeedController.ease_in_out_cubic
        }
        
        curve_func = curve_functions.get(curve_type, SpeedController.linear_easing)
        
        # Apply curve to all frames
        total_frames = len(self.frames)
        for i, frame in enumerate(self.frames):
            # Calculate position in animation (0.0 to 1.0)
            t = i / (total_frames - 1) if total_frames > 1 else 0.0
            
            # Apply curve to get speed multiplier
            speed_mult = curve_func(t)
            
            # Adjust frame duration based on speed curve
            if speed_mult > 0:
                new_duration = int(frame.duration_ms / speed_mult)
                frame.duration_ms = max(1, new_duration)
    
    @property
    def total_duration_ms(self) -> int:
        """Total pattern duration in milliseconds"""
        return self.duration_ms
    
    def to_json(self, use_rle: bool = True) -> Dict:
        """
        Convert to canonical JSON schema format (v1.0).
        
        Args:
            use_rle: Whether to use RLE compression for pixel data
            
        Returns:
            Pattern JSON dictionary conforming to schema v1.0
        """
        from core.schemas.pattern_converter import PatternConverter
        return PatternConverter.pattern_to_json(self, use_rle=use_rle)
    
    @staticmethod
    def from_json(data: Dict) -> 'Pattern':
        """
        Create Pattern from canonical JSON schema format (v1.0).
        
        Args:
            data: Pattern JSON dictionary conforming to schema v1.0
            
        Returns:
            Pattern object
        """
        from core.schemas.pattern_converter import PatternConverter
        return PatternConverter.pattern_from_json(data)
    
    def to_dict(self) -> Dict:
        """Serialize to JSON-compatible dictionary (legacy format)"""
        return {
            "version": "1.0",
            "id": self.id,
            "name": self.name,
            "metadata": {
                "width": self.metadata.width,
                "height": self.metadata.height,
                "color_order": self.metadata.color_order,
                "fps": self.metadata.fps,
                "total_ms": self.metadata.total_ms,
                "brightness": self.metadata.brightness,
                "wiring_mode": getattr(self.metadata, 'wiring_mode', "Row-major"),
                "data_in_corner": getattr(self.metadata, 'data_in_corner', "LT"),
                "custom_mapping": getattr(self.metadata, 'custom_mapping', None),
                "already_unwrapped": getattr(self.metadata, 'already_unwrapped', False),
                "original_wiring_mode": getattr(self.metadata, 'original_wiring_mode', None),
                "original_data_in_corner": getattr(self.metadata, 'original_data_in_corner', None),
                # Advanced brightness settings
                "brightness_curve": getattr(self.metadata, 'brightness_curve', 'gamma_corrected'),
                "led_type": getattr(self.metadata, 'led_type', 'ws2812'),
                "per_channel_brightness": getattr(self.metadata, 'per_channel_brightness', False),
                "red_brightness": getattr(self.metadata, 'red_brightness', 1.0),
                "green_brightness": getattr(self.metadata, 'green_brightness', 1.0),
                "blue_brightness": getattr(self.metadata, 'blue_brightness', 1.0),
                # Speed control settings
                "speed_curve": getattr(self.metadata, 'speed_curve', 'linear'),
                "variable_speed": getattr(self.metadata, 'variable_speed', False),
                "speed_keyframes": getattr(self.metadata, 'speed_keyframes', []),
                "target_fps": getattr(self.metadata, 'target_fps', None),
                # Interpolation settings
                "interpolation_enabled": getattr(self.metadata, 'interpolation_enabled', False),
                "interpolation_factor": getattr(self.metadata, 'interpolation_factor', 1.0),
                # Dimension detection metadata
                "dimension_source": getattr(self.metadata, 'dimension_source', 'unknown'),
                "dimension_confidence": getattr(self.metadata, 'dimension_confidence', 0.0),
                "source_format": getattr(self.metadata, 'source_format', None),
                "source_path": getattr(self.metadata, 'source_path', None),
                # Detection hints
                "wiring_mode_hint": getattr(self.metadata, 'wiring_mode_hint', None),
                "data_in_corner_hint": getattr(self.metadata, 'data_in_corner_hint', None),
                "hint_confidence": getattr(self.metadata, 'hint_confidence', 0.0),
                # Circular layout
                "layout_type": getattr(self.metadata, 'layout_type', 'rectangular'),
                "circular_led_count": getattr(self.metadata, 'circular_led_count', None),
                "circular_radius": getattr(self.metadata, 'circular_radius', None),
                "circular_inner_radius": getattr(self.metadata, 'circular_inner_radius', None),
                "circular_start_angle": getattr(self.metadata, 'circular_start_angle', 0.0),
                "circular_end_angle": getattr(self.metadata, 'circular_end_angle', 360.0),
                "circular_led_spacing": getattr(self.metadata, 'circular_led_spacing', None),
                "circular_mapping_table": getattr(self.metadata, 'circular_mapping_table', None),
                # Multi-ring layout (Budurasmala)
                "multi_ring_count": getattr(self.metadata, 'multi_ring_count', None),
                "ring_led_counts": getattr(self.metadata, 'ring_led_counts', None),
                "ring_radii": getattr(self.metadata, 'ring_radii', None),
                "ring_spacing": getattr(self.metadata, 'ring_spacing', None),
                # Radial ray layout (Budurasmala)
                "ray_count": getattr(self.metadata, 'ray_count', None),
                "leds_per_ray": getattr(self.metadata, 'leds_per_ray', None),
                "ray_spacing_angle": getattr(self.metadata, 'ray_spacing_angle', None),
                # Custom LED positions (Budurasmala)
                "custom_led_positions": getattr(self.metadata, 'custom_led_positions', None),
                "led_position_units": getattr(self.metadata, 'led_position_units', 'grid'),
                "custom_position_center_x": getattr(self.metadata, 'custom_position_center_x', None),
                "custom_position_center_y": getattr(self.metadata, 'custom_position_center_y', None),
                # Irregular/custom shape support (LED Build-style)
                "irregular_shape_enabled": getattr(self.metadata, 'irregular_shape_enabled', False),
                "active_cell_coordinates": getattr(self.metadata, 'active_cell_coordinates', None),
                "background_image_path": getattr(self.metadata, 'background_image_path', None),
                "background_image_scale": getattr(self.metadata, 'background_image_scale', 1.0),
                "background_image_offset_x": getattr(self.metadata, 'background_image_offset_x', 0.0),
                "background_image_offset_y": getattr(self.metadata, 'background_image_offset_y', 0.0),
            },
            "frames": [
                {
                    "pixels": f.pixels,
                    "duration_ms": f.duration_ms
                }
                for f in self.frames
            ],
            "lms_pattern_instructions": getattr(self, 'lms_pattern_instructions', []),
            "scratchpads": {
                str(slot): [list(pixel) for pixel in pixels]
                for slot, pixels in getattr(self, 'scratchpads', {}).items()
            },
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'Pattern':
        """Deserialize from dictionary"""
        version = data.get('version', '1.0')
        
        # Parse metadata
        meta_dict = data.get('metadata', {})
        meta = PatternMetadata(
            width=meta_dict.get('width', 1),
            height=meta_dict.get('height', 1),
            color_order=meta_dict.get('color_order', 'RGB'),
            fps=meta_dict.get('fps'),
            total_ms=meta_dict.get('total_ms'),
            brightness=meta_dict.get('brightness', 1.0),
            wiring_mode=meta_dict.get('wiring_mode', 'Row-major'),
            data_in_corner=meta_dict.get('data_in_corner', 'LT'),
            custom_mapping=meta_dict.get('custom_mapping', None),
            already_unwrapped=meta_dict.get('already_unwrapped', False),
            original_wiring_mode=meta_dict.get('original_wiring_mode', None),
            original_data_in_corner=meta_dict.get('original_data_in_corner', None),
            # Advanced brightness settings
            brightness_curve=meta_dict.get('brightness_curve', 'gamma_corrected'),
            led_type=meta_dict.get('led_type', 'ws2812'),
            per_channel_brightness=meta_dict.get('per_channel_brightness', False),
            red_brightness=meta_dict.get('red_brightness', 1.0),
            green_brightness=meta_dict.get('green_brightness', 1.0),
            blue_brightness=meta_dict.get('blue_brightness', 1.0),
            # Speed control settings
            speed_curve=meta_dict.get('speed_curve', 'linear'),
            variable_speed=meta_dict.get('variable_speed', False),
            speed_keyframes=meta_dict.get('speed_keyframes', []),
            target_fps=meta_dict.get('target_fps', None),
            # Interpolation settings
            interpolation_enabled=meta_dict.get('interpolation_enabled', False),
            interpolation_factor=meta_dict.get('interpolation_factor', 1.0),
            # Dimension detection metadata
            dimension_source=meta_dict.get('dimension_source', 'unknown'),
            dimension_confidence=meta_dict.get('dimension_confidence', 0.0),
            source_format=meta_dict.get('source_format'),
            source_path=meta_dict.get('source_path'),
            # Detection hints
            wiring_mode_hint=meta_dict.get('wiring_mode_hint'),
            data_in_corner_hint=meta_dict.get('data_in_corner_hint'),
            hint_confidence=meta_dict.get('hint_confidence', 0.0),
            # Circular layout
            layout_type=meta_dict.get('layout_type', 'rectangular'),
            circular_led_count=meta_dict.get('circular_led_count'),
            circular_radius=meta_dict.get('circular_radius'),
            circular_inner_radius=meta_dict.get('circular_inner_radius'),
            circular_start_angle=meta_dict.get('circular_start_angle', 0.0),
            circular_end_angle=meta_dict.get('circular_end_angle', 360.0),
            circular_led_spacing=meta_dict.get('circular_led_spacing'),
            circular_mapping_table=meta_dict.get('circular_mapping_table'),
            # Multi-ring layout (Budurasmala)
            multi_ring_count=meta_dict.get('multi_ring_count'),
            ring_led_counts=meta_dict.get('ring_led_counts'),
            ring_radii=meta_dict.get('ring_radii'),
            ring_spacing=meta_dict.get('ring_spacing'),
            # Radial ray layout (Budurasmala)
            ray_count=meta_dict.get('ray_count'),
            leds_per_ray=meta_dict.get('leds_per_ray'),
            ray_spacing_angle=meta_dict.get('ray_spacing_angle'),
            # Custom LED positions (Budurasmala)
            custom_led_positions=meta_dict.get('custom_led_positions'),
            led_position_units=meta_dict.get('led_position_units', 'grid'),
            custom_position_center_x=meta_dict.get('custom_position_center_x'),
            custom_position_center_y=meta_dict.get('custom_position_center_y'),
            # Irregular/custom shape support (LED Build-style)
            irregular_shape_enabled=meta_dict.get('irregular_shape_enabled', False),
            active_cell_coordinates=meta_dict.get('active_cell_coordinates'),
            background_image_path=meta_dict.get('background_image_path'),
            background_image_scale=meta_dict.get('background_image_scale', 1.0),
            background_image_offset_x=meta_dict.get('background_image_offset_x', 0.0),
            background_image_offset_y=meta_dict.get('background_image_offset_y', 0.0),
        )
        
        # Parse frames
        frames_data = data.get('frames', [])
        frames = [
            Frame(
                pixels=[tuple(p) if isinstance(p, list) else p for p in f['pixels']],
                duration_ms=f['duration_ms']
            )
            for f in frames_data
        ]
        
        scratchpads_raw = data.get('scratchpads', {})
        scratchpads: Dict[str, List[Tuple[int, int, int]]] = {}
        for slot, pixels in scratchpads_raw.items():
            normalized = []
            for pixel in pixels:
                if isinstance(pixel, tuple):
                    normalized.append(pixel)
                elif isinstance(pixel, list):
                    normalized.append(tuple(pixel))
            scratchpads[str(slot)] = normalized

        pattern = Pattern(
            id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', 'Untitled'),
            metadata=meta,
            frames=frames,
            scratchpads=scratchpads,
        )
        pattern.lms_pattern_instructions = data.get('lms_pattern_instructions', [])
        return pattern
    
    def save_to_file(self, filepath: str):
        """Save pattern to JSON project file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def load_from_file(filepath: str) -> 'Pattern':
        """Load pattern from JSON project file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return Pattern.from_dict(data)
    
    def get_frame_at_time(self, time_ms: int) -> Optional[int]:
        """Get frame index at specified time in milliseconds"""
        if time_ms < 0 or self.frame_count == 0:
            return None
        
        elapsed = 0
        for i, frame in enumerate(self.frames):
            elapsed += frame.duration_ms
            if time_ms < elapsed:
                return i
        
        # Time beyond pattern duration, return last frame
        return self.frame_count - 1
    
    def estimate_memory_bytes(self) -> int:
        """Estimate memory usage in bytes"""
        # Header: num_leds (2) + num_frames (2)
        size = 4
        
        # Each frame: delay (2) + RGB data (3 * led_count)
        for frame in self.frames:
            size += 2 + (frame.led_count * 3)
        
        return size
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate pattern for issues
        Returns: (is_valid, list_of_warnings)
        """
        warnings = []
        
        # Check frame count
        if self.frame_count == 0:
            warnings.append("Pattern has no frames")
        
        # Check LED count consistency
        expected_leds = self.metadata.led_count
        for i, frame in enumerate(self.frames):
            if frame.led_count != expected_leds:
                warnings.append(
                    f"Frame {i}: has {frame.led_count} LEDs, expected {expected_leds}"
                )
        
        # Check for very short frames
        for i, frame in enumerate(self.frames):
            if frame.duration_ms < 5:
                warnings.append(
                    f"Frame {i}: very short duration ({frame.duration_ms}ms), "
                    "may not display properly"
                )
        
        # Check for very long frames
        for i, frame in enumerate(self.frames):
            if frame.duration_ms > 60000:
                warnings.append(
                    f"Frame {i}: very long duration ({frame.duration_ms}ms), "
                    "may appear static"
                )
        
        # Check total size
        size_kb = self.estimate_memory_bytes() / 1024.0
        if size_kb > 900:
            warnings.append(
                f"Pattern size is large ({size_kb:.1f}KB), "
                "may not fit on some chips"
            )
        
        return (len(warnings) == 0, warnings)


# Convenience functions
def create_solid_color_pattern(
    led_count: int,
    color: Tuple[int, int, int],
    duration_ms: int = 1000,
    name: str = "Solid Color"
) -> Pattern:
    """Create a pattern with single solid color"""
    frame = Frame(
        pixels=[color] * led_count,
        duration_ms=duration_ms
    )
    
    return Pattern(
        name=name,
        metadata=PatternMetadata(width=led_count),
        frames=[frame]
    )


def create_test_pattern(led_count: int = 10, frame_count: int = 10) -> Pattern:
    """Create a test pattern (rainbow cycle)"""
    import math
    
    frames = []
    for f in range(frame_count):
        pixels = []
        for i in range(led_count):
            # Rainbow effect
            hue = ((i / led_count) + (f / frame_count)) % 1.0
            r = int(255 * (0.5 + 0.5 * math.sin(2 * math.pi * hue)))
            g = int(255 * (0.5 + 0.5 * math.sin(2 * math.pi * (hue + 0.333))))
            b = int(255 * (0.5 + 0.5 * math.sin(2 * math.pi * (hue + 0.666))))
            pixels.append((r, g, b))
        
        frames.append(Frame(pixels=pixels, duration_ms=50))
    
    return Pattern(
        name="Test Rainbow",
        metadata=PatternMetadata(width=led_count),
        frames=frames
    )


def load_pattern_from_file(file_path: str) -> Pattern:
    """
    Load pattern from file (supports multiple formats)
    
    Args:
        file_path: Path to pattern file
        
    Returns:
        Pattern object
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is not supported
    """
    from parsers.parser_registry import parse_pattern_file
    from pathlib import Path
    
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"Pattern file not found: {file_path}")
    
    # Delegate to parser registry which supports binary formats (e.g., .bin)
    # This will still handle .json/.txt/.dat via their respective parsers.
    return parse_pattern_file(str(p))


def _load_json_pattern(file_path: Path) -> Pattern:
    """Load pattern from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Convert JSON data to Pattern object
    frames = []
    for frame_data in data.get('frames', []):
        pixels = [tuple(pixel) for pixel in frame_data.get('pixels', [])]
        duration = frame_data.get('duration_ms', 100)
        frames.append(Frame(pixels=pixels, duration_ms=duration))
    
    metadata = PatternMetadata(
        width=data.get('width', 8),
        height=data.get('height', 8),
        brightness=data.get('brightness', 1.0)
    )
    
    return Pattern(
        name=data.get('name', file_path.stem),
        metadata=metadata,
        frames=frames
    )


def _load_text_pattern(file_path: Path) -> Pattern:
    """Load pattern from text file"""
    frames = []
    current_frame = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if line.startswith('FRAME:'):
                if current_frame:
                    frames.append(Frame(pixels=current_frame, duration_ms=100))
                current_frame = []
            elif line.startswith('DELAY:'):
                # Set delay for current frame
                if frames:
                    frames[-1].duration_ms = int(line.split(':')[1])
            else:
                # Parse RGB values
                try:
                    parts = line.split(',')
                    if len(parts) >= 3:
                        r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
                        current_frame.append((r, g, b))
                except ValueError:
                    continue
    
    # Add last frame
    if current_frame:
        frames.append(Frame(pixels=current_frame, duration_ms=100))
    
    if not frames:
        raise ValueError("No valid pattern data found in file")
    
    # Determine dimensions
    led_count = len(frames[0].pixels)
    width = int(led_count ** 0.5) if led_count > 1 else 1
    height = led_count // width
    
    return Pattern(
        name=file_path.stem,
        metadata=PatternMetadata(width=width, height=height),
        frames=frames
    )


def _auto_detect_and_load(file_path: Path) -> Pattern:
    """Auto-detect file format and load"""
    # Kept for backward compatibility but route through registry for robustness
    from parsers.parser_registry import parse_pattern_file
    return parse_pattern_file(str(file_path))


def auto_detect_pattern_info(file_path: str) -> Dict:
    """
    Auto-detect pattern information from file
    
    Args:
        file_path: Path to pattern file
        
    Returns:
        Dictionary with detected information
    """
    from pathlib import Path
    
    file_path = Path(file_path)
    if not file_path.exists():
        return {"error": "File not found"}
    
    try:
        # Use registry-backed loader to support binary formats
        pattern = load_pattern_from_file(str(file_path))
        return {
            "name": pattern.name,
            "width": pattern.metadata.width,
            "height": pattern.metadata.height,
            "frame_count": pattern.frame_count,
            "led_count": pattern.led_count,
            "duration_ms": pattern.total_duration_ms,
            "brightness": pattern.metadata.brightness,
            "file_size": file_path.stat().st_size,
            "format": "detected"
        }
    except Exception as e:
        return {"error": str(e)}


class BrightnessCurve(enum.Enum):
    """Brightness curve types for LED control"""
    LINEAR = "linear"
    GAMMA_CORRECTED = "gamma_corrected"
    LOGARITHMIC = "logarithmic"
    EXPONENTIAL = "exponential"
    S_CURVE = "s_curve"


class HardwareBrightnessMapper:
    """Maps software brightness to hardware brightness values"""
    
    def __init__(self, curve_type: BrightnessCurve = BrightnessCurve.GAMMA_CORRECTED):
        self.curve_type = curve_type
    
    def map_brightness(self, software_brightness: float) -> int:
        """
        Map software brightness (0.0-1.0) to hardware brightness (0-255)
        
        Args:
            software_brightness: Software brightness value (0.0-1.0)
            
        Returns:
            Hardware brightness value (0-255)
        """
        if not (0.0 <= software_brightness <= 1.0):
            raise ValueError(f"Software brightness must be 0.0-1.0, got {software_brightness}")
        
        if self.curve_type == BrightnessCurve.LINEAR:
            return int(software_brightness * 255)
        
        elif self.curve_type == BrightnessCurve.GAMMA_CORRECTED:
            # Gamma correction (gamma = 2.2)
            gamma_corrected = software_brightness ** 2.2
            return int(gamma_corrected * 255)
        
        elif self.curve_type == BrightnessCurve.LOGARITHMIC:
            # Logarithmic curve
            import math
            log_brightness = math.log(1 + software_brightness * 9) / math.log(10)
            return int(log_brightness * 255)
        
        elif self.curve_type == BrightnessCurve.EXPONENTIAL:
            # Exponential curve
            exp_brightness = software_brightness ** 0.5
            return int(exp_brightness * 255)
        
        elif self.curve_type == BrightnessCurve.S_CURVE:
            # S-curve (sigmoid-like)
            import math
            s_brightness = 1 / (1 + math.exp(-10 * (software_brightness - 0.5)))
            return int(s_brightness * 255)
        
        else:
            # Default to linear
            return int(software_brightness * 255)
    
    def apply_to_pattern(self, pattern: 'Pattern') -> 'Pattern':
        """
        Apply brightness mapping to a pattern
        
        Args:
            pattern: Pattern to apply brightness mapping to
            
        Returns:
            New pattern with mapped brightness
        """
        new_frames = []
        
        for frame in pattern.frames:
            new_pixels = []
            for r, g, b in frame.pixels:
                # Apply brightness mapping to each color channel
                brightness = pattern.metadata.brightness
                mapped_brightness = self.map_brightness(brightness)
                
                # Scale RGB values by mapped brightness
                new_r = int((r * mapped_brightness) / 255)
                new_g = int((g * mapped_brightness) / 255)
                new_b = int((b * mapped_brightness) / 255)
                
                new_pixels.append((new_r, new_g, new_b))
            
            new_frames.append(Frame(pixels=new_pixels, duration_ms=frame.duration_ms))
        
        return Pattern(
            name=pattern.name,
            metadata=pattern.metadata,
            frames=new_frames
        )


class SpeedController:
    """Controls animation speed and timing"""
    
    def __init__(self, base_fps: float = 30.0):
        self.base_fps = base_fps
        self.speed_multiplier = 1.0
        self.paused = False
    
    @staticmethod
    def linear_easing(t: float) -> float:
        """Linear easing function"""
        return t
    
    @staticmethod
    def ease_in_quad(t: float) -> float:
        """Quadratic ease-in"""
        return t * t
    
    @staticmethod
    def ease_out_quad(t: float) -> float:
        """Quadratic ease-out"""
        return 1 - (1 - t) * (1 - t)
    
    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        """Quadratic ease-in-out"""
        return 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2
    
    @staticmethod
    def ease_in_cubic(t: float) -> float:
        """Cubic ease-in"""
        return t * t * t
    
    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """Cubic ease-out"""
        return 1 - pow(1 - t, 3)
    
    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """Cubic ease-in-out"""
        return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2
    
    def set_speed_multiplier(self, multiplier: float):
        """Set speed multiplier (0.1 = 10% speed, 2.0 = 200% speed)"""
        self.speed_multiplier = max(0.1, min(10.0, multiplier))
    
    def pause(self):
        """Pause animation"""
        self.paused = True
    
    def resume(self):
        """Resume animation"""
        self.paused = False
    
    def get_effective_fps(self) -> float:
        """Get effective FPS based on speed multiplier"""
        if self.paused:
            return 0.0
        return self.base_fps * self.speed_multiplier
    
    def get_frame_duration_ms(self) -> float:
        """Get frame duration in milliseconds"""
        if self.paused:
            return float('inf')
        return 1000.0 / self.get_effective_fps()
    
    def apply_to_pattern(self, pattern: 'Pattern') -> 'Pattern':
        """
        Apply speed control to a pattern
        
        Args:
            pattern: Pattern to apply speed control to
            
        Returns:
            New pattern with adjusted timing
        """
        if self.speed_multiplier == 1.0 and not self.paused:
            return pattern  # No changes needed
        
        new_frames = []
        for frame in pattern.frames:
            if self.paused:
                # Set very long duration for paused state
                new_duration = 999999
            else:
                # Adjust duration based on speed multiplier
                new_duration = int(frame.duration_ms / self.speed_multiplier)
            
            new_frames.append(Frame(
                pixels=frame.pixels,
                duration_ms=new_duration
            ))
        
        return Pattern(
            name=pattern.name,
            metadata=pattern.metadata,
            frames=new_frames
        )

