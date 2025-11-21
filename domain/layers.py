"""
Layer Manager - Multi-layer support for LED matrix patterns.

This module provides layer management functionality, allowing multiple
layers per frame with visibility, opacity, and ordering controls.
"""

from __future__ import annotations
from typing import Optional, Tuple, List, Dict
from copy import deepcopy
from PySide6.QtCore import QObject, Signal
from core.pattern import Frame, Pattern
from domain.pattern_state import PatternState

Color = Tuple[int, int, int]


class Layer:
    """Represents a single layer in a frame."""
    
    def __init__(
        self,
        name: str = "Layer",
        pixels: Optional[List[Color]] = None,
        visible: bool = True,
        opacity: float = 1.0,
        blend_mode: str = "normal"
    ):
        self.name = name
        self.pixels = pixels or []
        self.visible = visible
        self.opacity = max(0.0, min(1.0, opacity))  # Clamp 0-1
        self.blend_mode = blend_mode  # "normal", "add", "multiply", "screen"
    
    def copy(self) -> Layer:
        """Create a deep copy of this layer."""
        return Layer(
            name=self.name,
            pixels=deepcopy(self.pixels),
            visible=self.visible,
            opacity=self.opacity
        )


class LayerManager(QObject):
    """
    Multi-layer manager for LED matrix patterns.
    
    Each frame can have multiple layers that can be:
    - Shown/hidden independently
    - Adjusted for opacity
    - Reordered
    - Composed together for display
    """

    pixel_changed = Signal(int, int, int, tuple)  # frame_index, x, y, colour
    frame_pixels_changed = Signal(int)
    layers_changed = Signal(int)  # frame_index
    layer_added = Signal(int, int)  # frame_index, layer_index
    layer_removed = Signal(int, int)  # frame_index, layer_index
    layer_moved = Signal(int, int, int)  # frame_index, from_index, to_index

    def __init__(self, state: PatternState):
        super().__init__()
        self._state = state
        # Store layers per frame: {frame_index: [Layer, ...]}
        self._layers: Dict[int, List[Layer]] = {}

    def set_pattern(self, pattern: Pattern) -> None:
        """Initialize layers for all frames."""
        self._state.set_pattern(pattern)
        self._layers = {}
        
        # Create default layer for each frame
        if pattern and pattern.frames:
            for idx, frame in enumerate(pattern.frames):
                layer = Layer(name="Layer 1", pixels=list(frame.pixels))
                self._layers[idx] = [layer]

    def get_layers(self, frame_index: int) -> List[Layer]:
        """Get all layers for a frame."""
        if frame_index not in self._layers:
            # Initialize if missing
            if self._state.pattern() and frame_index < len(self._state.pattern().frames):
                frame = self._state.pattern().frames[frame_index]
                layer = Layer(name="Layer 1", pixels=list(frame.pixels))
                self._layers[frame_index] = [layer]
            else:
                self._layers[frame_index] = []
        return self._layers[frame_index]

    def add_layer(self, frame_index: int, name: Optional[str] = None, insert_at: Optional[int] = None) -> int:
        """Add a new layer to a frame."""
        layers = self.get_layers(frame_index)
        width = self._state.width()
        height = self._state.height()
        blank_pixels = [(0, 0, 0)] * (width * height)
        
        layer_name = name or f"Layer {len(layers) + 1}"
        new_layer = Layer(name=layer_name, pixels=blank_pixels)
        
        if insert_at is None:
            layers.append(new_layer)
            layer_index = len(layers) - 1
        else:
            layers.insert(insert_at, new_layer)
            layer_index = insert_at
        
        self.layer_added.emit(frame_index, layer_index)
        self.layers_changed.emit(frame_index)
        return layer_index

    def remove_layer(self, frame_index: int, layer_index: int) -> bool:
        """Remove a layer from a frame."""
        layers = self.get_layers(frame_index)
        if len(layers) <= 1:
            return False  # Can't remove last layer
        
        if 0 <= layer_index < len(layers):
            del layers[layer_index]
            self.layer_removed.emit(frame_index, layer_index)
            self.layers_changed.emit(frame_index)
            return True
        return False

    def move_layer(self, frame_index: int, from_index: int, to_index: int) -> bool:
        """Move a layer to a new position."""
        layers = self.get_layers(frame_index)
        if 0 <= from_index < len(layers) and 0 <= to_index < len(layers):
            layer = layers.pop(from_index)
            layers.insert(to_index, layer)
            self.layer_moved.emit(frame_index, from_index, to_index)
            self.layers_changed.emit(frame_index)
            return True
        return False

    def set_layer_visible(self, frame_index: int, layer_index: int, visible: bool) -> None:
        """Set layer visibility."""
        layers = self.get_layers(frame_index)
        if 0 <= layer_index < len(layers):
            layers[layer_index].visible = visible
            self.layers_changed.emit(frame_index)

    def set_layer_opacity(self, frame_index: int, layer_index: int, opacity: float) -> None:
        """Set layer opacity (0.0 to 1.0)."""
        layers = self.get_layers(frame_index)
        if 0 <= layer_index < len(layers):
            layers[layer_index].opacity = max(0.0, min(1.0, opacity))
            self.layers_changed.emit(frame_index)

    def set_layer_name(self, frame_index: int, layer_index: int, name: str) -> None:
        """Set layer name."""
        layers = self.get_layers(frame_index)
        if 0 <= layer_index < len(layers):
            layers[layer_index].name = name
            self.layers_changed.emit(frame_index)

    def get_composite_pixels(self, frame_index: int) -> List[Color]:
        """Get composite pixels from all visible layers using blend modes."""
        try:
            from domain.layer_blending.blending import BlendMode, blend_pixels
        except ImportError:
            # Fallback to simple alpha blend if blending module not available
            return self._get_composite_pixels_simple(frame_index)
        
        layers = self.get_layers(frame_index)
        width = self._state.width()
        height = self._state.height()
        expected = width * height
        
        # Start with black background
        composite = [(0, 0, 0)] * expected
        
        # Blend visible layers from bottom to top
        for layer in layers:
            if not layer.visible:
                continue
            
            layer_pixels = layer.pixels[:expected]
            if len(layer_pixels) < expected:
                layer_pixels += [(0, 0, 0)] * (expected - len(layer_pixels))
            
            # Convert blend_mode string to enum
            blend_mode_map = {
                "normal": BlendMode.NORMAL,
                "add": BlendMode.ADD,
                "multiply": BlendMode.MULTIPLY,
                "screen": BlendMode.SCREEN,
            }
            blend_mode = blend_mode_map.get(layer.blend_mode, BlendMode.NORMAL)
            
            # Blend each pixel using blend mode
            for i in range(expected):
                composite[i] = blend_pixels(
                    bottom=composite[i],
                    top=layer_pixels[i],
                    opacity=layer.opacity,
                    blend_mode=blend_mode
                )
        
        return composite
    
    def _get_composite_pixels_simple(self, frame_index: int) -> List[Color]:
        """Simple alpha blend fallback"""
        layers = self.get_layers(frame_index)
        width = self._state.width()
        height = self._state.height()
        expected = width * height
        
        composite = [(0, 0, 0)] * expected
        
        for layer in layers:
            if not layer.visible:
                continue
            
            layer_pixels = layer.pixels[:expected]
            if len(layer_pixels) < expected:
                layer_pixels += [(0, 0, 0)] * (expected - len(layer_pixels))
            
            opacity = layer.opacity
            for i in range(expected):
                r1, g1, b1 = composite[i]
                r2, g2, b2 = layer_pixels[i]
                r = int(r1 * (1 - opacity) + r2 * opacity)
                g = int(g1 * (1 - opacity) + g2 * opacity)
                b = int(b1 * (1 - opacity) + b2 * opacity)
                composite[i] = (r, g, b)
        
        return composite

    def apply_pixel(self, frame_index: int, x: int, y: int, colour: Optional[Color], width: int, height: int, layer_index: int = 0) -> None:
        """Apply pixel change to a specific layer."""
        layers = self.get_layers(frame_index)
        if 0 <= layer_index < len(layers):
            layer = layers[layer_index]
            idx = y * width + x
            if idx < len(layer.pixels):
                layer.pixels[idx] = colour or (0, 0, 0)
                # Sync frame from layers after pixel change
                self.sync_frame_from_layers(frame_index)
                self.pixel_changed.emit(frame_index, x, y, colour or (0, 0, 0))
                self.layers_changed.emit(frame_index)

    def replace_pixels(self, frame_index: int, pixels, layer_index: int = 0) -> None:
        """Replace pixels in a specific layer."""
        layers = self.get_layers(frame_index)
        if 0 <= layer_index < len(layers):
            layers[layer_index].pixels = list(pixels)
            self.frame_pixels_changed.emit(frame_index)
            self.layers_changed.emit(frame_index)

    def resize_pixels(self, width: int, height: int) -> None:
        """Resize all layers to new dimensions."""
        # Update pattern metadata first so get_composite_pixels uses correct dimensions
        if self._state.pattern():
            self._state.pattern().metadata.width = width
            self._state.pattern().metadata.height = height
        
        expected = width * height
        for frame_idx in self._layers:
            for layer in self._layers[frame_idx]:
                pixels = layer.pixels[:expected]
                if len(pixels) < expected:
                    pixels += [(0, 0, 0)] * (expected - len(pixels))
                layer.pixels = pixels
            # Sync frame from layers after resizing
            self.sync_frame_from_layers(frame_idx)
        self.frame_pixels_changed.emit(-1)

    def sync_frame_from_layers(self, frame_index: int) -> None:
        """Update frame pixels from composite of all layers."""
        if not self._state.pattern() or frame_index >= len(self._state.pattern().frames):
            return
        
        composite = self.get_composite_pixels(frame_index)
        self._state.pattern().frames[frame_index].pixels = composite

    def sync_all_frames_from_layers(self) -> None:
        """Update all frames from their layer composites."""
        if not self._state.pattern():
            return
        
        for idx in range(len(self._state.pattern().frames)):
            self.sync_frame_from_layers(idx)
