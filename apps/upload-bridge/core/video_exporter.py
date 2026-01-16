"""
Video Exporter - Export patterns as video files.

This module provides functionality to export LED matrix patterns as video files
(MP4, AVI, etc.).
"""

from __future__ import annotations

import os
from typing import Optional
from PIL import Image
from core.pattern import Pattern, Frame

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import imageio
    IMAGEIO_AVAILABLE = True
except ImportError:
    IMAGEIO_AVAILABLE = False


class VideoExporter:
    """Handles exporting LED matrix patterns to video formats."""
    
    @staticmethod
    def export_pattern_as_video(
        pattern: Pattern,
        filepath: str,
        scale_factor: int = 10,
        fps: int = 10,
        codec: str = "mp4v",
        format: str = "mp4"
    ) -> bool:
        """
        Export a pattern as a video file.
        
        Args:
            pattern: Pattern to export
            filepath: Output file path
            scale_factor: Pixel scaling factor (1 = 1 pixel per LED, 10 = 10x10 pixels per LED)
            fps: Frames per second
            codec: Video codec (e.g., "mp4v", "XVID", "H264")
            format: Video format ("mp4", "avi", "mov")
        
        Returns:
            True if successful, False otherwise
        """
        if CV2_AVAILABLE:
            return VideoExporter._export_with_opencv(pattern, filepath, scale_factor, fps, codec, format)
        elif IMAGEIO_AVAILABLE:
            return VideoExporter._export_with_imageio(pattern, filepath, scale_factor, fps, format)
        else:
            raise ImportError(
                "Video export requires either 'opencv-python' or 'imageio' package. "
                "Install with: pip install opencv-python or pip install imageio"
            )
    
    @staticmethod
    def _export_with_opencv(
        pattern: Pattern,
        filepath: str,
        scale_factor: int,
        fps: int,
        codec: str,
        format: str
    ) -> bool:
        """Export using OpenCV."""
        try:
            width = pattern.metadata.width
            height = pattern.metadata.height
            video_width = width * scale_factor
            video_height = height * scale_factor
            
            # Determine fourcc codec
            fourcc_map = {
                "mp4v": cv2.VideoWriter_fourcc(*'mp4v'),
                "XVID": cv2.VideoWriter_fourcc(*'XVID'),
                "H264": cv2.VideoWriter_fourcc(*'H264'),
                "X264": cv2.VideoWriter_fourcc(*'X264'),
            }
            fourcc = fourcc_map.get(codec, cv2.VideoWriter_fourcc(*'mp4v'))
            
            # Create video writer
            video_writer = cv2.VideoWriter(filepath, fourcc, fps, (video_width, video_height))
            
            if not video_writer.isOpened():
                raise Exception("Failed to open video writer")
            
            # Write frames
            for frame in pattern.frames:
                # Create image
                img = Image.new("RGB", (video_width, video_height), (0, 0, 0))
                
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
                
                # Convert PIL Image to OpenCV format (BGR)
                import numpy as np
                img_array = np.array(img)
                img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                
                # Write frame (repeat based on duration)
                frame_duration_sec = frame.duration_ms / 1000.0
                frame_count = max(1, int(frame_duration_sec * fps))
                for _ in range(frame_count):
                    video_writer.write(img_bgr)
            
            video_writer.release()
            return True
            
        except Exception as e:
            raise Exception(f"Failed to export video with OpenCV: {e}")
    
    @staticmethod
    def _export_with_imageio(
        pattern: Pattern,
        filepath: str,
        scale_factor: int,
        fps: int,
        format: str
    ) -> bool:
        """Export using imageio."""
        try:
            width = pattern.metadata.width
            height = pattern.metadata.height
            video_width = width * scale_factor
            video_height = height * scale_factor
            
            # Prepare frames
            frames_data = []
            for frame in pattern.frames:
                # Create image
                img = Image.new("RGB", (video_width, video_height), (0, 0, 0))
                
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
                
                # Convert to numpy array
                import numpy as np
                img_array = np.array(img)
                
                # Repeat frame based on duration
                frame_duration_sec = frame.duration_ms / 1000.0
                frame_count = max(1, int(frame_duration_sec * fps))
                for _ in range(frame_count):
                    frames_data.append(img_array)
            
            # Write video
            imageio.mimwrite(filepath, frames_data, fps=fps, codec='libx264' if format == 'mp4' else None)
            return True
            
        except Exception as e:
            raise Exception(f"Failed to export video with imageio: {e}")
    
    @staticmethod
    def get_supported_formats() -> list[str]:
        """Get list of supported video formats."""
        formats = []
        if CV2_AVAILABLE:
            formats.extend(["mp4", "avi", "mov"])
        if IMAGEIO_AVAILABLE:
            formats.extend(["mp4", "mov", "gif"])
        return list(set(formats))  # Remove duplicates

