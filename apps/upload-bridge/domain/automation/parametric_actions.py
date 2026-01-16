"""
Parametric Actions - Deterministic, testable automation actions

Implements parametric actions: scroll, rotate, mirror, invert, wipe, reveal, bounce.
All actions are deterministic and testable.
"""

from typing import List, Tuple, Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass

from core.pattern import Pattern, Frame

Color = Tuple[int, int, int]


class ActionType(Enum):
    """Automation action types"""
    SCROLL = "scroll"
    ROTATE = "rotate"
    MIRROR = "mirror"
    FLIP = "flip"
    INVERT = "invert"
    WIPE = "wipe"
    REVEAL = "reveal"
    BOUNCE = "bounce"
    ROTATE_180 = "rotate_180"
    ROTATE_CCW = "rotate_ccw"


@dataclass
class ActionParameters:
    """Parameters for automation actions"""
    direction: str = "right"  # scroll/wipe direction
    speed: float = 1.0  # Action speed multiplier
    distance: int = 1  # Pixels/frames to move
    axis: str = "horizontal"  # Mirror/flip axis
    color: Optional[Color] = None  # Wipe/reveal color
    easing: str = "linear"  # Easing function


class ParametricAction:
    """
    Parametric automation action.
    
    All actions are deterministic and testable.
    """
    
    def __init__(
        self,
        action_type: ActionType,
        parameters: ActionParameters,
        frame_range: Optional[Tuple[int, int]] = None
    ):
        """
        Initialize parametric action.
        
        Args:
            action_type: Type of action
            parameters: Action parameters
            frame_range: Optional frame range (None = all frames)
        """
        self.action_type = action_type
        self.parameters = parameters
        self.frame_range = frame_range
    
    def apply(self, pattern: Pattern) -> Pattern:
        """
        Apply action to pattern.
        
        Args:
            pattern: Pattern to transform
            
        Returns:
            Transformed pattern (new instance)
        """
        from copy import deepcopy
        new_pattern = deepcopy(pattern)
        
        # Determine frame range
        if self.frame_range:
            start, end = self.frame_range
            frame_indices = list(range(start, min(end + 1, len(new_pattern.frames))))
        else:
            frame_indices = list(range(len(new_pattern.frames)))
        
        # Apply action to frames
        for frame_idx in frame_indices:
            frame = new_pattern.frames[frame_idx]
            transformed_pixels = self._transform_frame(
                frame.pixels,
                new_pattern.metadata.width,
                new_pattern.metadata.height,
                frame_idx
            )
            frame.pixels = transformed_pixels
        
        return new_pattern
    
    def _transform_frame(
        self,
        pixels: List[Color],
        width: int,
        height: int,
        frame_index: int
    ) -> List[Color]:
        """Transform frame pixels based on action type"""
        
        if self.action_type == ActionType.SCROLL:
            return self._scroll(pixels, width, height, frame_index)
        elif self.action_type == ActionType.ROTATE:
            return self._rotate(pixels, width, height)
        elif self.action_type == ActionType.ROTATE_180:
            return self._rotate_180(pixels, width, height)
        elif self.action_type == ActionType.ROTATE_CCW:
            return self._rotate_ccw(pixels, width, height)
        elif self.action_type == ActionType.MIRROR:
            return self._mirror(pixels, width, height)
        elif self.action_type == ActionType.FLIP:
            return self._flip(pixels, width, height)
        elif self.action_type == ActionType.INVERT:
            return self._invert(pixels)
        elif self.action_type == ActionType.WIPE:
            return self._wipe(pixels, width, height, frame_index)
        elif self.action_type == ActionType.REVEAL:
            return self._reveal(pixels, width, height, frame_index)
        elif self.action_type == ActionType.BOUNCE:
            return self._bounce(pixels, width, height, frame_index)
        else:
            return pixels
    
    def _scroll(
        self,
        pixels: List[Color],
        width: int,
        height: int,
        frame_index: int
    ) -> List[Color]:
        """Scroll pixels in specified direction"""
        direction = self.parameters.direction.lower()
        distance = int(self.parameters.distance * self.parameters.speed * (frame_index + 1))
        
        result = [pixels[i] for i in range(len(pixels))]
        
        if direction in ["right", "left"]:
            # Horizontal scroll
            for y in range(height):
                for x in range(width):
                    src_x = (x - distance) % width if direction == "right" else (x + distance) % width
                    src_idx = y * width + src_x
                    dst_idx = y * width + x
                    result[dst_idx] = pixels[src_idx]
        else:
            # Vertical scroll
            for y in range(height):
                for x in range(width):
                    src_y = (y - distance) % height if direction == "down" else (y + distance) % height
                    src_idx = src_y * width + x
                    dst_idx = y * width + x
                    result[dst_idx] = pixels[src_idx]
        
        return result
    
    def _rotate(self, pixels: List[Color], width: int, height: int) -> List[Color]:
        """Rotate pixels 90 degrees clockwise"""
        result = [(0, 0, 0)] * len(pixels)
        
        for y in range(height):
            for x in range(width):
                # 90° clockwise: (x, y) -> (height-1-y, x)
                src_idx = y * width + x
                dst_y = width - 1 - x
                dst_x = y
                dst_idx = dst_y * height + dst_x
                if 0 <= dst_idx < len(result):
                    result[dst_idx] = pixels[src_idx]
        
        return result

    def _rotate_180(self, pixels: List[Color], width: int, height: int) -> List[Color]:
        """Rotate pixels 180 degrees"""
        # 180 is same as reverse
        return list(reversed(pixels))

    def _rotate_ccw(self, pixels: List[Color], width: int, height: int) -> List[Color]:
        """Rotate pixels 90 degrees counter-clockwise"""
        result = [(0, 0, 0)] * len(pixels)
        
        for y in range(height):
            for x in range(width):
                # 90° CCW: (x, y) -> (y, width-1-x)
                src_idx = y * width + x
                dst_y = x
                dst_x = height - 1 - y
                dst_idx = dst_y * height + dst_x
                if 0 <= dst_idx < len(result):
                    result[dst_idx] = pixels[src_idx]
        
        return result
    
    def _mirror(self, pixels: List[Color], width: int, height: int) -> List[Color]:
        """Mirror pixels along axis"""
        axis = self.parameters.axis.lower()
        result = [pixels[i] for i in range(len(pixels))]
        
        if axis == "horizontal":
            # Mirror left-right
            for y in range(height):
                for x in range(width):
                    src_x = width - 1 - x
                    src_idx = y * width + src_x
                    dst_idx = y * width + x
                    result[dst_idx] = pixels[src_idx]
        else:
            # Mirror top-bottom
            for y in range(height):
                for x in range(width):
                    src_y = height - 1 - y
                    src_idx = src_y * width + x
                    dst_idx = y * width + x
                    result[dst_idx] = pixels[src_idx]
        
        return result
    
    def _flip(self, pixels: List[Color], width: int, height: int) -> List[Color]:
        """Flip pixels (same as mirror)"""
        return self._mirror(pixels, width, height)
    
    def _invert(self, pixels: List[Color]) -> List[Color]:
        """Invert pixel colors"""
        return [
            (255 - r, 255 - g, 255 - b)
            for r, g, b in pixels
        ]
    
    def _wipe(
        self,
        pixels: List[Color],
        width: int,
        height: int,
        frame_index: int
    ) -> List[Color]:
        """Wipe effect with color"""
        direction = self.parameters.direction.lower()
        progress = (frame_index + 1) / max(1, len(pixels) // (width * height))
        progress = min(1.0, progress * self.parameters.speed)
        
        color = self.parameters.color or (255, 255, 255)
        result = [pixels[i] for i in range(len(pixels))]
        
        if direction in ["right", "left"]:
            # Horizontal wipe
            wipe_x = int(width * progress) if direction == "right" else int(width * (1 - progress))
            for y in range(height):
                for x in range(width):
                    if (direction == "right" and x < wipe_x) or (direction == "left" and x >= wipe_x):
                        result[y * width + x] = color
        else:
            # Vertical wipe
            wipe_y = int(height * progress) if direction == "down" else int(height * (1 - progress))
            for y in range(height):
                for x in range(width):
                    if (direction == "down" and y < wipe_y) or (direction == "up" and y >= wipe_y):
                        result[y * width + x] = color
        
        return result
    
    def _reveal(
        self,
        pixels: List[Color],
        width: int,
        height: int,
        frame_index: int
    ) -> List[Color]:
        """Reveal effect (opposite of wipe)"""
        # Reveal is wipe with original pixels instead of color
        direction = self.parameters.direction.lower()
        progress = (frame_index + 1) / max(1, len(pixels) // (width * height))
        progress = min(1.0, progress * self.parameters.speed)
        
        result = [(0, 0, 0)] * len(pixels)  # Start with black
        
        if direction in ["right", "left"]:
            # Horizontal reveal
            reveal_x = int(width * progress) if direction == "right" else int(width * (1 - progress))
            for y in range(height):
                for x in range(width):
                    if (direction == "right" and x < reveal_x) or (direction == "left" and x >= reveal_x):
                        result[y * width + x] = pixels[y * width + x]
        else:
            # Vertical reveal
            reveal_y = int(height * progress) if direction == "down" else int(height * (1 - progress))
            for y in range(height):
                for x in range(width):
                    if (direction == "down" and y < reveal_y) or (direction == "up" and y >= reveal_y):
                        result[y * width + x] = pixels[y * width + x]
        
        return result
    
    def _bounce(
        self,
        pixels: List[Color],
        width: int,
        height: int,
        frame_index: int
    ) -> List[Color]:
        """Bounce effect (oscillating scroll)"""
        direction = self.parameters.direction.lower()
        period = max(1, int(10 / self.parameters.speed))
        phase = (frame_index % period) / period
        
        # Bounce: sin wave from 0 to 1
        import math
        bounce_progress = abs(math.sin(phase * math.pi))
        distance = int(self.parameters.distance * bounce_progress)
        
        result = [pixels[i] for i in range(len(pixels))]
        
        if direction in ["right", "left"]:
            # Horizontal bounce
            for y in range(height):
                for x in range(width):
                    src_x = (x - distance) % width if direction == "right" else (x + distance) % width
                    src_idx = y * width + src_x
                    dst_idx = y * width + x
                    result[dst_idx] = pixels[src_idx]
        else:
            # Vertical bounce
            for y in range(height):
                for x in range(width):
                    src_y = (y - distance) % height if direction == "down" else (y + distance) % height
                    src_idx = src_y * width + x
                    dst_idx = y * width + x
                    result[dst_idx] = pixels[src_idx]
        
        return result


def create_action(
    action_type: str,
    parameters: Optional[Dict[str, Any]] = None,
    frame_range: Optional[Tuple[int, int]] = None
) -> ParametricAction:
    """
    Create parametric action.
    
    Args:
        action_type: Action type string
        parameters: Optional parameters dict
        frame_range: Optional frame range
        
    Returns:
        ParametricAction instance
    """
    try:
        action_enum = ActionType(action_type.lower())
    except ValueError:
        action_enum = ActionType.SCROLL
    
    params = ActionParameters()
    if parameters:
        for key, value in parameters.items():
            if hasattr(params, key):
                setattr(params, key, value)
    
    return ParametricAction(
        action_type=action_enum,
        parameters=params,
        frame_range=frame_range
    )

