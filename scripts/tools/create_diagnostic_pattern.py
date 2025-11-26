"""
Create a comprehensive diagnostic LED pattern for testing all 16 wiring combinations
This pattern has unique identifiers at corners and edges to verify wiring
"""

from core.pattern import Pattern, Frame, PatternMetadata
from parsers.enhanced_binary_parser import EnhancedBinaryParser
import os

def create_diagnostic_pattern(width=12, height=6):
    """
    Create a 12x6 diagnostic pattern with:
    - Unique corner colors (easy to identify)
    - Row markers (to detect row flipping)
    - Column markers (to detect column flipping)
    """
    
    total_leds = width * height
    
    # Create pixels in DESIGN ORDER (left-to-right, top-to-bottom)
    pixels = [(0, 0, 0)] * total_leds  # All black by default
    
    # Corner markers (different colors)
    pixels[0] = (255, 0, 0)  # Top-left = RED
    pixels[width - 1] = (0, 255, 0)  # Top-right = GREEN
    pixels[total_leds - width] = (0, 0, 255)  # Bottom-left = BLUE
    pixels[total_leds - 1] = (255, 255, 0)  # Bottom-right = YELLOW
    
    # Row markers - first LED of each row (except corners) = Magenta
    for row in range(1, height - 1):
        pixels[row * width] = (255, 0, 255)  # Magenta
    
    # Column markers - first LED of each column (except corners) = Cyan
    for col in range(1, width - 1):
        pixels[col] = (0, 255, 255)  # Cyan
    
    # Edge markers - last LED of each row = White
    for row in range(1, height - 1):
        pixels[row * width + (width - 1)] = (255, 255, 255)  # White
    
    # Center marker - middle of matrix = Orange
    mid_x = width // 2
    mid_y = height // 2
    pixels[mid_y * width + mid_x] = (255, 128, 0)  # Orange
    
    # Create pattern
    metadata = PatternMetadata(
        width=width,
        height=height,
        color_order='RGB',
        brightness=1.0,
        wiring_mode='Row-major',  # Design order
        data_in_corner='LT'
    )
    
    frames = [Frame(pixels=pixels, duration_ms=2000)]
    pattern = Pattern(name=f"Diagnostic {width}x{height}", metadata=metadata, frames=frames)
    
    # Save to binary file
    output_file = f"diagnostic_{width}x{height}.bin"
    
    # Write as raw binary (design order)
    with open(output_file, 'wb') as f:
        # Write width and height as header (2 bytes each, little-endian)
        f.write(width.to_bytes(2, 'little'))
        f.write(height.to_bytes(2, 'little'))
        
        # Write frame count (2 bytes)
        f.write(len(frames).to_bytes(2, 'little'))
        
        # Write each frame
        for frame in frames:
            # Frame delay (2 bytes)
            f.write(frame.duration_ms.to_bytes(2, 'little'))
            
            # Pixel data (3 bytes per LED: R, G, B)
            for pixel in frame.pixels:
                r, g, b = pixel
                f.write(bytes([r, g, b]))
    
    print("="*80)
    print(f"DIAGNOSTIC PATTERN CREATED: {output_file}")
    print("="*80)
    print(f"Matrix: {width}×{height} = {total_leds} LEDs")
    print(f"Format: Design order (Row-major, Left Top)")
    print(f"")
    print("Corner Markers:")
    print(f"  Top-Left (0,0):        RED    LED {0}")
    print(f"  Top-Right ({width-1},0):      GREEN  LED {width-1}")
    print(f"  Bottom-Left (0,{height-1}):   BLUE   LED {total_leds - width}")
    print(f"  Bottom-Right ({width-1},{height-1}): YELLOW LED {total_leds - 1}")
    print(f"")
    print("Other Markers:")
    print(f"  First LED of rows 1-{height-2}:   MAGENTA")
    print(f"  Top row (except corners): CYAN")
    print(f"  Last LED of rows 1-{height-2}:    WHITE")
    print(f"  Center ({mid_x},{mid_y}):           ORANGE")
    print(f"")
    print("How to use:")
    print("1. Load this file in the app")
    print("2. Set File Format: Row-major, File Data-In: Left Top")
    print("3. Preview should show:")
    print("   - Red at top-left")
    print("   - Green at top-right") 
    print("   - Blue at bottom-left")
    print("   - Yellow at bottom-right")
    print("4. Try different Target Wiring modes in Flash tab")
    print("5. Use corner colors to verify hardware matches preview")
    print("="*80)
    
    return output_file

if __name__ == "__main__":
    filename = create_diagnostic_pattern(12, 6)
    print(f"\n✓ Created: {filename}")
    print(f"✓ File size: {os.path.getsize(filename)} bytes")

