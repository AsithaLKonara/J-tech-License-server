"""
Pattern Converter - Convert between hardware order and design order

Some pattern files are stored in hardware wiring order (e.g., serpentine).
The layered architecture expects patterns in design order (sequential, row-major).
This module handles conversion.
"""

from typing import List, Tuple, Optional
from .pattern import Pattern, Frame, PatternMetadata


def detect_serpentine_pattern(pattern: Pattern) -> bool:
    """
    Detect if a pattern appears to be stored in serpentine hardware order.
    
    DISABLED: Returns False to prevent automatic unwrapping.
    User must specify wiring mode explicitly in the UI.
    
    The previous implementation always returned True, which caused issues
    when files were not actually in serpentine format.
    """
    # DISABLED: Do not auto-detect serpentine
    # Files should be treated as design order by default
    # User can select target wiring in the UI if needed
    return False


def unwrap_serpentine_pattern(pattern: Pattern, data_in_corner: str = "LB") -> Pattern:
    """
    Convert a serpentine-ordered pattern to design order (row-major, sequential).
    
    This unwraps patterns that are stored in hardware serpentine order so they
    display correctly in the preview (visual design order).
    
    Args:
        pattern: Pattern with pixels in serpentine hardware order
        data_in_corner: Where data enters ("LB" = bottom-left, "LT" = top-left, etc.)
    
    Returns:
        Pattern with pixels in design order (sequential row-major)
    """
    width = pattern.metadata.width
    height = pattern.metadata.height
    
    if height <= 1:
        return pattern
    
    # Convert all frames
    converted_frames = []
    for frame in pattern.frames:
        design_pixels = []
        
        # For serpentine from bottom-left (most common):
        # Hardware order: bottom row L→R, next row R→L, next L→R, etc.
        # We need to reorder to: top row L→R, next row L→R, etc. (all same direction)
        
        if data_in_corner == "LB":
            # Bottom-left start: hardware goes bottom-to-top with alternating direction
            for visual_row in range(height):
                # Map visual row to hardware row (bottom-to-top)
                hw_row = height - 1 - visual_row
                hw_row_reversed = (hw_row % 2 == 1)  # Odd hardware rows are reversed
                
                # Extract row from hardware order
                hw_start = hw_row * width
                hw_pixels = frame.pixels[hw_start:hw_start + width]
                
                # Reverse if needed
                if hw_row_reversed:
                    hw_pixels = list(reversed(hw_pixels))
                
                design_pixels.extend(hw_pixels)
        elif data_in_corner == "LT":
            # Top-left start: hardware goes top-to-bottom with alternating direction
            for visual_row in range(height):
                # Hardware row is same as visual row (top-to-bottom)
                hw_row = visual_row
                hw_row_reversed = (hw_row % 2 == 1)  # Odd hardware rows are reversed
                
                # Extract row from hardware order
                hw_start = hw_row * width
                hw_pixels = frame.pixels[hw_start:hw_start + width]
                
                # Reverse if needed
                if hw_row_reversed:
                    hw_pixels = list(reversed(hw_pixels))
                
                design_pixels.extend(hw_pixels)
        else:
            # For other corners, implement as needed
            # For now, default behavior
            design_pixels = list(frame.pixels)
        
        converted_frames.append(Frame(
            pixels=design_pixels,
            duration_ms=frame.duration_ms
        ))
    
    # Return new pattern with converted frames
    import copy
    return Pattern(
        name=pattern.name,
        metadata=copy.deepcopy(pattern.metadata),  # Deep copy to avoid mutation
        frames=converted_frames
    )


def hardware_to_design_order(pattern: Pattern, wiring_mode: str = "Serpentine", 
                             data_in_corner: str = "LB") -> Pattern:
    """
    Convert a pattern from hardware wiring order to design order.
    
    This is the REVERSE of what WiringMapper does - it takes hardware-ordered
    pixels and converts them back to sequential design order.
    
    Args:
        pattern: Pattern with pixels in hardware order
        wiring_mode: How the hardware is wired
        data_in_corner: Where data enters the matrix
        
    Returns:
        Pattern with pixels in design order (sequential, row-major)
    """
    width = pattern.metadata.width
    height = pattern.metadata.height
    
    if height <= 1:
        # Strip - no conversion needed
        return pattern
    
    # Build reverse mapping: design_index -> hardware_index
    hardware_to_design_map = _build_hardware_to_design_map(
        width, height, wiring_mode, data_in_corner
    )
    
    # Convert all frames
    converted_frames = []
    for frame in pattern.frames:
        # Create design-order pixel array
        design_pixels = [None] * len(frame.pixels)
        
        # Map hardware pixels to design positions
        for hardware_idx, design_idx in enumerate(hardware_to_design_map):
            if hardware_idx < len(frame.pixels):
                design_pixels[design_idx] = frame.pixels[hardware_idx]
        
        converted_frames.append(Frame(
            pixels=design_pixels,
            duration_ms=frame.duration_ms
        ))
    
    # Create new pattern with converted frames
    import copy
    return Pattern(
        name=pattern.name,
        metadata=copy.deepcopy(pattern.metadata),  # Deep copy to avoid mutation
        frames=converted_frames
    )


