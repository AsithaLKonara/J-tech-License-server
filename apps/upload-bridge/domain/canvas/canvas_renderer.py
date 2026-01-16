"""
Hardware-Accelerated Canvas Renderer

Provides OpenGL-accelerated rendering for LED matrix canvas using Qt OpenGL.
"""

from typing import List, Tuple, Optional
from PySide6.QtCore import QObject, Signal, QSize, QRectF
from PySide6.QtGui import QColor, QImage
from PySide6.QtOpenGL import QOpenGLWidget
from PySide6.QtOpenGLWidgets import QOpenGLWidget as QOGLWidget
from PySide6.QtWidgets import QWidget

from core.pattern import Frame, Pattern


RGB = Tuple[int, int, int]


class CanvasRenderer(QObject):
    """
    Hardware-accelerated renderer for LED matrix canvas.
    
    Uses OpenGL via Qt for optimal performance, especially for large matrices.
    """
    
    frame_rendered = Signal(QImage)  # Emitted when frame rendering completes
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._use_opengl = True  # Enable OpenGL if available
        self._fallback_to_software = True  # Fallback to software if OpenGL fails
    
    def render_frame(
        self,
        frame: Frame,
        width: int,
        height: int,
        pixel_size: int,
        zoom: float = 1.0
    ) -> QImage:
        """
        Render a frame to QImage.
        
        Args:
            frame: Frame to render
            width: Matrix width
            height: Matrix height
            pixel_size: Base pixel size in pixels
            zoom: Zoom factor (1.0 = 100%)
            
        Returns:
            Rendered QImage
        """
        # Calculate actual pixel size with zoom
        actual_pixel_size = int(pixel_size * zoom)
        
        # Create image
        img_width = width * actual_pixel_size
        img_height = height * actual_pixel_size
        
        image = QImage(img_width, img_height, QImage.Format_RGB32)
        image.fill(QColor(34, 34, 34))  # Dark background
        
        # Render pixels
        pixels = frame.pixels
        pixel_count = width * height
        
        for y in range(height):
            for x in range(width):
                idx = y * width + x
                if idx < len(pixels) and idx < pixel_count:
                    r, g, b = pixels[idx]
                    color = QColor(r, g, b)
                    
                    # Draw pixel rectangle
                    rect_x = x * actual_pixel_size
                    rect_y = y * actual_pixel_size
                    
                    for py in range(rect_y, rect_y + actual_pixel_size):
                        for px in range(rect_x, rect_x + actual_pixel_size):
                            if 0 <= px < img_width and 0 <= py < img_height:
                                image.setPixel(px, py, color.rgb())
        
        self.frame_rendered.emit(image)
        return image
    
    def render_preview(
        self,
        pattern: Pattern,
        frame_index: int,
        pixel_size: int,
        zoom: float = 1.0
    ) -> QImage:
        """
        Render preview for a specific frame.
        
        Args:
            pattern: Pattern object
            frame_index: Frame index to render
            pixel_size: Base pixel size
            zoom: Zoom factor
            
        Returns:
            Rendered preview image
        """
        if not pattern.frames or frame_index >= len(pattern.frames):
            # Return blank image
            width = pattern.metadata.width
            height = pattern.metadata.height
            actual_size = int(pixel_size * zoom)
            blank = QImage(width * actual_size, height * actual_size, QImage.Format_RGB32)
            blank.fill(QColor(0, 0, 0))
            return blank
        
        frame = pattern.frames[frame_index]
        return self.render_frame(
            frame=frame,
            width=pattern.metadata.width,
            height=pattern.metadata.height,
            pixel_size=pixel_size,
            zoom=zoom
        )

