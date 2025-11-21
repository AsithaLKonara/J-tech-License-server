"""
Export Options - Configuration for advanced pattern export options.

This module defines export options for bit ordering, scanning direction,
color formats, and other hardware-specific configurations.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple

RGB = Tuple[int, int, int]


@dataclass
class ExportOptions:
    """Configuration options for pattern export."""
    
    # Bit ordering
    bit_order_msb_lsb: str = "MSB"  # "MSB" or "LSB"
    bit_order_position: str = "Top"  # "Top" or "Bottom"
    
    # Scanning direction
    scan_direction: str = "Rows"  # "Rows" or "Columns"
    scan_order: str = "LeftToRight"  # "LeftToRight", "RightToLeft", "TopToBottom", "BottomToTop", "Alternate"
    
    # Serpentine wiring (reverse every 2nd row/column)
    serpentine: bool = False
    
    # RGB color ordering
    rgb_order: str = "RGB"  # "RGB", "BGR", "GRB"
    
    # Color space
    color_space: str = "RGB888"  # "RGB888" or "RGB565"
    # Bit depth trimming per channel (R, G, B). Values 1-8, defaults to full 8-bit.
    bits_per_channel: Tuple[int, int, int] = (8, 8, 8)
    
    # Bytes per line grouping
    bytes_per_line: int = 0  # 0 = no grouping, >0 = group bytes
    
    # Number format
    number_format: str = "Hex"  # "Hex", "Decimal", "Binary"
    
    def reorder_pixels(self, pixels: List[RGB], width: int, height: int) -> List[RGB]:
        """
        Reorder pixels according to scanning direction and serpentine wiring.
        
        Args:
            pixels: Input pixels in row-major order
            width: Matrix width
            height: Matrix height
        
        Returns:
            Reordered pixel list
        """
        # Convert to 2D grid
        grid = [[pixels[y * width + x] for x in range(width)] for y in range(height)]
        
        # Apply serpentine if enabled
        if self.serpentine:
            if self.scan_direction == "Rows":
                # Reverse every 2nd row
                for y in range(1, height, 2):
                    grid[y] = grid[y][::-1]
            else:  # Columns
                # Reverse every 2nd column
                for y in range(height):
                    for x in range(1, width, 2):
                        grid[y][x], grid[y][width - 1 - x] = grid[y][width - 1 - x], grid[y][x]
        
        # Apply scanning order
        result: List[RGB] = []
        
        if self.scan_direction == "Rows":
            if self.scan_order == "RightToLeft":
                for row in grid:
                    result.extend(row[::-1])
            elif self.scan_order == "BottomToTop":
                for row in reversed(grid):
                    result.extend(row)
            elif self.scan_order == "TopToBottom":
                for row in grid:
                    result.extend(row)
            elif self.scan_order == "Alternate":
                # Alternate row direction
                for y, row in enumerate(grid):
                    if y % 2 == 0:
                        result.extend(row)
                    else:
                        result.extend(row[::-1])
            else:  # LeftToRight (default)
                for row in grid:
                    result.extend(row)
        else:  # Columns
            if self.scan_order == "TopToBottom":
                for x in range(width):
                    for y in range(height):
                        result.append(grid[y][x])
            elif self.scan_order == "BottomToTop":
                for x in range(width):
                    for y in range(height - 1, -1, -1):
                        result.append(grid[y][x])
            elif self.scan_order == "RightToLeft":
                for x in range(width - 1, -1, -1):
                    for y in range(height):
                        result.append(grid[y][x])
            elif self.scan_order == "Alternate":
                # Alternate column direction
                for x in range(width):
                    if x % 2 == 0:
                        for y in range(height):
                            result.append(grid[y][x])
                    else:
                        for y in range(height - 1, -1, -1):
                            result.append(grid[y][x])
            else:  # LeftToRight (default)
                for x in range(width):
                    for y in range(height):
                        result.append(grid[y][x])
        
        return result
    
    def reorder_color_channels(self, pixel: RGB) -> Tuple[int, int, int]:
        """
        Reorder RGB channels according to rgb_order setting.
        
        Args:
            pixel: RGB tuple
        
        Returns:
            Reordered RGB tuple
        """
        r, g, b = pixel
        
        if self.rgb_order == "BGR":
            return (b, g, r)
        elif self.rgb_order == "GRB":
            return (g, r, b)
        else:  # RGB
            return (r, g, b)

    def trim_to_bit_depth(self, pixel: RGB) -> RGB:
        """
        Reduce channel bit depth according to bits_per_channel setting.
        Values are scaled between 0-255 and optionally aligned to top/bottom bits.
        """
        trimmed: List[int] = []
        for value, bits in zip(pixel, self.bits_per_channel):
            bits = int(bits)
            if bits >= 8:
                trimmed.append(int(value) & 0xFF)
                continue
            if bits <= 0:
                trimmed.append(0)
                continue
            max_val = (1 << bits) - 1
            scaled = int(round((int(value) / 255.0) * max_val))
            if self.bit_order_position == "Top":
                trimmed.append((scaled << (8 - bits)) & 0xFF)
            else:
                trimmed.append(scaled & 0xFF)
        return tuple(trimmed)  # type: ignore[return-value]
    
    def convert_color_space(self, pixel: RGB) -> Tuple[int, ...]:
        """
        Convert pixel to target color space.
        
        Args:
            pixel: RGB888 tuple
        
        Returns:
            Color in target format (RGB888 tuple or RGB565 int)
        """
        r, g, b = pixel
        
        if self.color_space == "RGB565":
            # Convert to RGB565: 5 bits red, 6 bits green, 5 bits blue
            r5 = (r >> 3) & 0x1F
            g6 = (g >> 2) & 0x3F
            b5 = (b >> 3) & 0x1F
            rgb565 = (r5 << 11) | (g6 << 5) | b5
            return (rgb565,)  # Return as single value tuple
        else:  # RGB888
            return pixel
    
    def format_number(self, value: int, byte_count: int = 1) -> str:
        """
        Format number according to number_format setting.
        
        Args:
            value: Number to format
            byte_count: Number of bytes (for hex formatting)
        
        Returns:
            Formatted string
        """
        if self.number_format == "Binary":
            return bin(value)[2:].zfill(byte_count * 8)
        elif self.number_format == "Decimal":
            return str(value)
        else:  # Hex
            if byte_count == 1:
                return f"0x{value:02X}"
            elif byte_count == 2:
                return f"0x{value:04X}"
            else:
                return f"0x{value:02X}"

