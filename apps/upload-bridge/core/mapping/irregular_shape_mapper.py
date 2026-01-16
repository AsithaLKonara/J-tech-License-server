"""
Irregular Shape Mapper - Handles irregular/custom shape canvas operations.

This module provides functionality for LED Build-style irregular shapes where
users can define which grid cells contain LEDs (active) and which are empty (holes/gaps).
"""

from typing import List, Tuple, Optional
from core.pattern import PatternMetadata


class IrregularShapeMapper:
    """Handles irregular shape operations for custom LED arrangements."""
    
    @staticmethod
    def is_cell_active(x: int, y: int, metadata: PatternMetadata) -> bool:
        """
        Check if a grid cell is active (has an LED).
        
        Args:
            x: Grid X coordinate
            y: Grid Y coordinate
            metadata: PatternMetadata with irregular shape configuration
            
        Returns:
            True if cell is active, False otherwise
        """
        # If irregular shapes not enabled, all cells are active (backward compatible)
        if not metadata.irregular_shape_enabled:
            return 0 <= x < metadata.width and 0 <= y < metadata.height
        
        # If no active cell coordinates defined (None), all cells are active (backward compat)
        # If empty list, no cells are active
        if metadata.active_cell_coordinates is None:
            return 0 <= x < metadata.width and 0 <= y < metadata.height
        
        # Empty list means no active cells
        if len(metadata.active_cell_coordinates) == 0:
            return False
        
        # Check if (x, y) is in the active cell list
        return (x, y) in metadata.active_cell_coordinates
    
    @staticmethod
    def get_active_cell_count(metadata: PatternMetadata) -> int:
        """
        Get the number of active cells.
        
        Args:
            metadata: PatternMetadata with irregular shape configuration
            
        Returns:
            Number of active cells
        """
        if not metadata.irregular_shape_enabled:
            return metadata.width * metadata.height
        
        # If None, all cells are active (backward compat)
        if metadata.active_cell_coordinates is None:
            return metadata.width * metadata.height
        
        # Empty list means no active cells
        return len(metadata.active_cell_coordinates)
    
    @staticmethod
    def generate_mask_from_coordinates(
        coordinates: List[Tuple[int, int]], 
        width: int, 
        height: int
    ) -> List[List[bool]]:
        """
        Convert coordinate list to 2D boolean mask.
        
        Args:
            coordinates: List of (x, y) tuples for active cells
            width: Grid width
            height: Grid height
            
        Returns:
            2D list: mask[y][x] = True if cell is active
        """
        mask = [[False for _ in range(width)] for _ in range(height)]
        
        for x, y in coordinates:
            if 0 <= x < width and 0 <= y < height:
                mask[y][x] = True
        
        return mask
    
    @staticmethod
    def get_coordinates_from_mask(mask: List[List[bool]]) -> List[Tuple[int, int]]:
        """
        Convert 2D boolean mask to coordinate list.
        
        Args:
            mask: 2D list where mask[y][x] = True if cell is active
            
        Returns:
            List of (x, y) tuples for active cells
        """
        coordinates = []
        
        for y, row in enumerate(mask):
            for x, is_active in enumerate(row):
                if is_active:
                    coordinates.append((x, y))
        
        return coordinates
    
    @staticmethod
    def import_from_image(
        image_path: str, 
        threshold: int, 
        grid_width: int, 
        grid_height: int
    ) -> List[Tuple[int, int]]:
        """
        Import active cells from an image file.
        
        Converts image to grayscale, then uses threshold to determine active cells.
        Pixels darker than threshold become active cells.
        
        Args:
            image_path: Path to image file (PNG, BMP, etc.)
            threshold: Grayscale threshold (0-255), pixels <= threshold become active
            grid_width: Target grid width
            grid_height: Target grid height
            
        Returns:
            List of (x, y) tuples for active cells
            
        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If image cannot be loaded
        """
        try:
            from PIL import Image
        except ImportError:
            raise ImportError("PIL (Pillow) is required for image import. Install with: pip install Pillow")
        
        try:
            img = Image.open(image_path)
        except Exception as e:
            raise ValueError(f"Failed to load image: {e}")
        
        # Convert to grayscale
        if img.mode != 'L':
            img = img.convert('L')
        
        # Resize to grid dimensions
        img = img.resize((grid_width, grid_height), Image.Resampling.LANCZOS)
        
        # Get pixel data
        pixels = img.load()
        
        # Find active cells (pixels darker than threshold)
        active_cells = []
        for y in range(grid_height):
            for x in range(grid_width):
                pixel_value = pixels[x, y]
                if pixel_value <= threshold:
                    active_cells.append((x, y))
        
        return active_cells
    
    @staticmethod
    def ensure_active_cells_initialized(metadata: PatternMetadata) -> None:
        """
        Ensure active_cell_coordinates is initialized.
        
        If irregular_shape_enabled is True but active_cell_coordinates is None,
        initialize it to all cells (full grid).
        
        Args:
            metadata: PatternMetadata to initialize
        """
        if metadata.irregular_shape_enabled and metadata.active_cell_coordinates is None:
            # Initialize to all cells
            metadata.active_cell_coordinates = [
                (x, y) 
                for y in range(metadata.height) 
                for x in range(metadata.width)
            ]
    
    @staticmethod
    def toggle_cell(x: int, y: int, metadata: PatternMetadata) -> bool:
        """
        Toggle a cell's active state.
        
        Args:
            x: Grid X coordinate
            y: Grid Y coordinate
            metadata: PatternMetadata with irregular shape configuration
            
        Returns:
            True if cell is now active, False if now inactive
        """
        if not metadata.irregular_shape_enabled:
            return True  # All cells active by default
        
        IrregularShapeMapper.ensure_active_cells_initialized(metadata)
        
        if not metadata.active_cell_coordinates:
            metadata.active_cell_coordinates = []
        
        cell = (x, y)
        if cell in metadata.active_cell_coordinates:
            # Remove cell
            metadata.active_cell_coordinates.remove(cell)
            return False
        else:
            # Add cell
            metadata.active_cell_coordinates.append(cell)
            return True
    
    @staticmethod
    def set_cell_active(x: int, y: int, active: bool, metadata: PatternMetadata) -> None:
        """
        Set a cell's active state explicitly.
        
        Args:
            x: Grid X coordinate
            y: Grid Y coordinate
            active: True to make cell active, False to make inactive
            metadata: PatternMetadata with irregular shape configuration
        """
        if not metadata.irregular_shape_enabled:
            return  # No-op if irregular shapes not enabled
        
        IrregularShapeMapper.ensure_active_cells_initialized(metadata)
        
        if not metadata.active_cell_coordinates:
            metadata.active_cell_coordinates = []
        
        cell = (x, y)
        if active:
            if cell not in metadata.active_cell_coordinates:
                metadata.active_cell_coordinates.append(cell)
        else:
            if cell in metadata.active_cell_coordinates:
                metadata.active_cell_coordinates.remove(cell)
    
    @staticmethod
    def clear_all_cells(metadata: PatternMetadata) -> None:
        """
        Clear all active cells (make all inactive).
        
        Args:
            metadata: PatternMetadata with irregular shape configuration
        """
        if not metadata.irregular_shape_enabled:
            return
        
        metadata.active_cell_coordinates = []
    
    @staticmethod
    def fill_all_cells(metadata: PatternMetadata) -> None:
        """
        Fill all cells (make all active).
        
        Args:
            metadata: PatternMetadata with irregular shape configuration
        """
        if not metadata.irregular_shape_enabled:
            return
        
        metadata.active_cell_coordinates = [
            (x, y) 
            for y in range(metadata.height) 
            for x in range(metadata.width)
        ]