def _build_hardware_to_design_map(width: int, height: int, wiring_mode: str,
                                  data_in_corner: str) -> List[int]:
    """
    Build mapping from hardware index to design index.
    
    Returns list where: design_index = mapping[hardware_index]
    """
    # Determine starting position based on data_in_corner
    if data_in_corner == "LB":
        start_x, start_y = 0, height - 1
    elif data_in_corner == "RT":
        start_x, start_y = width - 1, 0
    elif data_in_corner == "RB":
        start_x, start_y = width - 1, height - 1
    else:  # LT (default)
        start_x, start_y = 0, 0
    
    # Build hardware traversal path (x, y coordinates)
    hardware_path = []
    
    if wiring_mode == 'Serpentine':
        # Serpentine rows (zigzag left-right)
        if data_in_corner in ("LT", "RT"):
            # Start from top, go down
            for y in range(height):
                if (y % 2 == 0 and start_x == 0) or (y % 2 == 1 and start_x == width - 1):
                    # Left to right
                    for x in range(width):
                        hardware_path.append((x, y))
                else:
                    # Right to left
                    for x in range(width-1, -1, -1):
                        hardware_path.append((x, y))
        else:  # LB or RB
            # Start from bottom, go up
            for y in range(height-1, -1, -1):
                if ((height - 1 - y) % 2 == 0 and start_x == 0) or ((height - 1 - y) % 2 == 1 and start_x == width - 1):
                    # Left to right
                    for x in range(width):
                        hardware_path.append((x, y))
                else:
                    # Right to left
                    for x in range(width-1, -1, -1):
                        hardware_path.append((x, y))
    elif wiring_mode == 'Column-serpentine':
        # Serpentine columns (zigzag up-down)
        if data_in_corner in ("LT", "LB"):
            # Start from left, go right
            for x in range(width):
                if (x % 2 == 0 and start_y == 0) or (x % 2 == 1 and start_y == height - 1):
                    # Top to bottom
                    for y in range(height):
                        hardware_path.append((x, y))
                else:
                    # Bottom to top
                    for y in range(height-1, -1, -1):
                        hardware_path.append((x, y))
        else:  # RT or RB
            # Start from right, go left
            for x in range(width-1, -1, -1):
                if ((width - 1 - x) % 2 == 0 and start_y == 0) or ((width - 1 - x) % 2 == 1 and start_y == height - 1):
                    # Top to bottom
                    for y in range(height):
                        hardware_path.append((x, y))
                else:
                    # Bottom to top
                    for y in range(height-1, -1, -1):
                        hardware_path.append((x, y))
    elif wiring_mode == 'Row-major':
        # Simple row-major (always left-right or right-left)
        if data_in_corner in ("LT", "LB"):
            # Start from left
            if start_y == 0:  # Top
                for y in range(height):
                    for x in range(width):
                        hardware_path.append((x, y))
            else:  # Bottom
                for y in range(height-1, -1, -1):
                    for x in range(width):
                        hardware_path.append((x, y))
        else:  # RT or RB
            # Start from right
            if start_y == 0:  # Top
                for y in range(height):
                    for x in range(width-1, -1, -1):
                        hardware_path.append((x, y))
            else:  # Bottom
                for y in range(height-1, -1, -1):
                    for x in range(width-1, -1, -1):
                        hardware_path.append((x, y))
                        
    elif wiring_mode == 'Column-major':
        # Simple column-major (always top-bottom or bottom-top)
        if data_in_corner in ("LT", "RT"):
            # Start from top
            if start_x == 0:  # Left
                for x in range(width):
                    for y in range(height):
                        hardware_path.append((x, y))
            else:  # Right
                for x in range(width-1, -1, -1):
                    for y in range(height):
                        hardware_path.append((x, y))
        else:  # LB or RB
            # Start from bottom
            if start_x == 0:  # Left
                for x in range(width):
                    for y in range(height-1, -1, -1):
                        hardware_path.append((x, y))
            else:  # Right
                for x in range(width-1, -1, -1):
                    for y in range(height-1, -1, -1):
                        hardware_path.append((x, y))
    else:
        # Fallback: simple row-major from top-left
        for y in range(height):
            for x in range(width):
                hardware_path.append((x, y))
    
    # Convert (x, y) to design index (row-major, top-left origin)
    mapping = []
    for (x, y) in hardware_path:
        design_idx = y * width + x
        mapping.append(design_idx)
    
    return mapping

