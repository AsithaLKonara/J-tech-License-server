"""
Circular Text Renderer - Render text on circular/curved matrix layouts.

This module provides utilities for rendering text on Budurasmala circular matrices,
including curved text layouts and hybrid ring+matrix arrangements.
"""

from __future__ import annotations

import math
from typing import List, Tuple, Optional
from core.pattern import PatternMetadata, Frame
from domain.text.text_renderer import TextRenderer, TextRenderOptions
from domain.text.glyph_provider import GlyphProvider

RGB = Tuple[int, int, int]


class CircularTextRenderer:
    """Render text on circular/curved matrix layouts for Budurasmala."""
    
    def __init__(self):
        self.text_renderer = TextRenderer()
    
    def render_text_on_circular_matrix(
        self,
        text: str,
        metadata: PatternMetadata,
        frame: Frame,
        color: RGB = (255, 255, 255),
        start_angle: float = 0.0,
        radius: Optional[float] = None,
        font_size: int = 5
    ) -> Frame:
        """
        Render text on a circular matrix layout.
        
        Text is rendered along a circular path, with each character positioned
        at appropriate angles around the circle.
        
        Args:
            text: Text to render
            metadata: PatternMetadata with circular layout
            frame: Frame to modify
            color: Text color (RGB)
            start_angle: Starting angle in degrees (0 = top, 90 = right)
            radius: Radius for text (None = use circular_radius)
            font_size: Character size (5x7 default)
            
        Returns:
            Modified frame with text rendered
        """
        from copy import deepcopy
        
        new_frame = deepcopy(frame)
        
        if not text or not metadata.circular_mapping_table:
            return new_frame
        
        # Get radius
        if radius is None:
            radius = metadata.circular_radius or (min(metadata.width, metadata.height) / 2.0 - 1.0)
        
        # Calculate center
        center_x = (metadata.width - 1) / 2.0
        center_y = (metadata.height - 1) / 2.0
        
        # Character dimensions
        char_width = font_size
        char_height = font_size
        
        # Calculate angle per character (distribute text around circle)
        total_angle = 360.0 if metadata.circular_end_angle >= metadata.circular_start_angle + 360 else (
            metadata.circular_end_angle - metadata.circular_start_angle
        )
        angle_per_char = total_angle / max(1, len(text))
        
        # Use glyph provider for character rendering
        glyph_provider = GlyphProvider(width=char_width, height=char_height)
        
        # Render each character
        for char_idx, char in enumerate(text):
            # Calculate angle for this character
            char_angle_deg = start_angle + (char_idx * angle_per_char)
            char_angle_rad = math.radians(char_angle_deg)
            
            # Character position on circle
            char_center_x = center_x + radius * math.cos(char_angle_rad)
            char_center_y = center_y + radius * math.sin(char_angle_rad)
            
            # Get glyph
            glyph = glyph_provider.glyph(char)
            
            # Render glyph pixels
            for gy, row in enumerate(glyph):
                for gx, pixel in enumerate(row):
                    if pixel:
                        # Calculate pixel position relative to character center
                        pixel_x = char_center_x + (gx - char_width / 2.0)
                        pixel_y = char_center_y + (gy - char_height / 2.0)
                        
                        # Find nearest grid cell
                        grid_x = int(round(pixel_x))
                        grid_y = int(round(pixel_y))
                        
                        if 0 <= grid_x < metadata.width and 0 <= grid_y < metadata.height:
                            # Find LED index that maps to this grid cell
                            led_idx = self._find_led_for_grid(metadata, grid_x, grid_y)
                            if led_idx is not None and led_idx < len(new_frame.pixels):
                                new_frame.pixels[led_idx] = color
        
        return new_frame
    
    def render_text_on_curved_matrix(
        self,
        text: str,
        metadata: PatternMetadata,
        frame: Frame,
        color: RGB = (255, 255, 255),
        curve_radius: Optional[float] = None,
        font_size: int = 5
    ) -> Frame:
        """
        Render text on a curved matrix (text follows a curved path).
        
        Args:
            text: Text to render
            metadata: PatternMetadata
            frame: Frame to modify
            color: Text color
            curve_radius: Curvature radius (None = auto)
            font_size: Character size
            
        Returns:
            Modified frame
        """
        from copy import deepcopy
        
        new_frame = deepcopy(frame)
        
        if not text:
            return new_frame
        
        # Use standard text rendering but on curved path
        char_width = font_size
        char_height = font_size
        
        # Calculate curve parameters
        if curve_radius is None:
            curve_radius = min(metadata.width, metadata.height) / 3.0
        
        center_x = metadata.width / 2.0
        center_y = metadata.height / 2.0
        
        # Render text along curve
        glyph_provider = GlyphProvider(width=char_width, height=char_height)
        text_width = len(text) * char_width
        
        for char_idx, char in enumerate(text):
            # Position along curve (from left to right, curved downward)
            t = char_idx / max(1, len(text) - 1)  # 0 to 1
            x_offset = (t - 0.5) * text_width
            
            # Calculate y offset for curve (parabolic curve)
            y_offset = (x_offset / curve_radius) ** 2 * curve_radius * 0.3
            
            char_x = center_x + x_offset
            char_y = center_y + y_offset
            
            # Get glyph
            glyph = glyph_provider.glyph(char)
            
            # Render glyph
            for gy, row in enumerate(glyph):
                for gx, pixel in enumerate(row):
                    if pixel:
                        pixel_x = int(round(char_x + gx - char_width / 2.0))
                        pixel_y = int(round(char_y + gy - char_height / 2.0))
                        
                        if 0 <= pixel_x < metadata.width and 0 <= pixel_y < metadata.height:
                            idx = pixel_y * metadata.width + pixel_x
                            if idx < len(new_frame.pixels):
                                new_frame.pixels[idx] = color
        
        return new_frame
    
    def _find_led_for_grid(
        self,
        metadata: PatternMetadata,
        grid_x: int,
        grid_y: int
    ) -> Optional[int]:
        """Find LED index that maps to given grid coordinates."""
        if not metadata.circular_mapping_table:
            # Fallback to standard row-major
            if 0 <= grid_x < metadata.width and 0 <= grid_y < metadata.height:
                return grid_y * metadata.width + grid_x
            return None
        
        # Search mapping table
        for led_idx, (mapped_x, mapped_y) in enumerate(metadata.circular_mapping_table):
            if mapped_x == grid_x and mapped_y == grid_y:
                return led_idx
        
        return None

