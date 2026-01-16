"""
Media Converter - Convert images, GIFs, and videos to LED patterns
Supports PNG, JPG, BMP, GIF, MP4, AVI, MOV formats
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional, Union
import numpy as np
from PIL import Image, ImageSequence
import cv2
import imageio
from dataclasses import dataclass

# Add project root to path
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from core.pattern import Pattern, PatternMetadata, Frame


@dataclass
class MediaInfo:
    """Information about loaded media"""
    width: int
    height: int
    frame_count: int
    duration_ms: int
    fps: float
    format: str
    file_size: int


class MediaConverter:
    """Convert various media formats to LED patterns"""
    
    def __init__(self):
        self.supported_image_formats = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}
        self.supported_video_formats = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
        self.max_dimensions = (1000, 1000)  # Max LED matrix size
        self.default_fps = 30.0
    
    def detect_media_type(self, file_path: str) -> str:
        """Detect media type from file extension"""
        ext = Path(file_path).suffix.lower()
        
        if ext in self.supported_image_formats:
            return 'image'
        elif ext in self.supported_video_formats:
            return 'video'
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    def get_media_info(self, file_path: str) -> MediaInfo:
        """Get information about media file"""
        media_type = self.detect_media_type(file_path)
        file_size = Path(file_path).stat().st_size
        
        if media_type == 'image':
            return self._get_image_info(file_path, file_size)
        elif media_type == 'video':
            return self._get_video_info(file_path, file_size)
    
    def _get_image_info(self, file_path: str, file_size: int) -> MediaInfo:
        """Get information about image file"""
        with Image.open(file_path) as img:
            width, height = img.size
            
            # Check if it's an animated GIF
            if hasattr(img, 'n_frames') and img.n_frames > 1:
                frame_count = img.n_frames
                duration_ms = img.info.get('duration', 100) * frame_count
                fps = 1000.0 / img.info.get('duration', 100)
            else:
                frame_count = 1
                duration_ms = 1000  # 1 second for static images
                fps = 1.0
            
            return MediaInfo(
                width=width,
                height=height,
                frame_count=frame_count,
                duration_ms=duration_ms,
                fps=fps,
                format='image',
                file_size=file_size
            )
    
    def _get_video_info(self, file_path: str, file_size: int) -> MediaInfo:
        """Get information about video file"""
        cap = cv2.VideoCapture(file_path)
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {file_path}")
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration_ms = int((frame_count / fps) * 1000) if fps > 0 else 0
        
        cap.release()
        
        return MediaInfo(
            width=width,
            height=height,
            frame_count=frame_count,
            duration_ms=duration_ms,
            fps=fps,
            format='video',
            file_size=file_size
        )
    
    def convert_to_pattern(self, file_path: str, 
                          target_width: Optional[int] = None,
                          target_height: Optional[int] = None,
                          fps: Optional[float] = None,
                          brightness: float = 1.0,
                          color_order: str = 'RGB') -> Pattern:
        """Convert media file to LED pattern"""
        
        media_info = self.get_media_info(file_path)
        media_type = self.detect_media_type(file_path)
        
        # Determine target dimensions
        if target_width is None or target_height is None:
            target_width, target_height = self._calculate_target_dimensions(
                media_info.width, media_info.height
            )
        
        # Use provided FPS or media FPS
        target_fps = fps if fps is not None else media_info.fps
        
        if media_type == 'image':
            return self._convert_image_to_pattern(
                file_path, target_width, target_height, target_fps, brightness, color_order
            )
        elif media_type == 'video':
            return self._convert_video_to_pattern(
                file_path, target_width, target_height, target_fps, brightness, color_order
            )
    
    def _calculate_target_dimensions(self, width: int, height: int) -> Tuple[int, int]:
        """Calculate target LED matrix dimensions"""
        # Keep aspect ratio but limit to max dimensions
        aspect_ratio = width / height
        
        if aspect_ratio > 1:  # Landscape
            target_width = min(width, self.max_dimensions[0])
            target_height = int(target_width / aspect_ratio)
        else:  # Portrait or square
            target_height = min(height, self.max_dimensions[1])
            target_width = int(target_height * aspect_ratio)
        
        # Ensure minimum size
        target_width = max(target_width, 1)
        target_height = max(target_height, 1)
        
        return target_width, target_height
    
    def _convert_image_to_pattern(self, file_path: str, 
                                 target_width: int, target_height: int,
                                 fps: float, brightness: float, 
                                 color_order: str) -> Pattern:
        """Convert image to LED pattern"""
        
        with Image.open(file_path) as img:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            frames = []
            
            # Handle animated GIFs
            if hasattr(img, 'n_frames') and img.n_frames > 1:
                frame_duration = img.info.get('duration', 100)
                
                for frame in ImageSequence.Iterator(img):
                    frame = frame.convert('RGB')
                    frame = frame.resize((target_width, target_height), Image.Resampling.LANCZOS)
                    
                    # Convert to LED pattern
                    pixels = self._image_to_pixels(frame, brightness, color_order)
                    frames.append(Frame(pixels=pixels, duration_ms=frame_duration))
            else:
                # Static image - resize and convert
                img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                pixels = self._image_to_pixels(img, brightness, color_order)
                
                # Create single frame
                frame_duration = int(1000 / fps) if fps > 0 else 1000
                frames.append(Frame(pixels=pixels, duration_ms=frame_duration))
            
            # Create pattern metadata
            metadata = PatternMetadata(
                width=target_width,
                height=target_height,
                color_order=color_order,
                brightness=brightness,
                fps=fps
            )
            
            # Create pattern
            pattern_name = Path(file_path).stem
            pattern = Pattern(
                name=f"Converted from {pattern_name}",
                metadata=metadata,
                frames=frames
            )
            
            return pattern
    
    def _convert_video_to_pattern(self, file_path: str,
                                 target_width: int, target_height: int,
                                 fps: float, brightness: float,
                                 color_order: str) -> Pattern:
        """Convert video to LED pattern"""
        
        cap = cv2.VideoCapture(file_path)
        frames = []
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {file_path}")
        
        # Calculate frame duration
        frame_duration = int(1000 / fps) if fps > 0 else 33  # Default 30 FPS
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Resize frame
            frame_resized = cv2.resize(frame_rgb, (target_width, target_height))
            
            # Convert to LED pattern
            pixels = self._cv2_to_pixels(frame_resized, brightness, color_order)
            frames.append(Frame(pixels=pixels, duration_ms=frame_duration))
            
            frame_count += 1
            
            # Limit frames for performance
            if frame_count > 1000:  # Max 1000 frames
                break
        
        cap.release()
        
        # Create pattern metadata
        metadata = PatternMetadata(
            width=target_width,
            height=target_height,
            color_order=color_order,
            brightness=brightness,
            fps=fps
        )
        
        # Create pattern
        pattern_name = Path(file_path).stem
        pattern = Pattern(
            name=f"Converted from {pattern_name}",
            metadata=metadata,
            frames=frames
        )
        
        return pattern
    
    def _image_to_pixels(self, img: Image.Image, brightness: float, color_order: str) -> List[Tuple[int, int, int]]:
        """Convert PIL Image to LED pixels"""
        pixels = []
        
        # Get image data
        img_array = np.array(img)
        
        # Apply brightness
        if brightness != 1.0:
            img_array = (img_array * brightness).astype(np.uint8)
        
        # Convert to LED pixels
        for y in range(img.height):
            for x in range(img.width):
                r, g, b = img_array[y, x]
                
                # Apply color order
                if color_order == 'RGB':
                    pixels.append((r, g, b))
                elif color_order == 'GRB':
                    pixels.append((g, r, b))
                elif color_order == 'BRG':
                    pixels.append((b, r, g))
                elif color_order == 'BGR':
                    pixels.append((b, g, r))
                elif color_order == 'RBG':
                    pixels.append((r, b, g))
                elif color_order == 'GBR':
                    pixels.append((g, b, r))
                else:
                    pixels.append((r, g, b))  # Default RGB
        
        return pixels
    
    def _cv2_to_pixels(self, frame: np.ndarray, brightness: float, color_order: str) -> List[Tuple[int, int, int]]:
        """Convert OpenCV frame to LED pixels"""
        pixels = []
        
        # Apply brightness
        if brightness != 1.0:
            frame = (frame * brightness).astype(np.uint8)
        
        # Convert to LED pixels
        for y in range(frame.shape[0]):
            for x in range(frame.shape[1]):
                r, g, b = frame[y, x]
                
                # Apply color order
                if color_order == 'RGB':
                    pixels.append((r, g, b))
                elif color_order == 'GRB':
                    pixels.append((g, r, b))
                elif color_order == 'BRG':
                    pixels.append((b, r, g))
                elif color_order == 'BGR':
                    pixels.append((b, g, r))
                elif color_order == 'RBG':
                    pixels.append((r, b, g))
                elif color_order == 'GBR':
                    pixels.append((g, b, r))
                else:
                    pixels.append((r, g, b))  # Default RGB
        
        return pixels
    
    def get_supported_formats(self) -> dict:
        """Get list of supported formats"""
        return {
            'images': list(self.supported_image_formats),
            'videos': list(self.supported_video_formats)
        }
    
    def validate_file(self, file_path: str) -> bool:
        """Validate if file can be converted"""
        try:
            self.detect_media_type(file_path)
            self.get_media_info(file_path)
            return True
        except Exception:
            return False

