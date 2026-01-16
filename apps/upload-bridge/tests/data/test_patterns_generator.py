"""
Test Data Generator - Creates sample patterns for testing
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from core.pattern import Pattern, Frame, PatternMetadata
from core.mapping.circular_mapper import CircularMapper
import json
from pathlib import Path


def create_rectangular_pattern(width=16, height=16, frames=1, name="Test Rectangular"):
    """Create a rectangular test pattern."""
    metadata = PatternMetadata(width=width, height=height)
    pattern = Pattern(name=name, metadata=metadata)
    
    pattern.frames = []
    for frame_idx in range(frames):
        pixels = []
        for y in range(height):
            for x in range(width):
                # Create a simple pattern
                r = (x * 255) // max(width - 1, 1) if width > 1 else 0
                g = (y * 255) // max(height - 1, 1) if height > 1 else 0
                b = (frame_idx * 255) // max(frames - 1, 1) if frames > 1 else 0
                pixels.append((r, g, b))
        pattern.frames.append(Frame(pixels=pixels, duration_ms=100))
    
    return pattern


def create_circular_pattern(led_count=60, radius=15, name="Test Circular"):
    """Create a circular test pattern."""
    metadata = PatternMetadata(
        width=32,
        height=32,
        layout_type="circle",
        circular_led_count=led_count,
        circular_radius=radius
    )
    
    # Generate mapping table
    CircularMapper.generate_mapping_table(metadata)
    
    pattern = Pattern(name=name, metadata=metadata)
    
    # Create frame with pixels
    pixels = [(0, 0, 0)] * (metadata.width * metadata.height)
    
    # Set some pixels based on mapping
    if metadata.circular_mapping_table:
        for idx, (x, y) in enumerate(metadata.circular_mapping_table):
            if idx < len(pixels):
                # Create a color pattern
                r = (idx * 255) // max(led_count - 1, 1) if led_count > 1 else 0
                g = 128
                b = 255 - r
                pixel_idx = y * metadata.width + x
                if pixel_idx < len(pixels):
                    pixels[pixel_idx] = (r, g, b)
    
    pattern.frames = [Frame(pixels=pixels, duration_ms=100)]
    
    return pattern


def create_multi_ring_pattern(ring_count=3, name="Test Multi-Ring"):
    """Create a multi-ring test pattern."""
    ring_led_counts = [20, 30, 40]
    ring_radii = [10, 15, 20]
    
    metadata = PatternMetadata(
        width=50,
        height=50,
        layout_type="multi_ring",
        multi_ring_count=ring_count,
        ring_led_counts=ring_led_counts[:ring_count],
        ring_radii=ring_radii[:ring_count]
    )
    
    # Generate mapping table
    CircularMapper.generate_mapping_table(metadata)
    
    pattern = Pattern(name=name, metadata=metadata)
    
    # Create frame
    pixels = [(0, 0, 0)] * (metadata.width * metadata.height)
    
    if metadata.circular_mapping_table:
        for idx, (x, y) in enumerate(metadata.circular_mapping_table):
            if idx < len(pixels):
                pixel_idx = y * metadata.width + x
                if pixel_idx < len(pixels):
                    # Color based on ring
                    ring_idx = 0
                    total_leds = 0
                    for i, count in enumerate(ring_led_counts[:ring_count]):
                        if idx < total_leds + count:
                            ring_idx = i
                            break
                        total_leds += count
                    
                    r = (ring_idx * 255) // max(ring_count - 1, 1) if ring_count > 1 else 0
                    g = 128
                    b = 255 - r
                    pixels[pixel_idx] = (r, g, b)
    
    pattern.frames = [Frame(pixels=pixels, duration_ms=100)]
    
    return pattern


def create_radial_rays_pattern(ray_count=8, leds_per_ray=10, name="Test Radial Rays"):
    """Create a radial rays test pattern."""
    metadata = PatternMetadata(
        width=30,
        height=30,
        layout_type="radial_rays",
        ray_count=ray_count,
        leds_per_ray=leds_per_ray
    )
    
    # Generate mapping table
    CircularMapper.generate_mapping_table(metadata)
    
    pattern = Pattern(name=name, metadata=metadata)
    
    # Create frame
    pixels = [(0, 0, 0)] * (metadata.width * metadata.height)
    
    if metadata.circular_mapping_table:
        for idx, (x, y) in enumerate(metadata.circular_mapping_table):
            if idx < len(pixels):
                pixel_idx = y * metadata.width + x
                if pixel_idx < len(pixels):
                    ray_idx = idx // leds_per_ray
                    led_in_ray = idx % leds_per_ray
                    
                    r = (ray_idx * 255) // max(ray_count - 1, 1) if ray_count > 1 else 0
                    g = (led_in_ray * 255) // max(leds_per_ray - 1, 1) if leds_per_ray > 1 else 0
                    b = 128
                    pixels[pixel_idx] = (r, g, b)
    
    pattern.frames = [Frame(pixels=pixels, duration_ms=100)]
    
    return pattern


def save_pattern_as_project(pattern, filepath):
    """Save pattern as .ledproj file."""
    from core.project.project_file import save_project
    from pathlib import Path
    save_project(pattern, Path(filepath))


def save_pattern_as_json(pattern, filepath):
    """Save pattern as JSON file."""
    pattern_dict = pattern.to_dict()
    with open(filepath, 'w') as f:
        json.dump(pattern_dict, f, indent=2)


def main():
    """Generate all test patterns."""
    output_dir = Path(__file__).parent
    output_dir.mkdir(exist_ok=True)
    
    print("Generating test patterns...")
    
    # Rectangular patterns
    print("  Creating rectangular patterns...")
    rect_16x16 = create_rectangular_pattern(16, 16, 1, "Test Rect 16x16")
    save_pattern_as_project(rect_16x16, output_dir / "test_rect_16x16.ledproj")
    save_pattern_as_json(rect_16x16, output_dir / "test_rect_16x16.json")
    
    rect_32x32 = create_rectangular_pattern(32, 32, 5, "Test Rect 32x32 5frames")
    save_pattern_as_project(rect_32x32, output_dir / "test_rect_32x32_5frames.ledproj")
    
    rect_large = create_rectangular_pattern(64, 64, 10, "Test Rect 64x64 10frames")
    save_pattern_as_project(rect_large, output_dir / "test_rect_64x64_10frames.ledproj")
    
    # Circular patterns
    print("  Creating circular patterns...")
    circular_60 = create_circular_pattern(60, 15, "Test Circular 60LEDs")
    save_pattern_as_project(circular_60, output_dir / "test_circular_60leds.ledproj")
    save_pattern_as_json(circular_60, output_dir / "test_circular_60leds.json")
    
    circular_120 = create_circular_pattern(120, 20, "Test Circular 120LEDs")
    save_pattern_as_project(circular_120, output_dir / "test_circular_120leds.ledproj")
    
    # Multi-ring patterns
    print("  Creating multi-ring patterns...")
    multi_ring_3 = create_multi_ring_pattern(3, "Test Multi-Ring 3rings")
    save_pattern_as_project(multi_ring_3, output_dir / "test_multiring_3rings.ledproj")
    save_pattern_as_json(multi_ring_3, output_dir / "test_multiring_3rings.json")
    
    # Radial rays patterns
    print("  Creating radial rays patterns...")
    radial_rays = create_radial_rays_pattern(8, 10, "Test Radial Rays 8x10")
    save_pattern_as_project(radial_rays, output_dir / "test_radial_rays_8x10.ledproj")
    save_pattern_as_json(radial_rays, output_dir / "test_radial_rays_8x10.json")
    
    print(f"\nTest patterns generated in: {output_dir}")
    print("Files created:")
    for file in sorted(output_dir.glob("test_*.ledproj")):
        print(f"  - {file.name}")
    for file in sorted(output_dir.glob("test_*.json")):
        print(f"  - {file.name}")


if __name__ == "__main__":
    main()

