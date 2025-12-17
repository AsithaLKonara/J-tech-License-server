"""
Wiring Mapper - Layer 4: Firmware Generation Mapping

This module translates the design layer (sequential pixels) into hardware strip order
based on the wiring configuration (mode + data_in_corner).

LAYER ARCHITECTURE:
- Layer 1 (Base): Matrix grid with sequential numbering 0..N-1
- Layer 2 (Design): Pattern pixels displayed sequentially (pixel[i] → cell i)
- Layer 3 (Wiring): Visual overlay showing data flow (doesn't alter data)
- Layer 4 (Mapping): THIS MODULE - translates design to hardware order for firmware
"""

from typing import List, Tuple


class WiringMapper:
    """
    Maps design pixels (sequential 0..N-1) to hardware strip order based on wiring configuration.
    
    The design pixels are always in sequential order (left-to-right, top-to-bottom).
    The hardware strip order depends on how the physical LED strip is wired through the matrix.
    """
    
    def __init__(self, width: int, height: int, wiring_mode: str = "Row-major", data_in_corner: str = "LT", flip_x: bool = False, flip_y: bool = False, active_cell_coordinates: List[Tuple[int, int]] = None):
        """
        Initialize the wiring mapper.
        
        Args:
            width: Matrix width
            height: Matrix height
            wiring_mode: "Row-major", "Serpentine", "Column-major", or "Column-serpentine"
            data_in_corner: "LT" (Left Top), "LB" (Left Bottom), "RT" (Right Top), or "RB" (Right Bottom)
            flip_x: Flip horizontally (mirror left-right) after mapping
            flip_y: Flip vertically (mirror top-bottom) after mapping
            active_cell_coordinates: Optional list of (x, y) tuples for irregular shapes. If provided, only these cells will be included in the wiring path.
        """
        self.width = width
        self.height = height
        self.wiring_mode = wiring_mode
        self.data_in_corner = data_in_corner
        self.flip_x = flip_x
        self.flip_y = flip_y
        self.active_cell_coordinates = active_cell_coordinates
        
    def design_to_hardware(self, design_pixels: List[Tuple[int, int, int]]) -> List[Tuple[int, int, int]]:
        """
        Map design pixels (sequential order) to hardware strip order.
        PURE FUNCTION: Does not mutate input, returns fresh list.
        
        Args:
            design_pixels: List of (R, G, B) tuples in design order (sequential 0..N-1)
            
        Returns:
            New list of (R, G, B) tuples in hardware strip order
        """
        # Build mapping table: hardware_strip_index -> design_cell_index
        # For irregular shapes, this will only include active cells
        mapping = self._build_mapping_table()
        
        # Expected count is the number of LEDs in the hardware strip
        # For irregular shapes, this equals the number of active cells
        # For regular shapes, this equals width * height
        expected_count = len(mapping)
        
        if len(design_pixels) < max(mapping) + 1 if mapping else 0:
            # Dimension mismatch - return copy (not original reference)
            return list(design_pixels)
        
        # Preallocate destination buffer (prevents append aliasing bugs)
        # This ensures deterministic behavior and no mutation of input
        hardware_pixels = [None] * expected_count
        
        # Fill destination buffer by index (pure, deterministic)
        for hardware_idx in range(expected_count):
            design_idx = mapping[hardware_idx]
            if design_idx < len(design_pixels):
                hardware_pixels[hardware_idx] = design_pixels[design_idx]
            else:
                # Fallback for out-of-bounds indices
                hardware_pixels[hardware_idx] = (0, 0, 0)
        
        # Sanity check: ensure all pixels were filled
        assert all(p is not None for p in hardware_pixels), "Mapping incomplete - some pixels not set"
            
        return hardware_pixels
    
    def _build_mapping_table(self) -> List[int]:
        """
        Build lookup table: hardware_strip_index -> design_cell_index.
        
        The design cells are numbered sequentially 0..N-1, left-to-right, top-to-bottom.
        The hardware strip indices depend on the wiring mode and data-in corner.
        
        Returns:
            List where index is hardware position, value is design cell index
        """
        w, h = self.width, self.height
        
        # Step 1: Determine starting position based on data_in_corner
        if self.data_in_corner == "LB":
            start_x, start_y = 0, h - 1
        elif self.data_in_corner == "RT":
            start_x, start_y = w - 1, 0
        elif self.data_in_corner == "RB":
            start_x, start_y = w - 1, h - 1
        else:  # LT (default)
            start_x, start_y = 0, 0
        
        # Step 2: Build traversal path according to wiring mode
        path = []  # List of (x, y) in hardware order
        
        if self.wiring_mode == 'Serpentine':
            # Serpentine rows (zigzag left-right)
            if self.data_in_corner in ("LT", "RT"):
                # Start from top, go down
                for y in range(h):
                    if (y % 2 == 0 and start_x == 0) or (y % 2 == 1 and start_x == w - 1):
                        # Left to right
                        for x in range(w):
                            path.append((x, y))
                    else:
                        # Right to left
                        for x in range(w-1, -1, -1):
                            path.append((x, y))
            else:  # LB or RB
                # Start from bottom, go up
                for y in range(h-1, -1, -1):
                    if ((h - 1 - y) % 2 == 0 and start_x == 0) or ((h - 1 - y) % 2 == 1 and start_x == w - 1):
                        # Left to right
                        for x in range(w):
                            path.append((x, y))
                    else:
                        # Right to left
                        for x in range(w-1, -1, -1):
                            path.append((x, y))
                            
        elif self.wiring_mode == 'Row-major':
            # Simple row-major (always left-right or right-left)
            if self.data_in_corner in ("LT", "LB"):
                # Start from left
                if start_y == 0:  # Top
                    for y in range(h):
                        for x in range(w):
                            path.append((x, y))
                else:  # Bottom
                    for y in range(h-1, -1, -1):
                        for x in range(w):
                            path.append((x, y))
            else:  # RT or RB
                # Start from right
                if start_y == 0:  # Top
                    for y in range(h):
                        for x in range(w-1, -1, -1):
                            path.append((x, y))
                else:  # Bottom
                    for y in range(h-1, -1, -1):
                        for x in range(w-1, -1, -1):
                            path.append((x, y))
                            
        elif self.wiring_mode == 'Column-major':
            # Simple column-major (always top-bottom or bottom-top)
            if self.data_in_corner in ("LT", "RT"):
                # Start from top
                if start_x == 0:  # Left
                    for x in range(w):
                        for y in range(h):
                            path.append((x, y))
                else:  # Right
                    for x in range(w-1, -1, -1):
                        for y in range(h):
                            path.append((x, y))
            else:  # LB or RB
                # Start from bottom
                if start_x == 0:  # Left
                    for x in range(w):
                        for y in range(h-1, -1, -1):
                            path.append((x, y))
                else:  # Right
                    for x in range(w-1, -1, -1):
                        for y in range(h-1, -1, -1):
                            path.append((x, y))
                            
        elif self.wiring_mode == 'Column-serpentine':
            # Serpentine columns (zigzag up-down)
            if self.data_in_corner in ("LT", "LB"):
                # Start from left, go right
                for x in range(w):
                    if (x % 2 == 0 and start_y == 0) or (x % 2 == 1 and start_y == h - 1):
                        # Top to bottom
                        for y in range(h):
                            path.append((x, y))
                    else:
                        # Bottom to top
                        for y in range(h-1, -1, -1):
                            path.append((x, y))
            else:  # RT or RB
                # Start from right, go left
                for x in range(w-1, -1, -1):
                    if ((w - 1 - x) % 2 == 0 and start_y == 0) or ((w - 1 - x) % 2 == 1 and start_y == h - 1):
                        # Top to bottom
                        for y in range(h):
                            path.append((x, y))
                    else:
                        # Bottom to top
                        for y in range(h-1, -1, -1):
                            path.append((x, y))
        else:
            # Fallback: simple row-major from top-left
            for y in range(h):
                for x in range(w):
                    path.append((x, y))
        
        # Step 3: Apply flip transformations (if enabled)
        # This corrects for physical panel orientation mismatches
        if self.flip_x or self.flip_y:
            flipped_path = []
            for (x, y) in path:
                if self.flip_x:
                    x = (w - 1) - x
                if self.flip_y:
                    y = (h - 1) - y
                flipped_path.append((x, y))
            path = flipped_path
        
        # Step 3.5: Filter to active cells if irregular shape
        # For irregular matrices, only include active cells in the wiring path
        if self.active_cell_coordinates is not None:
            active_set = set(self.active_cell_coordinates)
            path = [(x, y) for (x, y) in path if (x, y) in active_set]
        
        # Step 4: Convert (x, y) path to design cell indices
        # Design cells are numbered sequentially: cell_idx = y * width + x
        mapping = []
        for (x, y) in path:
            design_cell_idx = y * w + x
            mapping.append(design_cell_idx)
            
        return mapping
    
    def get_hardware_index(self, design_x: int, design_y: int) -> int:
        """
        Get the hardware strip index for a given design cell position.
        
        Args:
            design_x: X coordinate in design grid (0 = left)
            design_y: Y coordinate in design grid (0 = top)
            
        Returns:
            Hardware strip index (0 = first LED in strip)
        """
        design_idx = design_y * self.width + design_x
        mapping = self._build_mapping_table()
        
        # Find which hardware position corresponds to this design cell
        try:
            return mapping.index(design_idx)
        except ValueError:
            return -1  # Not found

