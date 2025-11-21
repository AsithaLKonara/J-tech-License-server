"""
Drawing Tools - Implementation of all drawing tools

Provides implementations for: Pixel, Rectangle, Circle, Line, Fill, Gradient, Random Spray, Text.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from enum import Enum
import random
import math

from core.pattern import Frame
from domain.drawing.brush import Brush, BrushSettings

RGB = Tuple[int, int, int]


class DrawingTool(ABC):
    """Base class for drawing tools"""
    
    def __init__(self, brush: Brush = None):
        """
        Initialize drawing tool.
        
        Args:
            brush: Brush settings (creates default if None)
        """
        self.brush = brush or Brush()
    
    @abstractmethod
    def apply(
        self,
        frame: Frame,
        start_pos: Tuple[int, int],
        end_pos: Tuple[int, int],
        color: RGB,
        width: int,
        height: int
    ) -> Frame:
        """
        Apply drawing operation to frame.
        
        Args:
            frame: Frame to modify
            start_pos: Start position (x, y)
            end_pos: End position (x, y)
            color: Drawing color
            width: Matrix width
            height: Matrix height
            
        Returns:
            Modified frame (new instance)
        """
        pass


class PixelTool(DrawingTool):
    """Pixel tool - single pixel painting"""
    
    def apply(
        self,
        frame: Frame,
        start_pos: Tuple[int, int],
        end_pos: Tuple[int, int],
        color: RGB,
        width: int,
        height: int
    ) -> Frame:
        """Paint single pixel"""
        from copy import deepcopy
        new_frame = deepcopy(frame)
        
        x, y = end_pos
        if 0 <= x < width and 0 <= y < height:
            idx = y * width + x
            if idx < len(new_frame.pixels):
                new_frame.pixels[idx] = color
        
        return new_frame


class RectangleTool(DrawingTool):
    """Rectangle tool - draw filled or outline rectangles"""
    
    def apply(
        self,
        frame: Frame,
        start_pos: Tuple[int, int],
        end_pos: Tuple[int, int],
        color: RGB,
        width: int,
        height: int,
        filled: bool = True
    ) -> Frame:
        """Draw rectangle"""
        from copy import deepcopy
        new_frame = deepcopy(frame)
        
        x1, y1 = start_pos
        x2, y2 = end_pos
        
        # Ensure x1 <= x2 and y1 <= y2
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)
        
        # Clamp to matrix bounds
        x1 = max(0, min(width - 1, x1))
        x2 = max(0, min(width - 1, x2))
        y1 = max(0, min(height - 1, y1))
        y2 = max(0, min(height - 1, y2))
        
        if filled:
            # Fill rectangle
            for y in range(y1, y2 + 1):
                for x in range(x1, x2 + 1):
                    idx = y * width + x
                    if idx < len(new_frame.pixels):
                        new_frame.pixels[idx] = color
        else:
            # Outline only
            for y in range(y1, y2 + 1):
                for x in range(x1, x2 + 1):
                    if x == x1 or x == x2 or y == y1 or y == y2:
                        idx = y * width + x
                        if idx < len(new_frame.pixels):
                            new_frame.pixels[idx] = color
        
        return new_frame


class CircleTool(DrawingTool):
    """Circle tool - draw filled or outline circles"""
    
    def apply(
        self,
        frame: Frame,
        start_pos: Tuple[int, int],
        end_pos: Tuple[int, int],
        color: RGB,
        width: int,
        height: int,
        filled: bool = True
    ) -> Frame:
        """Draw circle"""
        from copy import deepcopy
        new_frame = deepcopy(frame)
        
        x1, y1 = start_pos
        x2, y2 = end_pos
        
        # Calculate center and radius
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        radius = int(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 / 2)
        
        # Draw circle
        for y in range(max(0, cy - radius), min(height, cy + radius + 1)):
            for x in range(max(0, cx - radius), min(width, cx + radius + 1)):
                dx = x - cx
                dy = y - cy
                dist = math.sqrt(dx * dx + dy * dy)
                
                if filled:
                    if dist <= radius:
                        idx = y * width + x
                        if idx < len(new_frame.pixels):
                            new_frame.pixels[idx] = color
                else:
                    # Outline only (within tolerance)
                    if abs(dist - radius) < 0.5:
                        idx = y * width + x
                        if idx < len(new_frame.pixels):
                            new_frame.pixels[idx] = color
        
        return new_frame


class LineTool(DrawingTool):
    """Line tool - draw straight lines"""
    
    def apply(
        self,
        frame: Frame,
        start_pos: Tuple[int, int],
        end_pos: Tuple[int, int],
        color: RGB,
        width: int,
        height: int
    ) -> Frame:
        """Draw line using Bresenham's algorithm"""
        from copy import deepcopy
        new_frame = deepcopy(frame)
        
        x1, y1 = start_pos
        x2, y2 = end_pos
        
        # Bresenham's line algorithm
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        x, y = x1, y1
        
        while True:
            if 0 <= x < width and 0 <= y < height:
                idx = y * width + x
                if idx < len(new_frame.pixels):
                    new_frame.pixels[idx] = color
            
            if x == x2 and y == y2:
                break
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
        
        return new_frame


