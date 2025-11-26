"""
Shape Tools - Drawing tools for rectangles, circles, lines, and polygons

Provides shape drawing capabilities with filled/outline modes.
"""

from __future__ import annotations

from typing import Tuple, List, Optional
from abc import ABC, abstractmethod
from math import sqrt, pi, cos, sin

from core.pattern import Frame

RGB = Tuple[int, int, int]


class ShapeTool(ABC):
    """Base class for shape drawing tools."""
    
    @abstractmethod
    def draw_shape(
        self,
        frame: Frame,
        start_pos: Tuple[int, int],
        end_pos: Tuple[int, int],
        color: RGB,
        width: int,
        height: int,
        filled: bool = True
    ) -> Frame:
        """
        Draw shape on frame.
        
        Args:
            frame: Frame to modify
            start_pos: Start position (x, y)
            end_pos: End position (x, y)
            color: Shape color
            width: Matrix width
            height: Matrix height
            filled: Whether shape is filled (True) or outline only (False)
        
        Returns:
            Modified frame
        """
        pass


class RectangleTool(ShapeTool):
    """Rectangle drawing tool."""
    
    def draw_shape(
        self,
        frame: Frame,
        start_pos: Tuple[int, int],
        end_pos: Tuple[int, int],
        color: RGB,
        width: int,
        height: int,
        filled: bool = True
    ) -> Frame:
        """Draw rectangle on frame."""
        from copy import deepcopy
        new_frame = deepcopy(frame)
        
        x1, y1 = start_pos
        x2, y2 = end_pos
        
        # Ensure x1 <= x2 and y1 <= y2
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        
        # Clamp to matrix bounds
        x1 = max(0, min(x1, width - 1))
        x2 = max(0, min(x2, width - 1))
        y1 = max(0, min(y1, height - 1))
        y2 = max(0, min(y2, height - 1))
        
        if filled:
            # Fill rectangle
            for y in range(y1, y2 + 1):
                for x in range(x1, x2 + 1):
                    idx = y * width + x
                    if 0 <= idx < len(new_frame.pixels):
                        new_frame.pixels[idx] = color
        else:
            # Draw outline only
            for y in range(y1, y2 + 1):
                for x in range(x1, x2 + 1):
                    # Check if on border
                    if y == y1 or y == y2 or x == x1 or x == x2:
                        idx = y * width + x
                        if 0 <= idx < len(new_frame.pixels):
                            new_frame.pixels[idx] = color
        
        return new_frame


class CircleTool(ShapeTool):
    """Circle drawing tool."""
    
    def draw_shape(
        self,
        frame: Frame,
        start_pos: Tuple[int, int],
        end_pos: Tuple[int, int],
        color: RGB,
        width: int,
        height: int,
        filled: bool = True
    ) -> Frame:
        """Draw circle on frame."""
        from copy import deepcopy
        new_frame = deepcopy(frame)
        
        x1, y1 = start_pos
        x2, y2 = end_pos
        
        # Calculate center and radius
        center_x = (x1 + x2) / 2.0
        center_y = (y1 + y2) / 2.0
        radius = sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2) / 2.0
        
        # Draw circle
        for y in range(height):
            for x in range(width):
                # Calculate distance from center
                dx = x - center_x
                dy = y - center_y
                distance = sqrt(dx * dx + dy * dy)
                
                if filled:
                    # Fill circle
                    if distance <= radius:
                        idx = y * width + x
                        if 0 <= idx < len(new_frame.pixels):
                            new_frame.pixels[idx] = color
                else:
                    # Draw outline only (with 1-pixel tolerance)
                    if abs(distance - radius) < 1.0:
                        idx = y * width + x
                        if 0 <= idx < len(new_frame.pixels):
                            new_frame.pixels[idx] = color
        
        return new_frame


class LineTool(ShapeTool):
    """Line drawing tool."""
    
    def draw_shape(
        self,
        frame: Frame,
        start_pos: Tuple[int, int],
        end_pos: Tuple[int, int],
        color: RGB,
        width: int,
        height: int,
        filled: bool = True  # Ignored for lines
    ) -> Frame:
        """Draw line on frame using Bresenham's algorithm."""
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
            # Draw pixel
            if 0 <= x < width and 0 <= y < height:
                idx = y * width + x
                if 0 <= idx < len(new_frame.pixels):
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


class PolygonTool(ShapeTool):
    """Polygon drawing tool (simplified - draws triangle for now)."""
    
    def __init__(self):
        self._points: List[Tuple[int, int]] = []
    
    def add_point(self, point: Tuple[int, int]):
        """Add a point to the polygon."""
        self._points.append(point)
    
    def reset(self):
        """Reset polygon points."""
        self._points = []
    
    def draw_shape(
        self,
        frame: Frame,
        start_pos: Tuple[int, int],
        end_pos: Tuple[int, int],
        color: RGB,
        width: int,
        height: int,
        filled: bool = True
    ) -> Frame:
        """Draw polygon on frame (simplified - draws triangle from 3 points)."""
        from copy import deepcopy
        new_frame = deepcopy(frame)
        
        # For now, draw a simple triangle
        # Full polygon implementation would require point collection
        x1, y1 = start_pos
        x2, y2 = end_pos
        
        # Calculate third point to form triangle
        x3 = x1 + (x2 - x1) // 2
        y3 = y1 - abs(y2 - y1)
        
        # Draw triangle outline
        line_tool = LineTool()
        new_frame = line_tool.draw_shape(new_frame, (x1, y1), (x2, y2), color, width, height, False)
        new_frame = line_tool.draw_shape(new_frame, (x2, y2), (x3, y3), color, width, height, False)
        new_frame = line_tool.draw_shape(new_frame, (x3, y3), (x1, y1), color, width, height, False)
        
        if filled:
            # Fill triangle (simple scanline fill)
            # Find bounding box
            min_x = min(x1, x2, x3)
            max_x = max(x1, x2, x3)
            min_y = min(y1, y2, y3)
            max_y = max(y1, y2, y3)
            
            for y in range(max(0, min_y), min(height, max_y + 1)):
                for x in range(max(0, min_x), min(width, max_x + 1)):
                    if self._point_in_triangle(x, y, (x1, y1), (x2, y2), (x3, y3)):
                        idx = y * width + x
                        if 0 <= idx < len(new_frame.pixels):
                            new_frame.pixels[idx] = color
        
        return new_frame
    
    def _point_in_triangle(self, px: int, py: int, p1: Tuple[int, int], p2: Tuple[int, int], p3: Tuple[int, int]) -> bool:
        """Check if point is inside triangle using barycentric coordinates."""
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        
        # Barycentric coordinates
        denom = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
        if abs(denom) < 0.001:
            return False
        
        a = ((y2 - y3) * (px - x3) + (x3 - x2) * (py - y3)) / denom
        b = ((y3 - y1) * (px - x3) + (x1 - x3) * (py - y3)) / denom
        c = 1 - a - b
        
        return 0 <= a <= 1 and 0 <= b <= 1 and 0 <= c <= 1


# Tool factory
def create_shape_tool(tool_type: str) -> Optional[ShapeTool]:
    """Create a shape tool by type."""
    if tool_type == "rectangle":
        return RectangleTool()
    elif tool_type == "circle":
        return CircleTool()
    elif tool_type == "line":
        return LineTool()
    elif tool_type == "polygon":
        return PolygonTool()
    return None

