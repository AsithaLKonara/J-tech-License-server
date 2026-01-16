"""
Layer Blending Modes - Deterministic pixel blending implementations

Provides documented blend mode formulas for layer compositing.
"""

from enum import Enum
from typing import Tuple, List


RGB = Tuple[int, int, int]


class BlendMode(Enum):
    """Layer blend modes"""
    NORMAL = "normal"
    ADD = "add"
    MULTIPLY = "multiply"
    SCREEN = "screen"


def blend_pixels(
    bottom: RGB,
    top: RGB,
    opacity: float,
    blend_mode: BlendMode = BlendMode.NORMAL
) -> RGB:
    """
    Blend two pixels using specified blend mode.
    
    Formulas:
    - NORMAL: result = top * opacity + bottom * (1 - opacity)
    - ADD: result = bottom + top * opacity (clamped to 0-255)
    - MULTIPLY: result = (bottom * top) / 255 * opacity + bottom * (1 - opacity)
    - SCREEN: result = 255 - ((255 - bottom) * (255 - top)) / 255 * opacity + bottom * (1 - opacity)
    
    Args:
        bottom: Bottom pixel (R, G, B)
        top: Top pixel (R, G, B)
        opacity: Top pixel opacity (0.0-1.0)
        blend_mode: Blend mode to use
        
    Returns:
        Blended pixel (R, G, B)
    """
    r1, g1, b1 = bottom
    r2, g2, b2 = top
    
    if blend_mode == BlendMode.NORMAL:
        # Normal blend: alpha compositing
        r = int(r1 * (1 - opacity) + r2 * opacity)
        g = int(g1 * (1 - opacity) + g2 * opacity)
        b = int(b1 * (1 - opacity) + b2 * opacity)
    
    elif blend_mode == BlendMode.ADD:
        # Additive blend: add colors
        r = min(255, int(r1 + r2 * opacity))
        g = min(255, int(g1 + g2 * opacity))
        b = min(255, int(b1 + b2 * opacity))
    
    elif blend_mode == BlendMode.MULTIPLY:
        # Multiply blend: multiply then blend
        mult_r = (r1 * r2) // 255
        mult_g = (g1 * g2) // 255
        mult_b = (b1 * b2) // 255
        r = int(r1 * (1 - opacity) + mult_r * opacity)
        g = int(g1 * (1 - opacity) + mult_g * opacity)
        b = int(b1 * (1 - opacity) + mult_b * opacity)
    
    elif blend_mode == BlendMode.SCREEN:
        # Screen blend: inverse multiply
        screen_r = 255 - ((255 - r1) * (255 - r2)) // 255
        screen_g = 255 - ((255 - g1) * (255 - g2)) // 255
        screen_b = 255 - ((255 - b1) * (255 - b2)) // 255
        r = int(r1 * (1 - opacity) + screen_r * opacity)
        g = int(g1 * (1 - opacity) + screen_g * opacity)
        b = int(b1 * (1 - opacity) + screen_b * opacity)
    
    else:
        # Default to normal
        r = int(r1 * (1 - opacity) + r2 * opacity)
        g = int(g1 * (1 - opacity) + g2 * opacity)
        b = int(b1 * (1 - opacity) + b2 * opacity)
    
    # Clamp to valid range
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    
    return (r, g, b)


def composite_layers(
    layers: List[Tuple[List[RGB], float, BlendMode, bool]],
    pixel_count: int
) -> List[RGB]:
    """
    Composite multiple layers into single pixel array.
    
    Layers are composited from bottom to top.
    Only visible layers are composited.
    
    Args:
        layers: List of (pixels, opacity, blend_mode, visible) tuples
        pixel_count: Expected number of pixels
        
    Returns:
        Composited pixel array
    """
    # Start with black background
    composite = [(0, 0, 0)] * pixel_count
    
    # Composite layers from bottom to top
    for layer_pixels, opacity, blend_mode, visible in layers:
        if not visible:
            continue
        
        # Ensure layer has correct pixel count
        pixels = layer_pixels[:pixel_count]
        if len(pixels) < pixel_count:
            pixels += [(0, 0, 0)] * (pixel_count - len(pixels))
        
        # Blend each pixel
        for i in range(pixel_count):
            composite[i] = blend_pixels(
                bottom=composite[i],
                top=pixels[i],
                opacity=opacity,
                blend_mode=blend_mode
            )
    
    return composite

