"""
Generate test patterns for preview mapping and irregular wiring testing.

Creates test patterns as specified in the comprehensive testing plan:
- Regular matrices with known color positions
- Irregular matrices with various patterns (cross, border, checkerboard, sparse, single)
- Multi-frame patterns
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from core.pattern import Pattern, Frame, PatternMetadata
from core.project.project_file import save_project
from pathlib import Path


def create_regular_test_pattern(width=8, height=8, name="Test Regular"):
    """
    Create regular rectangular pattern with distinct colors at known positions.
    
    Colors:
    - Top-left (0,0): Red (255,0,0)
    - Top-right (width-1,0): Green (0,255,0)
    - Bottom-left (0,height-1): Blue (0,0,255)
    - Bottom-right (width-1,height-1): Yellow (255,255,0)
    - Center (width//2, height//2): Magenta (255,0,255)
    """
    metadata = PatternMetadata(width=width, height=height)
    pattern = Pattern(name=name, metadata=metadata)
    
    pixels = [(0, 0, 0)] * (width * height)
    
    # Top-left corner: Red
    pixels[0] = (255, 0, 0)
    
    # Top-right corner: Green
    pixels[width - 1] = (0, 255, 0)
    
    # Bottom-left corner: Blue
    pixels[(height - 1) * width] = (0, 0, 255)
    
    # Bottom-right corner: Yellow
    pixels[height * width - 1] = (255, 255, 0)
    
    # Center: Magenta
    center_x = width // 2
    center_y = height // 2
    pixels[center_y * width + center_x] = (255, 0, 255)
    
    pattern.frames = [Frame(pixels=pixels, duration_ms=100)]
    return pattern


def create_irregular_cross_pattern(width=10, height=10, name="Test Irregular Cross"):
    """
    Create irregular matrix with cross pattern (center row and column inactive).
    """
    metadata = PatternMetadata(
        width=width,
        height=height,
        layout_type="irregular",
        irregular_shape_enabled=True
    )
    
    # Create active cells (all except center row and column)
    active_cells = []
    center_row = height // 2
    center_col = width // 2
    
    for y in range(height):
        for x in range(width):
            if x != center_col and y != center_row:
                active_cells.append((x, y))
    
    metadata.active_cell_coordinates = active_cells
    
    pattern = Pattern(name=name, metadata=metadata)
    
    # Create pixels (full grid, but only active cells will be used)
    pixels = [(0, 0, 0)] * (width * height)
    
    # Paint colors on active cells
    # Top-left active cell
    if (0, 0) in active_cells:
        pixels[0] = (255, 0, 0)  # Red
    
    # Center active cell (if not in cross)
    center_x = width // 2
    center_y = height // 2
    # Find a cell near center that's active
    for offset in range(1, min(width, height)):
        for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset)]:
            test_x = center_x + dx
            test_y = center_y + dy
            if (test_x, test_y) in active_cells and 0 <= test_x < width and 0 <= test_y < height:
                pixels[test_y * width + test_x] = (0, 255, 0)  # Green
                break
        else:
            continue
        break
    
    # Bottom-right active cell
    for y in range(height - 1, -1, -1):
        for x in range(width - 1, -1, -1):
            if (x, y) in active_cells:
                pixels[y * width + x] = (0, 0, 255)  # Blue
                break
        else:
            continue
        break
    
    pattern.frames = [Frame(pixels=pixels, duration_ms=100)]
    return pattern


def create_irregular_border_pattern(width=10, height=10, name="Test Irregular Border"):
    """
    Create irregular matrix with border pattern (outer cells inactive).
    """
    metadata = PatternMetadata(
        width=width,
        height=height,
        layout_type="irregular",
        irregular_shape_enabled=True
    )
    
    # Create active cells (only inner cells, border is inactive)
    active_cells = []
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            active_cells.append((x, y))
    
    metadata.active_cell_coordinates = active_cells
    
    pattern = Pattern(name=name, metadata=metadata)
    
    pixels = [(0, 0, 0)] * (width * height)
    
    # Paint colors on active cells
    if active_cells:
        # First active cell: Red
        x, y = active_cells[0]
        pixels[y * width + x] = (255, 0, 0)
        
        # Middle active cell: Green
        mid_idx = len(active_cells) // 2
        x, y = active_cells[mid_idx]
        pixels[y * width + x] = (0, 255, 0)
        
        # Last active cell: Blue
        x, y = active_cells[-1]
        pixels[y * width + x] = (0, 0, 255)
    
    pattern.frames = [Frame(pixels=pixels, duration_ms=100)]
    return pattern


def create_irregular_checkerboard_pattern(width=10, height=10, name="Test Irregular Checkerboard"):
    """
    Create irregular matrix with checkerboard pattern (alternating cells inactive).
    """
    metadata = PatternMetadata(
        width=width,
        height=height,
        layout_type="irregular",
        irregular_shape_enabled=True
    )
    
    # Create active cells (checkerboard pattern)
    active_cells = []
    for y in range(height):
        for x in range(width):
            if (x + y) % 2 == 0:  # Even sum = active
                active_cells.append((x, y))
    
    metadata.active_cell_coordinates = active_cells
    
    pattern = Pattern(name=name, metadata=metadata)
    
    pixels = [(0, 0, 0)] * (width * height)
    
    # Paint colors on active cells
    if active_cells:
        # First active cell: Red
        x, y = active_cells[0]
        pixels[y * width + x] = (255, 0, 0)
        
        # Middle active cell: Green
        mid_idx = len(active_cells) // 2
        x, y = active_cells[mid_idx]
        pixels[y * width + x] = (0, 255, 0)
        
        # Last active cell: Blue
        x, y = active_cells[-1]
        pixels[y * width + x] = (0, 0, 255)
    
    pattern.frames = [Frame(pixels=pixels, duration_ms=100)]
    return pattern


def create_irregular_sparse_pattern(width=10, height=10, num_active=8, name="Test Irregular Sparse"):
    """
    Create irregular matrix with sparse pattern (few scattered active cells).
    """
    metadata = PatternMetadata(
        width=width,
        height=height,
        layout_type="irregular",
        irregular_shape_enabled=True
    )
    
    # Create sparse active cells (scattered)
    import random
    random.seed(42)  # For reproducibility
    all_cells = [(x, y) for y in range(height) for x in range(width)]
    active_cells = random.sample(all_cells, min(num_active, len(all_cells)))
    
    metadata.active_cell_coordinates = active_cells
    
    pattern = Pattern(name=name, metadata=metadata)
    
    pixels = [(0, 0, 0)] * (width * height)
    
    # Paint colors on active cells
    for idx, (x, y) in enumerate(active_cells):
        # Create gradient color
        r = (idx * 255) // max(len(active_cells) - 1, 1) if len(active_cells) > 1 else 0
        g = 128
        b = 255 - r
        pixels[y * width + x] = (r, g, b)
    
    pattern.frames = [Frame(pixels=pixels, duration_ms=100)]
    return pattern


def create_irregular_single_pattern(width=8, height=8, name="Test Irregular Single"):
    """
    Create irregular matrix with only center cell active.
    """
    metadata = PatternMetadata(
        width=width,
        height=height,
        layout_type="irregular",
        irregular_shape_enabled=True
    )
    
    # Only center cell is active
    center_x = width // 2
    center_y = height // 2
    active_cells = [(center_x, center_y)]
    
    metadata.active_cell_coordinates = active_cells
    
    pattern = Pattern(name=name, metadata=metadata)
    
    pixels = [(0, 0, 0)] * (width * height)
    
    # Paint center cell: Magenta
    pixels[center_y * width + center_x] = (255, 0, 255)
    
    pattern.frames = [Frame(pixels=pixels, duration_ms=100)]
    return pattern


def create_multiframe_pattern(base_pattern_func, num_frames=10, name_prefix="Test MultiFrame"):
    """
    Create multi-frame pattern from base pattern function.
    """
    base_pattern = base_pattern_func()
    base_pattern.name = f"{name_prefix} {base_pattern.metadata.width}x{base_pattern.metadata.height}"
    
    # Create additional frames with different colors
    width = base_pattern.metadata.width
    height = base_pattern.metadata.height
    
    for frame_idx in range(1, num_frames):
        pixels = [(0, 0, 0)] * (width * height)
        
        # Create frame-specific pattern
        for y in range(height):
            for x in range(width):
                cell_idx = y * width + x
                # Create color based on frame index
                r = (frame_idx * 255) // max(num_frames - 1, 1) if num_frames > 1 else 0
                g = (x * 255) // max(width - 1, 1) if width > 1 else 0
                b = (y * 255) // max(height - 1, 1) if height > 1 else 0
                pixels[cell_idx] = (r, g, b)
        
        base_pattern.frames.append(Frame(pixels=pixels, duration_ms=100))
    
    return base_pattern


def main():
    """Generate all test patterns."""
    output_dir = Path(__file__).parent
    output_dir.mkdir(exist_ok=True)
    
    print("Generating preview mapping and irregular wiring test patterns...")
    
    # Regular matrices
    print("\n  Creating regular matrices...")
    regular_8x8 = create_regular_test_pattern(8, 8, "Test Regular 8x8")
    save_project(regular_8x8, output_dir / "test_regular_8x8.ledproj")
    print(f"    Created: test_regular_8x8.ledproj")
    
    regular_16x16 = create_regular_test_pattern(16, 16, "Test Regular 16x16")
    save_project(regular_16x16, output_dir / "test_regular_16x16.ledproj")
    print(f"    Created: test_regular_16x16.ledproj")
    
    regular_32x8 = create_regular_test_pattern(32, 8, "Test Regular 32x8")
    save_project(regular_32x8, output_dir / "test_regular_32x8.ledproj")
    print(f"    Created: test_regular_32x8.ledproj")
    
    regular_8x32 = create_regular_test_pattern(8, 32, "Test Regular 8x32")
    save_project(regular_8x32, output_dir / "test_regular_8x32.ledproj")
    print(f"    Created: test_regular_8x32.ledproj")
    
    # Irregular matrices
    print("\n  Creating irregular matrices...")
    irregular_cross = create_irregular_cross_pattern(10, 10, "Test Irregular Cross")
    save_project(irregular_cross, output_dir / "test_irregular_cross.ledproj")
    print(f"    Created: test_irregular_cross.ledproj ({len(irregular_cross.metadata.active_cell_coordinates)} active cells)")
    
    irregular_border = create_irregular_border_pattern(10, 10, "Test Irregular Border")
    save_project(irregular_border, output_dir / "test_irregular_border.ledproj")
    print(f"    Created: test_irregular_border.ledproj ({len(irregular_border.metadata.active_cell_coordinates)} active cells)")
    
    irregular_checkerboard = create_irregular_checkerboard_pattern(10, 10, "Test Irregular Checkerboard")
    save_project(irregular_checkerboard, output_dir / "test_irregular_checkerboard.ledproj")
    print(f"    Created: test_irregular_checkerboard.ledproj ({len(irregular_checkerboard.metadata.active_cell_coordinates)} active cells)")
    
    irregular_sparse = create_irregular_sparse_pattern(10, 10, 8, "Test Irregular Sparse")
    save_project(irregular_sparse, output_dir / "test_irregular_sparse.ledproj")
    print(f"    Created: test_irregular_sparse.ledproj ({len(irregular_sparse.metadata.active_cell_coordinates)} active cells)")
    
    irregular_single = create_irregular_single_pattern(8, 8, "Test Irregular Single")
    save_project(irregular_single, output_dir / "test_irregular_single.ledproj")
    print(f"    Created: test_irregular_single.ledproj ({len(irregular_single.metadata.active_cell_coordinates)} active cell)")
    
    # Multi-frame patterns
    print("\n  Creating multi-frame patterns...")
    multiframe_regular = create_multiframe_pattern(
        lambda: create_regular_test_pattern(8, 8, "Test MultiFrame Regular"),
        num_frames=10,
        name_prefix="Test MultiFrame Regular"
    )
    save_project(multiframe_regular, output_dir / "test_multiframe_regular.ledproj")
    print(f"    Created: test_multiframe_regular.ledproj ({len(multiframe_regular.frames)} frames)")
    
    multiframe_irregular = create_multiframe_pattern(
        lambda: create_irregular_cross_pattern(10, 10, "Test MultiFrame Irregular"),
        num_frames=10,
        name_prefix="Test MultiFrame Irregular"
    )
    save_project(multiframe_irregular, output_dir / "test_multiframe_irregular.ledproj")
    print(f"    Created: test_multiframe_irregular.ledproj ({len(multiframe_irregular.frames)} frames)")
    
    print(f"\n✓ All test patterns generated in: {output_dir}")
    print("\nTest patterns created:")
    for file in sorted(output_dir.glob("test_*.ledproj")):
        print(f"  - {file.name}")


if __name__ == "__main__":
    main()
