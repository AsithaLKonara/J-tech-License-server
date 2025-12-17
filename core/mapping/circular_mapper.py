"""
Circular Mapper - Coordinate mapping between 2D grid and circular LED layouts.

This module implements the LED Matrix Studio-style circular view concept:
- The canvas is always a rectangular grid (rows × columns)
- Users paint normally using X,Y coordinates
- A circular mapping table interprets the grid as a circular layout
- Preview and export use the mapping table to reorder pixels

KEY PRINCIPLE: "Circular View is a lens, not a new world"
- Grid-based editing remains primary
- Circular layout is an interpretation layer only
- Mapping table is the single source of truth
- No polar drawing or special circular tools

This module provides functions to map between:
- Grid coordinates (x, y) in a virtual 2D matrix
- LED indices in a circular/ring/arc layout (0..N-1 physical order)
"""

import math
from typing import List, Tuple, Optional
from core.pattern import PatternMetadata


class CircularMapper:
    """Maps between 2D grid coordinates and circular LED layouts."""
    
    @staticmethod
    def generate_circular_positions(
        led_count: int,
        radius: float,
        start_angle: float,
        end_angle: float,
        inner_radius: Optional[float] = None
    ) -> List[Tuple[float, float]]:
        """
        Generate LED positions in polar coordinates.
        
        Args:
            led_count: Number of LEDs in the circular layout
            radius: Outer radius
            start_angle: Start angle in degrees
            end_angle: End angle in degrees
            inner_radius: Inner radius for ring layouts (None for filled circle)
            
        Returns:
            List of (angle_rad, radius) tuples in polar coordinates
        """
        positions = []
        start_rad = math.radians(start_angle)
        end_rad = math.radians(end_angle)
        angle_range = end_rad - start_rad
        
        for i in range(led_count):
            # Calculate angle for this LED
            t = i / (led_count - 1) if led_count > 1 else 0.0
            angle = start_rad + t * angle_range
            
            # For ring layouts, LEDs are typically on the outer radius
            # (inner radius is just for visual bounds)
            # For future enhancement, could interpolate radius for multi-ring layouts
            if inner_radius is not None:
                # For ring, use outer radius (LEDs on outer ring)
                led_radius = radius
            else:
                # For filled circle, use the specified radius
                led_radius = radius
            
            positions.append((angle, led_radius))
        
        return positions
    
    @staticmethod
    def polar_to_cartesian(angle: float, radius: float, center_x: float, center_y: float) -> Tuple[float, float]:
        """Convert polar coordinates to cartesian."""
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        return (x, y)
    
    @staticmethod
    def generate_multi_ring_mapping(metadata: PatternMetadata) -> List[Tuple[int, int]]:
        """
        Generate mapping table for multiple concentric rings (Budurasmala).
        
        Args:
            metadata: PatternMetadata with multi_ring configuration
            
        Returns:
            List of (x, y) tuples, where mapping_table[led_idx] = (x, y)
            
        Raises:
            ValueError: If multi-ring parameters are invalid
        """
        if metadata.multi_ring_count is None or metadata.multi_ring_count < 1:
            raise ValueError(f"multi_ring_count must be >= 1, got {metadata.multi_ring_count}")
        
        grid_width = metadata.width
        grid_height = metadata.height
        center_x = (grid_width - 1) / 2.0
        center_y = (grid_height - 1) / 2.0
        
        # Validate ring configuration
        if len(metadata.ring_led_counts) != metadata.multi_ring_count:
            raise ValueError(f"ring_led_counts length ({len(metadata.ring_led_counts)}) must match multi_ring_count ({metadata.multi_ring_count})")
        if len(metadata.ring_radii) != metadata.multi_ring_count:
            raise ValueError(f"ring_radii length ({len(metadata.ring_radii)}) must match multi_ring_count ({metadata.multi_ring_count})")
        
        mapping = []
        total_leds = sum(metadata.ring_led_counts)
        
        # Generate mapping for each ring, starting from innermost
        # LEDs are ordered: ring 0 (inner), ring 1, ..., ring N-1 (outer)
        for ring_idx in range(metadata.multi_ring_count):
            led_count = metadata.ring_led_counts[ring_idx]
            radius = metadata.ring_radii[ring_idx]
            
            # Generate positions for this ring (full circle, 0-360 degrees)
            positions = CircularMapper.generate_circular_positions(
                led_count=led_count,
                radius=radius,
                start_angle=0.0,
                end_angle=360.0,
                inner_radius=None
            )
            
            # Map each LED position to grid cell
            for angle, led_radius in positions:
                x_rel, y_rel = CircularMapper.polar_to_cartesian(angle, led_radius, 0.0, 0.0)
                grid_x = int(round(center_x + x_rel))
                grid_y = int(round(center_y + y_rel))
                
                # Clamp to grid bounds
                grid_x = max(0, min(grid_width - 1, grid_x))
                grid_y = max(0, min(grid_height - 1, grid_y))
                
                mapping.append((grid_x, grid_y))
        
        # Set circular_led_count for compatibility
        if metadata.circular_led_count is None:
            metadata.circular_led_count = total_leds
        
        return mapping
    
    @staticmethod
    def generate_radial_ray_mapping(metadata: PatternMetadata) -> List[Tuple[int, int]]:
        """
        Generate mapping table for radial ray pattern (Budurasmala).
        
        LEDs are arranged along straight lines (rays) extending from center outward.
        
        Args:
            metadata: PatternMetadata with radial_rays configuration
            
        Returns:
            List of (x, y) tuples, where mapping_table[led_idx] = (x, y)
            
        Raises:
            ValueError: If radial ray parameters are invalid
        """
        if metadata.ray_count is None or metadata.ray_count < 1:
            raise ValueError(f"ray_count must be >= 1, got {metadata.ray_count}")
        if metadata.leds_per_ray is None or metadata.leds_per_ray < 1:
            raise ValueError(f"leds_per_ray must be >= 1, got {metadata.leds_per_ray}")
        
        grid_width = metadata.width
        grid_height = metadata.height
        center_x = (grid_width - 1) / 2.0
        center_y = (grid_height - 1) / 2.0
        
        # Calculate max radius (fit to grid)
        max_radius = min(grid_width, grid_height) / 2.0 - 1.0
        if max_radius < 0.5:
            max_radius = 0.5
        
        # Calculate ray spacing angle
        if metadata.ray_spacing_angle is not None:
            ray_spacing_rad = math.radians(metadata.ray_spacing_angle)
        else:
            # Auto-calculate: evenly space rays around full circle
            ray_spacing_rad = (2 * math.pi) / metadata.ray_count
        
        mapping = []
        total_leds = metadata.ray_count * metadata.leds_per_ray
        
        # Generate mapping for each ray
        # LEDs are ordered: ray 0 (all LEDs), ray 1 (all LEDs), ..., ray N-1 (all LEDs)
        for ray_idx in range(metadata.ray_count):
            # Calculate angle for this ray
            ray_angle = ray_idx * ray_spacing_rad
            
            # Generate LEDs along this ray (from center outward)
            for led_idx_in_ray in range(metadata.leds_per_ray):
                # Calculate distance from center (evenly spaced along ray)
                t = (led_idx_in_ray + 1) / metadata.leds_per_ray  # 0 to 1
                led_radius = t * max_radius
                
                # Convert to cartesian
                x_rel, y_rel = CircularMapper.polar_to_cartesian(ray_angle, led_radius, 0.0, 0.0)
                grid_x = int(round(center_x + x_rel))
                grid_y = int(round(center_y + y_rel))
                
                # Clamp to grid bounds
                grid_x = max(0, min(grid_width - 1, grid_x))
                grid_y = max(0, min(grid_height - 1, grid_y))
                
                mapping.append((grid_x, grid_y))
        
        # Set circular_led_count for compatibility
        if metadata.circular_led_count is None:
            metadata.circular_led_count = total_leds
        
        return mapping
    
    @staticmethod
    def generate_custom_position_mapping(metadata: PatternMetadata) -> List[Tuple[int, int]]:
        """
        Generate mapping table from custom LED positions (for custom PCBs).
        
        This allows importing LED positions from PCB design files or manual entry.
        Positions can be in mm, inches, or grid units.
        
        Args:
            metadata: PatternMetadata with custom_led_positions configured
            
        Returns:
            List of (x, y) tuples, where mapping_table[led_idx] = (x, y)
            
        Raises:
            ValueError: If custom_led_positions is invalid
        """
        if not metadata.custom_led_positions:
            raise ValueError("custom_led_positions must be provided for custom position layout")
        
        grid_width = metadata.width
        grid_height = metadata.height
        center_x = (grid_width - 1) / 2.0
        center_y = (grid_height - 1) / 2.0
        
        # Determine scale factor based on units
        if metadata.led_position_units == "grid":
            # Positions are already in grid units
            scale_factor = 1.0
            offset_x = 0.0
            offset_y = 0.0
        elif metadata.led_position_units == "mm":
            # Convert mm to grid units (assuming 1 grid unit = 1mm, adjust as needed)
            # For Budurasmala, typical PCB might be 100-200mm diameter
            # Grid might be 20x20, so scale appropriately
            # Find bounding box of positions
            if metadata.custom_led_positions:
                x_coords = [pos[0] for pos in metadata.custom_led_positions]
                y_coords = [pos[1] for pos in metadata.custom_led_positions]
                min_x, max_x = min(x_coords), max(x_coords)
                min_y, max_y = min(y_coords), max(y_coords)
                width_mm = max_x - min_x
                height_mm = max_y - min_y
                
                # Scale to fit grid (leave 10% margin)
                scale_x = (grid_width * 0.9) / width_mm if width_mm > 0 else 1.0
                scale_y = (grid_height * 0.9) / height_mm if height_mm > 0 else 1.0
                scale_factor = min(scale_x, scale_y)
                
                # Center the positions
                center_x_mm = (min_x + max_x) / 2.0
                center_y_mm = (min_y + max_y) / 2.0
                offset_x = center_x - (center_x_mm * scale_factor)
                offset_y = center_y - (center_y_mm * scale_factor)
            else:
                scale_factor = 1.0
                offset_x = center_x
                offset_y = center_y
        elif metadata.led_position_units == "inches":
            # Convert inches to mm first, then to grid
            # 1 inch = 25.4 mm
            inch_to_mm = 25.4
            # Use same logic as mm but convert first
            if metadata.custom_led_positions:
                x_coords = [pos[0] * inch_to_mm for pos in metadata.custom_led_positions]
                y_coords = [pos[1] * inch_to_mm for pos in metadata.custom_led_positions]
                min_x, max_x = min(x_coords), max(x_coords)
                min_y, max_y = min(y_coords), max(y_coords)
                width_mm = max_x - min_x
                height_mm = max_y - min_y
                
                scale_x = (grid_width * 0.9) / width_mm if width_mm > 0 else 1.0
                scale_y = (grid_height * 0.9) / height_mm if height_mm > 0 else 1.0
                scale_factor = min(scale_x, scale_y)
                
                center_x_mm = (min_x + max_x) / 2.0
                center_y_mm = (min_y + max_y) / 2.0
                offset_x = center_x - (center_x_mm * scale_factor)
                offset_y = center_y - (center_y_mm * scale_factor)
            else:
                scale_factor = 1.0
                offset_x = center_x
                offset_y = center_y
        else:
            raise ValueError(f"Unknown led_position_units: {metadata.led_position_units}")
        
        # Use custom center if provided
        if metadata.custom_position_center_x is not None:
            offset_x = metadata.custom_position_center_x
        if metadata.custom_position_center_y is not None:
            offset_y = metadata.custom_position_center_y
        
        # Map each LED position to grid cell
        mapping = []
        for led_pos in metadata.custom_led_positions:
            # Convert position to grid coordinates
            if metadata.led_position_units == "inches":
                # Convert inches to mm, then scale
                grid_x = (led_pos[0] * 25.4 * scale_factor) + offset_x
                grid_y = (led_pos[1] * 25.4 * scale_factor) + offset_y
            else:
                grid_x = (led_pos[0] * scale_factor) + offset_x
                grid_y = (led_pos[1] * scale_factor) + offset_y
            
            # Round to nearest grid cell
            grid_x = int(round(grid_x))
            grid_y = int(round(grid_y))
            
            # Clamp to grid bounds
            grid_x = max(0, min(grid_width - 1, grid_x))
            grid_y = max(0, min(grid_height - 1, grid_y))
            
            mapping.append((grid_x, grid_y))
        
        # Set circular_led_count for compatibility
        if metadata.circular_led_count is None:
            metadata.circular_led_count = len(metadata.custom_led_positions)
        
        return mapping
    
    @staticmethod
    def generate_mapping_table(metadata: PatternMetadata) -> List[Tuple[int, int]]:
        """
        Generate mapping table: LED index -> (grid_x, grid_y).
        
        For each LED in the circular layout, find the nearest grid cell.
        This is the SINGLE SOURCE OF TRUTH for circular layout mapping.
        The mapping table is deterministic and stable across sessions.
        
        Args:
            metadata: PatternMetadata with circular layout configuration
            
        Returns:
            List of (x, y) tuples, where mapping_table[led_idx] = (x, y)
            
        Raises:
            ValueError: If circular_led_count is not set for circular layouts
        """
        if metadata.layout_type == "rectangular":
            # For rectangular layouts, create 1:1 mapping (row-major order)
            mapping = []
            for y in range(metadata.height):
                for x in range(metadata.width):
                    mapping.append((x, y))
            return mapping
        
        # Handle multi-ring layout (Budurasmala)
        if metadata.layout_type == "multi_ring":
            return CircularMapper.generate_multi_ring_mapping(metadata)
        
        # Handle radial ray layout: ray count = columns, LED per ray = rows
        # Outer ring = top row (row 0), inner ring = bottom row (row height-1)
        if metadata.layout_type == "radial_rays":
            # Use row/column interpretation: columns = rays, rows = LEDs per ray
            ray_count = metadata.width  # columns = ray count
            leds_per_ray = metadata.height  # rows = LEDs per ray
            total_leds = ray_count * leds_per_ray
            
            # Set circular_led_count if not already set
            if metadata.circular_led_count is None:
                metadata.circular_led_count = total_leds
            
            # Auto-set ray_count and leds_per_ray from width/height if not set
            if metadata.ray_count is None:
                metadata.ray_count = ray_count
            if metadata.leds_per_ray is None:
                metadata.leds_per_ray = leds_per_ray
            
            mapping = []
            # Generate mapping: ray by ray, LED by LED
            # Outer ring (row=0) = top row, inner ring (row=height-1) = bottom row
            for ray_idx in range(ray_count):
                for row in range(leds_per_ray):  # row 0 = outer, row height-1 = inner
                    # Map to grid: (ray_idx, row) -> (col, row)
                    # Outer ring (row=0) = top row, inner ring (row=height-1) = bottom row
                    grid_x = ray_idx  # column = ray index
                    grid_y = row  # row 0 = outer circle (top row), row height-1 = inner circle (bottom row)
                    mapping.append((grid_x, grid_y))
            return mapping
        
        # Handle custom LED positions (for custom PCBs)
        if metadata.layout_type == "custom_positions" and metadata.custom_led_positions:
            return CircularMapper.generate_custom_position_mapping(metadata)
        
        # Handle radial layout: rows = circles, columns = LEDs per circle
        # Left column = arch start angle, right column = arch end angle
        if metadata.layout_type == "radial":
            # Row/column interpretation (LMS-style)
            num_circles = metadata.height
            leds_per_circle = metadata.width
            total_leds = num_circles * leds_per_circle
            
            # Set circular_led_count if not already set (for export compatibility)
            # Export system expects this to be set, but we use row/column interpretation
            if metadata.circular_led_count is None:
                metadata.circular_led_count = total_leds
            
            # Calculate center
            center_x = (metadata.width - 1) / 2.0
            center_y = (metadata.height - 1) / 2.0
            
            # Calculate radius range (inner to outer)
            outer_radius = min(metadata.width, metadata.height) / 2.0 - 1.0
            inner_radius = outer_radius * 0.15
            radius_delta = (outer_radius - inner_radius) / max(1, num_circles - 1) if num_circles > 1 else 0
            
            # Get start/end angles for arch
            start_angle = metadata.circular_start_angle
            end_angle = metadata.circular_end_angle
            angle_range = end_angle - start_angle
            
            mapping = []
            for row in range(num_circles):  # Each row = different circle
                radius = inner_radius + radius_delta * row
                
                for col in range(leds_per_circle):  # Each col = arc position
                    # Interpret column as arc position
                    # Left column (0) = start angle, right column (width-1) = end angle
                    t = col / max(1, leds_per_circle - 1) if leds_per_circle > 1 else 0.0  # 0 to 1
                    angle_deg = start_angle + t * angle_range
                    angle_rad = math.radians(angle_deg)
                    
                    # Convert to cartesian
                    x_rel = radius * math.cos(angle_rad)
                    y_rel = radius * math.sin(angle_rad)
                    grid_x = int(round(center_x + x_rel))
                    grid_y = int(round(center_y + y_rel))
                    
                    # Clamp to grid bounds
                    grid_x = max(0, min(metadata.width - 1, grid_x))
                    grid_y = max(0, min(metadata.height - 1, grid_y))
                    
                    mapping.append((grid_x, grid_y))
            
            return mapping
        
        # Handle circular layout: ray = column, led_per_ray = row
        # Top row (row 0) = outer circle, bottom row (height-1) = inner circle
        if metadata.layout_type == "circle" or metadata.layout_type == "ring":
            # Use row/column interpretation: columns are rays, rows are LEDs per ray
            ray_count = metadata.width  # Number of columns (rays)
            leds_per_ray = metadata.height  # Number of rows (LEDs per ray)
            total_leds = ray_count * leds_per_ray
            
            # Set circular_led_count if not already set
            if metadata.circular_led_count is None:
                metadata.circular_led_count = total_leds
            
            mapping = []
            # Generate mapping: for each ray (column), map LEDs from outer (top row) to inner (bottom row)
            # LED index order: ray 0 (all LEDs), ray 1 (all LEDs), ..., ray N-1 (all LEDs)
            # Within each ray: outer (row=0) to inner (row=height-1)
            for col in range(ray_count):  # For each ray (column)
                for row in range(leds_per_ray):  # For each LED along the ray
                    # Map from outer (top row) to inner (bottom row)
                    # row=0 -> outer circle (top row)
                    # row=height-1 -> inner circle (bottom row)
                    mapping.append((col, row))
            
            # Verify mapping order: LED 0 should map to row 0 (outer), LED N-1 should map to row height-1 (inner)
            if len(mapping) > 0:
                first_x, first_y = mapping[0]
                last_x, last_y = mapping[-1]
                # For ray-based interpretation: first LED should be row 0, last should be row height-1
                if first_y != 0 or last_y != leds_per_ray - 1:
                    import logging
                    logging.warning(
                        f"Mapping order validation: LED 0 -> row {first_y} (expected 0), "
                        f"LED {len(mapping)-1} -> row {last_y} (expected {leds_per_ray-1})"
                    )
            
            return mapping
        
        if metadata.circular_led_count is None:
            raise ValueError("circular_led_count must be set for circular layouts")
        
        led_count = metadata.circular_led_count
        grid_width = metadata.width
        grid_height = metadata.height
        
        # Validate grid size
        if grid_width < 1 or grid_height < 1:
            raise ValueError(f"Invalid grid size: {grid_width}x{grid_height}")
        
        # Validate LED count
        if led_count < 1:
            raise ValueError(f"circular_led_count must be >= 1, got {led_count}")
        
        # Calculate center of grid
        center_x = (grid_width - 1) / 2.0
        center_y = (grid_height - 1) / 2.0
        
        # Determine radius if not set
        radius = metadata.circular_radius
        if radius is None:
            # Auto-calculate radius to fit grid (leave 1 pixel margin)
            radius = min(grid_width, grid_height) / 2.0 - 1.0
            if radius < 0.5:
                radius = 0.5  # Minimum radius
        
        # Validate radius
        if radius <= 0:
            raise ValueError(f"circular_radius must be > 0, got {radius}")
        
        # Get start/end angles
        start_angle = metadata.circular_start_angle
        end_angle = metadata.circular_end_angle
        
        # Validate angles
        if start_angle < 0 or start_angle >= 360:
            raise ValueError(f"circular_start_angle must be 0-360, got {start_angle}")
        if end_angle <= start_angle or end_angle > 360:
            raise ValueError(f"circular_end_angle must be > start_angle and <= 360, got {end_angle}")
        
        # Validate ring-specific parameters
        if metadata.layout_type == "ring" and metadata.circular_inner_radius is not None:
            if metadata.circular_inner_radius >= radius:
                raise ValueError(f"circular_inner_radius ({metadata.circular_inner_radius}) must be < circular_radius ({radius})")
            if metadata.circular_inner_radius < 0:
                raise ValueError(f"circular_inner_radius must be >= 0, got {metadata.circular_inner_radius}")
        
        # Generate LED positions in polar coordinates
        positions = CircularMapper.generate_circular_positions(
            led_count=led_count,
            radius=radius,
            start_angle=start_angle,
            end_angle=end_angle,
            inner_radius=metadata.circular_inner_radius
        )
        
        # Map each LED position to nearest grid cell
        # This mapping is deterministic - same inputs always produce same outputs
        mapping = []
        for angle, led_radius in positions:
            # Convert polar to cartesian (relative to center)
            x_rel, y_rel = CircularMapper.polar_to_cartesian(angle, led_radius, 0.0, 0.0)
            
            # Convert to grid coordinates
            grid_x = int(round(center_x + x_rel))
            grid_y = int(round(center_y + y_rel))
            
            # Clamp to grid bounds (ensures all mappings are valid)
            grid_x = max(0, min(grid_width - 1, grid_x))
            grid_y = max(0, min(grid_height - 1, grid_y))
            
            mapping.append((grid_x, grid_y))
        
        return mapping
    
    @staticmethod
    def grid_to_led_index(x: int, y: int, metadata: PatternMetadata) -> Optional[int]:
        """
        Convert grid coordinate to LED index.
        
        Args:
            x: Grid X coordinate
            y: Grid Y coordinate
            metadata: PatternMetadata with circular layout configuration
            
        Returns:
            LED index if found, None otherwise
        """
        if metadata.layout_type == "rectangular":
            # For rectangular, use standard row-major mapping
            if 0 <= x < metadata.width and 0 <= y < metadata.height:
                return y * metadata.width + x
            return None
        
        # For circular layouts, use reverse lookup in mapping table
        if metadata.circular_mapping_table is None:
            # Generate mapping table if not present
            metadata.circular_mapping_table = CircularMapper.generate_mapping_table(metadata)
        
        mapping_table = metadata.circular_mapping_table
        
        # Find LED index that maps to this grid cell
        for led_idx, (grid_x, grid_y) in enumerate(mapping_table):
            if grid_x == x and grid_y == y:
                return led_idx
        
        return None
    
    @staticmethod
    def led_index_to_grid(led_idx: int, metadata: PatternMetadata) -> Optional[Tuple[int, int]]:
        """
        Convert LED index to grid coordinate.
        
        Args:
            led_idx: LED index in circular layout
            metadata: PatternMetadata with circular layout configuration
            
        Returns:
            (x, y) grid coordinate if found, None otherwise
        """
        if metadata.layout_type == "rectangular":
            # For rectangular, use standard row-major mapping
            if led_idx < 0 or led_idx >= metadata.led_count:
                return None
            x = led_idx % metadata.width
            y = led_idx // metadata.width
            return (x, y)
        
        # For circular layouts, use mapping table
        if metadata.circular_mapping_table is None:
            # Generate mapping table if not present
            metadata.circular_mapping_table = CircularMapper.generate_mapping_table(metadata)
        
        mapping_table = metadata.circular_mapping_table
        
        if 0 <= led_idx < len(mapping_table):
            return mapping_table[led_idx]
        
        return None
    
    @staticmethod
    def get_led_count_for_layout(metadata: PatternMetadata) -> int:
        """
        Get the number of LEDs for the layout.
        
        For rectangular: width * height
        For circular: circular_led_count
        
        This is the physical LED count, not the grid size.
        """
        if metadata.layout_type == "rectangular":
            return metadata.led_count
        return metadata.circular_led_count or metadata.led_count
    
    @staticmethod
    def validate_mapping_table(metadata: PatternMetadata) -> Tuple[bool, Optional[str]]:
        """
        Validate that the mapping table is consistent with metadata.
        
        This ensures the mapping table (single source of truth) is valid
        before use in preview or export.
        
        Returns:
            (is_valid, error_message)
        """
        if metadata.layout_type == "rectangular":
            # Rectangular layouts don't need mapping table validation
            return (True, None)
        
        if not metadata.circular_mapping_table:
            return (False, "circular_mapping_table is None - cannot use circular layout without mapping")
        
        # For multi-ring and radial_rays, calculate expected LED count
        expected_led_count = metadata.circular_led_count
        if metadata.layout_type == "multi_ring" and metadata.multi_ring_count:
            expected_led_count = sum(metadata.ring_led_counts) if metadata.ring_led_counts else expected_led_count
        elif metadata.layout_type == "radial_rays" and metadata.ray_count and metadata.leds_per_ray:
            expected_led_count = metadata.ray_count * metadata.leds_per_ray
        
        if expected_led_count is None:
            return (False, "circular_led_count is None - required for circular layouts")
        
        if len(metadata.circular_mapping_table) != expected_led_count:
            return (False, f"Mapping table length ({len(metadata.circular_mapping_table)}) != expected LED count ({expected_led_count})")
        
        # Validate all mappings are within grid bounds
        # This ensures we can safely read from grid without index errors
        for led_idx, (grid_x, grid_y) in enumerate(metadata.circular_mapping_table):
            if not isinstance(grid_x, int) or not isinstance(grid_y, int):
                return (False, f"LED {led_idx} has non-integer grid coordinates: ({grid_x}, {grid_y})")
            if not (0 <= grid_x < metadata.width):
                return (False, f"LED {led_idx} maps to invalid grid_x: {grid_x} (width={metadata.width})")
            if not (0 <= grid_y < metadata.height):
                return (False, f"LED {led_idx} maps to invalid grid_y: {grid_y} (height={metadata.height})")
        
        return (True, None)
    
    @staticmethod
    def is_mapped(x: int, y: int, metadata: PatternMetadata) -> bool:
        """
        Check if grid cell (x, y) is mapped to a LED.
        
        For rectangular layouts, all cells are mapped.
        For circular layouts, only cells in the mapping table are mapped.
        
        Args:
            x: Grid X coordinate
            y: Grid Y coordinate
            metadata: PatternMetadata with layout configuration
            
        Returns:
            True if (x, y) is mapped to a LED, False otherwise
        """
        if metadata.layout_type == "rectangular":
            # All cells are mapped in rectangular layouts
            return 0 <= x < metadata.width and 0 <= y < metadata.height
        
        # For circular layouts, check if (x, y) is in mapping table
        if not metadata.circular_mapping_table:
            return False
        
        # Check if (x, y) appears in mapping table
        return (x, y) in metadata.circular_mapping_table
    
    @staticmethod
    def ensure_mapping_table(metadata: PatternMetadata) -> bool:
        """
        Ensure mapping table exists, generating it if necessary.
        
        This is a safe helper that regenerates the mapping table if missing
        or invalid. Used when loading patterns that may have missing tables.
        
        Returns:
            True if mapping table is now valid, False if generation failed
        """
        if metadata.layout_type == "rectangular":
            return True
        
        # Check if mapping table exists and is valid
        is_valid, error_msg = CircularMapper.validate_mapping_table(metadata)
        if is_valid:
            return True
        
        # Try to regenerate
        try:
            metadata.circular_mapping_table = CircularMapper.generate_mapping_table(metadata)
            # Validate the regenerated table
            is_valid, error_msg = CircularMapper.validate_mapping_table(metadata)
            return is_valid
        except Exception:
            return False
    
    @staticmethod
    def suggest_grid_size(led_count: int, layout_type: str) -> Tuple[int, int]:
        """
        Suggest appropriate grid dimensions for a circular layout.
        
        This calculates grid size that will be large enough to accommodate
        all LEDs in the circular layout. The grid should be at least as large
        as needed to map all LED positions.
        
        Args:
            led_count: Number of LEDs in the circular layout
            layout_type: Layout type ("circle", "ring", "arc", "multi_ring", "radial_rays", etc.)
            
        Returns:
            Tuple of (width, height) suggested grid dimensions
        """
        # For simple circular layouts, use a square grid
        # Size should be at least sqrt(led_count) to ensure we have enough cells
        # Add some margin for better mapping accuracy
        base_size = int((led_count ** 0.5) * 1.5) + 2
        
        # Round up to next even number for better symmetry
        base_size = (base_size + 1) // 2 * 2
        
        # Minimum size
        base_size = max(base_size, 8)
        
        # For multi-ring and radial layouts, might need larger grid
        if layout_type in ["multi_ring", "radial_rays"]:
            base_size = max(base_size, 16)
        
        return (base_size, base_size)
    
    @staticmethod
    def generate_led_positions_for_preview(
        metadata: PatternMetadata, 
        center_x: float, 
        center_y: float, 
        max_radius: float
    ) -> List[Tuple[float, float]]:
        """
        Generate LED positions in screen coordinates for preview rendering.
        
        This method generates the actual physical LED positions based on layout geometry,
        matching how LED Matrix Studio would position LEDs in a circular view.
        
        Args:
            metadata: PatternMetadata with layout configuration
            center_x: Screen X coordinate of center
            center_y: Screen Y coordinate of center
            max_radius: Maximum radius available for rendering
            
        Returns:
            List of (x, y) tuples in screen coordinates, indexed by LED index (0..N-1)
            Each tuple represents the screen position where that LED should be rendered.
        """
        if metadata.layout_type == "rectangular":
            # Rectangular layouts don't use circular preview
            return []
        
        # Ensure mapping table exists
        if not metadata.circular_mapping_table:
            CircularMapper.ensure_mapping_table(metadata)
        
        if not metadata.circular_mapping_table:
            return []
        
        led_count = len(metadata.circular_mapping_table)
        positions = []
        
        # Handle multi-ring layout
        if metadata.layout_type == "multi_ring":
            if not metadata.multi_ring_count or not metadata.ring_radii:
                return []
            
            # Scale radii to fit in max_radius
            max_physical_radius = max(metadata.ring_radii) if metadata.ring_radii else 1.0
            scale_factor = (max_radius * 0.8) / max_physical_radius if max_physical_radius > 0 else 1.0
            
            led_idx = 0
            for ring_idx in range(metadata.multi_ring_count):
                ring_led_count = metadata.ring_led_counts[ring_idx] if ring_idx < len(metadata.ring_led_counts) else 0
                ring_radius = metadata.ring_radii[ring_idx] if ring_idx < len(metadata.ring_radii) else 0.0
                
                # Generate positions for this ring
                ring_positions = CircularMapper.generate_circular_positions(
                    led_count=ring_led_count,
                    radius=ring_radius,
                    start_angle=0.0,
                    end_angle=360.0,
                    inner_radius=None
                )
                
                # Convert to screen coordinates
                for angle, led_radius in ring_positions:
                    scaled_radius = led_radius * scale_factor
                    x = center_x + scaled_radius * math.cos(angle)
                    y = center_y + scaled_radius * math.sin(angle)
                    positions.append((x, y))
                    led_idx += 1
            
            return positions
        
        # Handle radial ray layout: ray count = columns, LED per ray = rows
        # Outer ring = top row (row 0), inner ring = bottom row (row height-1)
        if metadata.layout_type == "radial_rays":
            # Use row/column interpretation
            ray_count = metadata.width  # columns = ray count
            leds_per_ray = metadata.height  # rows = LEDs per ray
            
            if ray_count < 1 or leds_per_ray < 1:
                return []
            
            # Calculate ray spacing angle
            if metadata.ray_spacing_angle is not None:
                ray_spacing_rad = math.radians(metadata.ray_spacing_angle)
            else:
                ray_spacing_rad = (2 * math.pi) / ray_count
            
            # Scale to fit in max_radius
            outer_radius = max_radius * 0.8
            inner_radius = outer_radius * 0.15
            radius_delta = (outer_radius - inner_radius) / max(1, leds_per_ray - 1) if leds_per_ray > 1 else 0
            
            # Generate positions: ray by ray, from outer (row 0) to inner (row height-1)
            for ray_idx in range(ray_count):
                # Offset angle so Ray 0 is at bottom (π/2 radians = 90° = 6 o'clock)
                # In Qt coordinates: 0° = right, 90° = bottom, 180° = left, 270° = top
                ray_angle = ray_idx * ray_spacing_rad + math.pi / 2
                
                for row in range(leds_per_ray):
                    # Row 0 = outer circle, row height-1 = inner circle
                    # Calculate radius: row 0 has largest radius, row height-1 has smallest
                    # Invert row index so row 0 maps to outer_radius and last row maps to inner_radius
                    inverted_row = leds_per_ray - 1 - row
                    radius = inner_radius + radius_delta * inverted_row
                    
                    # Convert to screen coordinates
                    x = center_x + radius * math.cos(ray_angle)
                    y = center_y + radius * math.sin(ray_angle)
                    positions.append((x, y))
            
            return positions
        
        # Handle custom positions layout
        if metadata.layout_type == "custom_positions" and metadata.custom_led_positions:
            # Scale custom positions to fit in max_radius
            if not metadata.custom_led_positions:
                return []
            
            # Find bounding box of custom positions
            x_coords = [pos[0] for pos in metadata.custom_led_positions]
            y_coords = [pos[1] for pos in metadata.custom_led_positions]
            if not x_coords or not y_coords:
                return []
            
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)
            width_physical = max_x - min_x
            height_physical = max_y - min_y
            
            # Scale to fit in max_radius
            max_dimension = max(width_physical, height_physical)
            scale_factor = (max_radius * 1.6) / max_dimension if max_dimension > 0 else 1.0
            
            # Center the positions
            center_x_physical = (min_x + max_x) / 2.0
            center_y_physical = (min_y + max_y) / 2.0
            
            # Convert each position to screen coordinates
            for led_pos in metadata.custom_led_positions:
                # Convert position units if needed
                if metadata.led_position_units == "inches":
                    pos_x = led_pos[0] * 25.4  # Convert to mm
                    pos_y = led_pos[1] * 25.4
                elif metadata.led_position_units == "mm":
                    pos_x = led_pos[0]
                    pos_y = led_pos[1]
                else:  # grid units
                    pos_x = led_pos[0]
                    pos_y = led_pos[1]
                
                # Scale and center
                x = center_x + (pos_x - center_x_physical) * scale_factor
                y = center_y + (pos_y - center_y_physical) * scale_factor
                positions.append((x, y))
            
            return positions
        
        # Handle radial layout (rows = circles, columns = LEDs per circle)
        if metadata.layout_type == "radial":
            num_circles = metadata.height
            leds_per_circle = metadata.width
            
            # Calculate radius range
            outer_radius = max_radius * 0.8
            inner_radius = outer_radius * 0.15
            radius_delta = (outer_radius - inner_radius) / max(1, num_circles - 1) if num_circles > 1 else 0
            
            # Generate positions for each circle
            for row in range(num_circles):
                radius = inner_radius + radius_delta * row
                
                for col in range(leds_per_circle):
                    angle = 2 * math.pi * (col / max(1, leds_per_circle))
                    x = center_x + radius * math.cos(angle)
                    y = center_y + radius * math.sin(angle)
                    positions.append((x, y))
            
            return positions
        
        # Handle circular/ring layout with ray interpretation: columns = rays, rows = LEDs per ray
        # Top row (row 0) = outer circle, bottom row (height-1) = inner circle
        if metadata.layout_type == "circle" or metadata.layout_type == "ring":
            # Check if this uses ray interpretation (columns=rays, rows=LEDs per ray)
            # This is the case when width and height represent ray structure
            ray_count = metadata.width  # Number of columns (rays)
            leds_per_ray = metadata.height  # Number of rows (LEDs per ray)
            
            if ray_count > 0 and leds_per_ray > 0:
                # Calculate ray spacing angle (evenly spaced around circle)
                ray_spacing_rad = (2 * math.pi) / ray_count if ray_count > 0 else 0
                
                # Scale to fit in max_radius
                outer_radius = max_radius * 0.8
                inner_radius = outer_radius * 0.15
                radius_delta = (outer_radius - inner_radius) / max(1, leds_per_ray - 1) if leds_per_ray > 1 else 0
                
                # Generate positions: ray by ray, from outer (row 0) to inner (row height-1)
                for ray_idx in range(ray_count):
                    # Offset angle so Ray 0 is at bottom (π/2 radians = 90° = 6 o'clock)
                    # In Qt coordinates: 0° = right, 90° = bottom, 180° = left, 270° = top
                    # Note: cos(π/2) = 0, sin(π/2) = 1 → (x=0, y=1) = bottom in screen coords
                    ray_angle = ray_idx * ray_spacing_rad + math.pi / 2
                    
                    # Debug: Log first ray angle to verify offset is applied
                    if ray_idx == 0:
                        import logging
                        logging.debug(f"Ray 0 angle: {math.degrees(ray_angle):.1f}° (should be 90° for bottom)")
                    
                    for row in range(leds_per_ray):
                        # Row 0 = outer circle, row height-1 = inner circle
                        # Calculate radius: row 0 has largest radius, row height-1 has smallest
                        # Invert row index so row 0 maps to outer_radius and last row maps to inner_radius
                        inverted_row = leds_per_ray - 1 - row
                        radius = inner_radius + radius_delta * inverted_row
                        
                        # Convert to screen coordinates
                        x = center_x + radius * math.cos(ray_angle)
                        y = center_y + radius * math.sin(ray_angle)
                        positions.append((x, y))
                
                return positions
        
        # Handle standard circular layouts (circle, ring, arc) - single circle/ring
        # Get layout parameters
        led_count = metadata.circular_led_count or len(metadata.circular_mapping_table)
        radius = metadata.circular_radius
        if radius is None:
            # Auto-calculate radius to fit grid
            radius = min(metadata.width, metadata.height) / 2.0 - 1.0
            if radius < 0.5:
                radius = 0.5
        
        # Scale radius to fit in max_radius
        # Use a reasonable scale factor to fit the layout
        grid_max_dimension = max(metadata.width, metadata.height)
        scale_factor = (max_radius * 0.8) / (grid_max_dimension / 2.0) if grid_max_dimension > 0 else 1.0
        scaled_radius = radius * scale_factor
        
        # Generate LED positions in polar coordinates
        polar_positions = CircularMapper.generate_circular_positions(
            led_count=led_count,
            radius=scaled_radius,
            start_angle=metadata.circular_start_angle,
            end_angle=metadata.circular_end_angle,
            inner_radius=metadata.circular_inner_radius
        )
        
        # Convert polar to screen coordinates
        for angle, led_radius in polar_positions:
            x = center_x + led_radius * math.cos(angle)
            y = center_y + led_radius * math.sin(angle)
            positions.append((x, y))
        
        return positions

