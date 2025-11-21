"""
Image Exporter - Export frames as bitmap images and animated GIFs.

This module provides functionality to export LED matrix frames as PNG, BMP images
or animated GIFs.
"""

from __future__ import annotations

import os
from typing import List, Tuple
from PIL import Image
from core.pattern import Pattern, Frame

RGB = Tuple[int, int, int]


class ImageExporter:
    """Handles exporting LED matrix patterns to image formats."""
    
    @staticmethod
    def export_frame_as_image(
        frame: Frame,
        filepath: str,
        width: int,
        height: int,
        scale_factor: int = 1,
        format: str = "PNG"
    ) -> bool:
        """
        Export a single frame as an image file.
        
        Args:
            frame: Frame to export
            filepath: Output file path
            width: Matrix width
            height: Matrix height
            scale_factor: Pixel scaling factor (1 = 1 pixel per LED, 10 = 10x10 pixels per LED)
            format: Image format ("PNG", "BMP")
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create image
            img_width = width * scale_factor
            img_height = height * scale_factor
            img = Image.new("RGB", (img_width, img_height), (0, 0, 0))
            
            # Draw pixels
            pixels = frame.pixels
            for y in range(height):
                for x in range(width):
                    idx = y * width + x
                    if idx < len(pixels):
                        r, g, b = pixels[idx]
                        # Draw scaled pixel
                        x_start = x * scale_factor
                        y_start = y * scale_factor
                        for py in range(scale_factor):
                            for px in range(scale_factor):
                                img.putpixel((x_start + px, y_start + py), (r, g, b))
            
            # Save image
            img.save(filepath, format=format)
            return True
        
        except Exception as e:
            raise Exception(f"Failed to export image: {e}")
    
    @staticmethod
    def export_animation_as_gif(
        pattern: Pattern,
        filepath: str,
        scale_factor: int = 1,
        loop_count: int = 0
    ) -> bool:
        """
        Export pattern as animated GIF.
        
        Args:
            pattern: Pattern to export
            filepath: Output file path
            scale_factor: Pixel scaling factor
            loop_count: Number of loops (0 = infinite)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not pattern.frames:
                raise Exception("Pattern has no frames")
            
            width = pattern.metadata.width
            height = pattern.metadata.height
            img_width = width * scale_factor
            img_height = height * scale_factor
            
            # Create frames
            images = []
            durations = []
            
            for frame in pattern.frames:
                # Create image
                img = Image.new("RGB", (img_width, img_height), (0, 0, 0))
                
                # Draw pixels
                pixels = frame.pixels
                for y in range(height):
                    for x in range(width):
                        idx = y * width + x
                        if idx < len(pixels):
                            r, g, b = pixels[idx]
                            # Draw scaled pixel
                            x_start = x * scale_factor
                            y_start = y * scale_factor
                            for py in range(scale_factor):
                                for px in range(scale_factor):
                                    img.putpixel((x_start + px, y_start + py), (r, g, b))
                
                images.append(img)
                # Convert milliseconds to centiseconds (GIF uses centiseconds)
                durations.append(max(1, frame.duration_ms // 10))
            
            # Save as animated GIF
            if len(images) == 1:
                # Single frame, save as static image
                images[0].save(filepath, format="GIF")
            else:
                # Multiple frames, save as animated GIF
                images[0].save(
                    filepath,
                    format="GIF",
                    save_all=True,
                    append_images=images[1:],
                    duration=durations,
                    loop=loop_count
                )
            
            return True
        
        except Exception as e:
            raise Exception(f"Failed to export GIF: {e}")
    
    @staticmethod
    def get_supported_formats() -> List[str]:
        """Get list of supported export formats."""
        return ["PNG", "BMP", "GIF"]

