"""
Image Importer - Import bitmap images and animated GIFs.

This module provides functionality to import PNG, BMP, JPEG images and
animated GIFs, converting them to LED matrix frames.
"""

from __future__ import annotations

import os
from typing import List, Tuple, Optional
from PIL import Image
from core.pattern import Frame

RGB = Tuple[int, int, int]


class ImageImporter:
    """Handles importing images and GIFs into LED matrix patterns."""
    
    @staticmethod
    def import_image(
        filepath: str,
        target_width: int,
        target_height: int,
        resize_mode: str = "fit"
    ) -> List[RGB]:
        """
        Import a single image file and convert to RGB pixel array.
        
        Args:
            filepath: Path to image file (PNG, BMP, JPEG)
            target_width: Target matrix width
            target_height: Target matrix height
            resize_mode: "fit" (maintain aspect, pad), "stretch" (fill entire matrix), "crop" (center crop)
        
        Returns:
            List of RGB tuples in row-major order
        """
        try:
            img = Image.open(filepath)
            
            # Convert to RGB if needed
            if img.mode != "RGB":
                img = img.convert("RGB")
            
            # Resize according to mode
            if resize_mode == "stretch":
                img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            elif resize_mode == "crop":
                # Center crop to maintain aspect ratio
                aspect = img.width / img.height
                target_aspect = target_width / target_height
                
                if aspect > target_aspect:
                    # Image is wider, crop width
                    new_width = int(img.height * target_aspect)
                    left = (img.width - new_width) // 2
                    img = img.crop((left, 0, left + new_width, img.height))
                else:
                    # Image is taller, crop height
                    new_height = int(img.width / target_aspect)
                    top = (img.height - new_height) // 2
                    img = img.crop((0, top, img.width, top + new_height))
                
                img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            else:  # fit mode
                # Maintain aspect ratio, pad with black
                aspect = img.width / img.height
                target_aspect = target_width / target_height
                
                if aspect > target_aspect:
                    # Image is wider, fit to width
                    new_width = target_width
                    new_height = int(target_width / aspect)
                else:
                    # Image is taller, fit to height
                    new_height = target_height
                    new_width = int(target_height * aspect)
                
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Create new image with black background
                padded = Image.new("RGB", (target_width, target_height), (0, 0, 0))
                x_offset = (target_width - new_width) // 2
                y_offset = (target_height - new_height) // 2
                padded.paste(img, (x_offset, y_offset))
                img = padded
            
            # Convert to pixel list (row-major)
            pixels: List[RGB] = []
            for y in range(target_height):
                for x in range(target_width):
                    r, g, b = img.getpixel((x, y))
                    pixels.append((r, g, b))
            
            return pixels
        
        except Exception as e:
            raise Exception(f"Failed to import image: {e}")
    
    @staticmethod
    def import_gif(
        filepath: str,
        target_width: int,
        target_height: int,
        resize_mode: str = "fit",
        extract_all_frames: bool = True
    ) -> List[List[RGB]]:
        """
        Import animated GIF and extract frames.
        
        Args:
            filepath: Path to GIF file
            target_width: Target matrix width
            target_height: Target matrix height
            resize_mode: "fit", "stretch", or "crop"
            extract_all_frames: If True, extract all frames; if False, extract first frame only
        
        Returns:
            List of frame pixel arrays (each is a list of RGB tuples)
        """
        try:
            frames: List[List[RGB]] = []
            img = Image.open(filepath)
            
            frame_count = 0
            while True:
                # Convert to RGB if needed
                frame_img = img.copy()
                if frame_img.mode != "RGB":
                    frame_img = frame_img.convert("RGB")
                
                # Resize using same logic as import_image
                if resize_mode == "stretch":
                    frame_img = frame_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                elif resize_mode == "crop":
                    aspect = frame_img.width / frame_img.height
                    target_aspect = target_width / target_height
                    
                    if aspect > target_aspect:
                        new_width = int(frame_img.height * target_aspect)
                        left = (frame_img.width - new_width) // 2
                        frame_img = frame_img.crop((left, 0, left + new_width, frame_img.height))
                    else:
                        new_height = int(frame_img.width / target_aspect)
                        top = (frame_img.height - new_height) // 2
                        frame_img = frame_img.crop((0, top, frame_img.width, top + new_height))
                    
                    frame_img = frame_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                else:  # fit mode
                    aspect = frame_img.width / frame_img.height
                    target_aspect = target_width / target_height
                    
                    if aspect > target_aspect:
                        new_width = target_width
                        new_height = int(target_width / aspect)
                    else:
                        new_height = target_height
                        new_width = int(target_height * aspect)
                    
                    frame_img = frame_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    padded = Image.new("RGB", (target_width, target_height), (0, 0, 0))
                    x_offset = (target_width - new_width) // 2
                    y_offset = (target_height - new_height) // 2
                    padded.paste(frame_img, (x_offset, y_offset))
                    frame_img = padded
                
                # Convert to pixel list
                pixels: List[RGB] = []
                for y in range(target_height):
                    for x in range(target_width):
                        r, g, b = frame_img.getpixel((x, y))
                        pixels.append((r, g, b))
                
                frames.append(pixels)
                frame_count += 1
                
                if not extract_all_frames or frame_count >= 1000:  # Limit to prevent memory issues
                    break
                
                try:
                    img.seek(img.tell() + 1)
                except EOFError:
                    break
            
            return frames
        
        except Exception as e:
            raise Exception(f"Failed to import GIF: {e}")
    
    @staticmethod
    def is_gif(filepath: str) -> bool:
        """Check if file is a GIF."""
        try:
            img = Image.open(filepath)
            return img.format == "GIF" and getattr(img, "is_animated", False)
        except Exception:
            return False
    
    @staticmethod
    def get_supported_formats() -> List[str]:
        """Get list of supported image formats."""
        return ["PNG", "BMP", "JPEG", "JPG", "GIF"]