class FillTool(DrawingTool):
    """Fill tool - flood fill connected pixels"""
    
    def apply(
        self,
        frame: Frame,
        start_pos: Tuple[int, int],
        end_pos: Tuple[int, int],
        color: RGB,
        width: int,
        height: int
    ) -> Frame:
        """Flood fill from start position"""
        from copy import deepcopy
        new_frame = deepcopy(frame)
        
        x, y = start_pos
        if not (0 <= x < width and 0 <= y < height):
            return new_frame
        
        # Get target color
        idx = y * width + x
        if idx >= len(new_frame.pixels):
            return new_frame
        
        target_color = new_frame.pixels[idx]
        
        # If already the same color, nothing to do
        if target_color == color:
            return new_frame
        
        # Flood fill using stack
        stack = [(x, y)]
        visited = set()
        
        while stack:
            px, py = stack.pop()
            
            if (px, py) in visited:
                continue
            
            if not (0 <= px < width and 0 <= py < height):
                continue
            
            pixel_idx = py * width + px
            if pixel_idx >= len(new_frame.pixels):
                continue
            
            if new_frame.pixels[pixel_idx] != target_color:
                continue
            
            visited.add((px, py))
            new_frame.pixels[pixel_idx] = color
            
            # Add neighbors
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                stack.append((px + dx, py + dy))
        
        return new_frame


class GradientTool(DrawingTool):
    """Gradient tool - draw gradient between two colors"""
    
    def __init__(self, brush: Brush = None, start_color: RGB = None, end_color: RGB = None):
        super().__init__(brush)
        self.start_color = start_color or (255, 0, 0)
        self.end_color = end_color or (0, 0, 255)
    
    def apply(
        self,
        frame: Frame,
        start_pos: Tuple[int, int],
        end_pos: Tuple[int, int],
        color: RGB,
        width: int,
        height: int
    ) -> Frame:
        """Draw gradient from start to end position"""
        from copy import deepcopy
        new_frame = deepcopy(frame)
        
        x1, y1 = start_pos
        x2, y2 = end_pos
        
        # Calculate distance
        dx = x2 - x1
        dy = y2 - y1
        max_dist = math.sqrt(dx * dx + dy * dy)
        
        if max_dist == 0:
            return new_frame
        
        # Draw gradient along line
        steps = int(max_dist)
        for i in range(steps + 1):
            t = i / steps if steps > 0 else 0
            x = int(x1 + dx * t)
            y = int(y1 + dy * t)
            
            if 0 <= x < width and 0 <= y < height:
                # Interpolate color
                r = int(self.start_color[0] * (1 - t) + self.end_color[0] * t)
                g = int(self.start_color[1] * (1 - t) + self.end_color[1] * t)
                b = int(self.start_color[2] * (1 - t) + self.end_color[2] * t)
                gradient_color = (r, g, b)
                
                idx = y * width + x
                if idx < len(new_frame.pixels):
                    new_frame.pixels[idx] = gradient_color
        
        return new_frame


class RandomSprayTool(DrawingTool):
    """Random spray tool - spray random pixels"""
    
    def apply(
        self,
        frame: Frame,
        start_pos: Tuple[int, int],
        end_pos: Tuple[int, int],
        color: RGB,
        width: int,
        height: int,
        density: float = 0.3
    ) -> Frame:
        """Spray random pixels in brush area"""
        from copy import deepcopy
        new_frame = deepcopy(frame)
        
        x, y = end_pos
        brush_size = self.brush.settings.size
        half_size = brush_size // 2
        
        # Random pixels in brush area
        num_pixels = int(brush_size * brush_size * density)
        for _ in range(num_pixels):
            rx = x + random.randint(-half_size, half_size)
            ry = y + random.randint(-half_size, half_size)
            
            if 0 <= rx < width and 0 <= ry < height:
                idx = ry * width + rx
                if idx < len(new_frame.pixels):
                    new_frame.pixels[idx] = color
        
        return new_frame


class TextTool(DrawingTool):
    """Text tool - render text using bitmap fonts"""
    
    def apply(
        self,
        frame: Frame,
        start_pos: Tuple[int, int],
        end_pos: Tuple[int, int],
        color: RGB,
        width: int,
        height: int,
        text: str = "A",
        font: Optional[object] = None
    ) -> Frame:
        """
        Render text using bitmap font.
        
        Args:
            frame: Frame to modify
            start_pos: Text start position
            end_pos: Unused (for consistency)
            color: Text color
            width: Matrix width
            height: Matrix height
            text: Text to render
            font: BitmapFont object (if None, uses default)
            
        Returns:
            Modified frame
        """
        from copy import deepcopy
        new_frame = deepcopy(frame)
        
        x, y = start_pos
        
        # Basic text rendering (simplified - full implementation would use BitmapFont)
        # For now, just render a simple pattern
        # TODO: Integrate with BitmapFontRepository
        
        if font is None:
            # Default: render "A" pattern
            pattern = [
                [0, 1, 1, 0],
                [1, 0, 0, 1],
                [1, 1, 1, 1],
                [1, 0, 0, 1],
                [1, 0, 0, 1],
            ]
            
            for py, row in enumerate(pattern):
                for px, pixel in enumerate(row):
                    if pixel:
                        px_abs = x + px
                        py_abs = y + py
                        if 0 <= px_abs < width and 0 <= py_abs < height:
                            idx = py_abs * width + px_abs
                            if idx < len(new_frame.pixels):
                                new_frame.pixels[idx] = color
        
        return new_frame


# Tool factory
def create_tool(tool_type: str, brush: Brush = None) -> DrawingTool:
    """
    Create drawing tool by type.
    
    Args:
        tool_type: Tool type ("pixel", "rectangle", "circle", "line", "fill", "gradient", "random", "text")
        brush: Brush settings
        
    Returns:
        DrawingTool instance
    """
    tool_map = {
        "pixel": PixelTool,
        "rectangle": RectangleTool,
        "circle": CircleTool,
        "line": LineTool,
        "fill": FillTool,
        "gradient": GradientTool,
        "random": RandomSprayTool,
        "text": TextTool,
    }
    
    tool_class = tool_map.get(tool_type.lower(), PixelTool)
    return tool_class(brush=brush)

