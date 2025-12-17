"""
Layer Manager - Multi-layer support for LED matrix patterns.

This module provides layer management functionality, allowing multiple
layers per frame with visibility, opacity, and ordering controls.

NEW ARCHITECTURE (Layer Tracks):
- Layers span across frames (like video editing software)
- Each LayerTrack contains frame data (LayerFrame objects)
- Layers can animate independently
- Better organization and efficiency
"""

from __future__ import annotations
from typing import Optional, Tuple, List, Dict
from copy import deepcopy
from PySide6.QtCore import QObject, Signal
from core.pattern import Frame, Pattern
from domain.pattern_state import PatternState

Color = Tuple[int, int, int]

# Import migration functions
try:
    from core.migration.layer_migration import auto_migrate_on_load, detect_old_layer_structure
except ImportError:
    # Migration module not available - define stubs
    def auto_migrate_on_load(layer_manager) -> bool:
        return False
    
    def detect_old_layer_structure(layer_manager) -> bool:
        return False


class LayerFrame:
    """
    Represents frame data within a layer track.
    
    Each frame in a layer track can have:
    - Independent pixel data (stored per frame)
    - Override visibility (None = use layer default)
    - Override opacity (None = use layer default)
    - Per-pixel mask
    
    Pixel Storage Model:
    - Each LayerFrame stores its own pixel array
    - Pixels are stored per frame (not shared across frames)
    - Animations transform pixels at render time without modifying stored pixels
    - This allows the same base pixels to be transformed differently per frame
    """
    
    def __init__(
        self,
        pixels: Optional[List[Color]] = None,
        visible: Optional[bool] = None,  # None = use layer default
        opacity: Optional[float] = None,  # None = use layer default
        mask: Optional[List[float]] = None,  # Mask values 0.0-1.0 per pixel
    ):
        self.pixels = pixels or []
        self.visible = visible  # None means inherit from layer
        self.opacity = opacity  # None means inherit from layer (clamped if set)
        if self.opacity is not None:
            self.opacity = max(0.0, min(1.0, self.opacity))
        self.mask = mask  # Per-pixel mask (0.0 = transparent, 1.0 = opaque)
    
    def copy(self) -> 'LayerFrame':
        """Create a deep copy of this layer frame."""
        return LayerFrame(
            pixels=deepcopy(self.pixels),
            visible=self.visible,
            opacity=self.opacity,
            mask=deepcopy(self.mask) if self.mask else None,
        )
    
    def apply_mask(self, width: int, height: int) -> List[Color]:
        """Apply mask to layer frame pixels."""
        if not self.mask:
            return self.pixels
        
        expected = width * height
        masked_pixels = []
        mask_values = self.mask[:expected]
        if len(mask_values) < expected:
            mask_values += [1.0] * (expected - len(mask_values))
        
        pixels = self.pixels[:expected]
        if len(pixels) < expected:
            pixels += [(0, 0, 0)] * (expected - len(pixels))
        
        for i, (pixel, mask_value) in enumerate(zip(pixels, mask_values)):
            r, g, b = pixel
            masked_r = int(r * mask_value)
            masked_g = int(g * mask_value)
            masked_b = int(b * mask_value)
            masked_pixels.append((masked_r, masked_g, masked_b))
        
        return masked_pixels


class LayerTrack:
    """
    Represents a layer that spans across multiple frames.
    
    This is the new architecture where layers are first-class entities
    that exist across the entire animation timeline, similar to video
    editing software (After Effects, Premiere Pro).
    
    Each LayerTrack contains:
    - Frame data (Dict[int, LayerFrame]) - one LayerFrame per frame
    - Global properties (visible, opacity, blend_mode) - can be overridden per-frame
    - Layer metadata (name, z_index, group_id, locked)
    """
    
    def __init__(
        self,
        name: str = "Layer",
        frames: Optional[Dict[int, LayerFrame]] = None,
        visible: bool = True,
        opacity: float = 1.0,
        blend_mode: str = "normal",
        group_id: Optional[str] = None,
        locked: bool = False,
        z_index: int = 0,  # Rendering order (lower = bottom, higher = top)
        start_frame: Optional[int] = None,  # Layer starts at this frame (None = frame 0)
        end_frame: Optional[int] = None,  # Layer ends at this frame, inclusive (None = end of pattern)
    ):
        self.name = name
        self.frames: Dict[int, LayerFrame] = frames or {}
        self.visible = visible  # Global visibility (can be overridden per-frame)
        self.opacity = max(0.0, min(1.0, opacity))  # Global opacity (can be overridden per-frame)
        self.blend_mode = blend_mode  # "normal", "add", "multiply", "screen"
        self.group_id = group_id  # ID of layer group this layer belongs to
        self.locked = locked  # Lock layer to prevent editing
        self.z_index = z_index  # Rendering order
        self.start_frame = start_frame  # Layer timing: start frame
        self.end_frame = end_frame  # Layer timing: end frame (inclusive)
    
    def get_frame(self, frame_index: int) -> Optional[LayerFrame]:
        """Get frame data for a specific frame index, returning None if frame is outside layer's range."""
        # Check if frame is outside layer's timing range
        if self.start_frame is not None and frame_index < self.start_frame:
            return None
        if self.end_frame is not None and frame_index > self.end_frame:
            return None
        return self.frames.get(frame_index)
    
    def set_frame(self, frame_index: int, layer_frame: LayerFrame) -> None:
        """Set frame data for a specific frame index."""
        self.frames[frame_index] = layer_frame
    
    def get_or_create_frame(self, frame_index: int, width: int, height: int) -> LayerFrame:
        """Get frame data, creating it if it doesn't exist."""
        if frame_index not in self.frames:
            blank_pixels = [(0, 0, 0)] * (width * height)
            self.frames[frame_index] = LayerFrame(pixels=blank_pixels)
        return self.frames[frame_index]
    
    def get_effective_visibility(self, frame_index: int) -> bool:
        """Get effective visibility for a frame (frame override or layer default)."""
        frame = self.get_frame(frame_index)
        if frame and frame.visible is not None:
            return frame.visible
        return self.visible
    
    def get_effective_opacity(self, frame_index: int) -> float:
        """Get effective opacity for a frame (frame override or layer default)."""
        frame = self.get_frame(frame_index)
        if frame and frame.opacity is not None:
            return max(0.0, min(1.0, frame.opacity))
        return self.opacity
    
    def copy(self) -> 'LayerTrack':
        """Create a deep copy of this layer track."""
        copied_frames = {
            idx: frame.copy() for idx, frame in self.frames.items()
        }
        return LayerTrack(
            name=self.name,
            frames=copied_frames,
            visible=self.visible,
            opacity=self.opacity,
            blend_mode=self.blend_mode,
            group_id=self.group_id,
            locked=self.locked,
            z_index=self.z_index,
            start_frame=self.start_frame,
            end_frame=self.end_frame,
        )


class Layer:
    """Represents a single layer in a frame."""
    
    def __init__(
        self,
        name: str = "Layer",
        pixels: Optional[List[Color]] = None,
        visible: bool = True,
        opacity: float = 1.0,
        blend_mode: str = "normal",
        group_id: Optional[str] = None,
        mask: Optional[List[float]] = None,  # Mask values 0.0-1.0 per pixel
        locked: bool = False  # Lock layer to prevent editing
    ):
        self.name = name
        self.pixels = pixels or []
        self.visible = visible
        self.opacity = max(0.0, min(1.0, opacity))  # Clamp 0-1
        self.blend_mode = blend_mode  # "normal", "add", "multiply", "screen"
        self.group_id = group_id  # ID of layer group this layer belongs to
        self.mask = mask  # Per-pixel mask (0.0 = transparent, 1.0 = opaque)
        self.locked = locked  # Lock layer to prevent editing
    
    def copy(self) -> Layer:
        """Create a deep copy of this layer."""
        return Layer(
            name=self.name,
            pixels=deepcopy(self.pixels),
            visible=self.visible,
            opacity=self.opacity,
            blend_mode=self.blend_mode,
            group_id=self.group_id,
            mask=deepcopy(self.mask) if self.mask else None,
            locked=self.locked
        )
    
    def apply_mask(self, width: int, height: int) -> List[Color]:
        """Apply mask to layer pixels."""
        if not self.mask:
            return self.pixels
        
        expected = width * height
        masked_pixels = []
        mask_values = self.mask[:expected]
        if len(mask_values) < expected:
            mask_values += [1.0] * (expected - len(mask_values))
        
        pixels = self.pixels[:expected]
        if len(pixels) < expected:
            pixels += [(0, 0, 0)] * (expected - len(pixels))
        
        for i, (pixel, mask_value) in enumerate(zip(pixels, mask_values)):
            r, g, b = pixel
            masked_r = int(r * mask_value)
            masked_g = int(g * mask_value)
            masked_b = int(b * mask_value)
            masked_pixels.append((masked_r, masked_g, masked_b))
        
        return masked_pixels


class LayerGroup:
    """Represents a group of layers."""
    
    def __init__(self, group_id: str, name: str = "Group", visible: bool = True, opacity: float = 1.0):
        self.group_id = group_id
        self.name = name
        self.visible = visible
        self.opacity = max(0.0, min(1.0, opacity))  # Clamp 0-1


class LayerManager(QObject):
    """
    Multi-layer manager for LED matrix patterns.
    
    NEW ARCHITECTURE: Layer tracks span across frames (like video editing software).
    Each layer track can have:
    - Independent animations across frames
    - Per-frame property overrides (visibility, opacity)
    - Global properties (visible, opacity, blend_mode)
    - Z-order (rendering order)
    - Grouping support
    - Per-pixel masks
    
    BACKWARD COMPATIBILITY: Still supports old per-frame layer structure
    through migration layer.
    """

    pixel_changed = Signal(int, int, int, tuple)  # frame_index, x, y, colour
    frame_pixels_changed = Signal(int)
    layers_changed = Signal(int)  # frame_index (-1 = all frames)
    layer_added = Signal(int, int)  # frame_index, layer_index (for compatibility)
    layer_track_added = Signal(int)  # layer_track_index (new signal)
    layer_removed = Signal(int, int)  # frame_index, layer_index (for compatibility)
    layer_track_removed = Signal(int)  # layer_track_index (new signal)
    layer_moved = Signal(int, int, int)  # frame_index, from_index, to_index (for compatibility)
    layer_track_moved = Signal(int, int)  # from_index, to_index (new signal)
    group_changed = Signal(int)  # frame_index (-1 = all frames)

    def __init__(self, state: PatternState):
        super().__init__()
        self._state = state
        # NEW: Store layer tracks (layers span across frames)
        self._layer_tracks: List[LayerTrack] = []
        # Store layer groups (span across frames too)
        self._groups: Dict[str, LayerGroup] = {}
        # Animation manager for layer animations
        from domain.layer_animation import LayerAnimationManager
        self._animation_manager = LayerAnimationManager()
        # OLD: Legacy per-frame storage (for backward compatibility)
        self._legacy_layers: Optional[Dict[int, List[Layer]]] = None
        self._legacy_groups: Optional[Dict[int, Dict[str, LayerGroup]]] = None
        self._use_legacy_mode = False

    def set_pattern(self, pattern: Pattern) -> None:
        """
        Initialize layers for all frames.
        
        Automatically migrates old per-frame layer structure if detected.
        """
        self._state.set_pattern(pattern)
        self._layer_tracks = []
        self._groups = {}
        self._legacy_layers = None
        self._legacy_groups = None
        self._use_legacy_mode = False
        
        # Try to auto-migrate if old structure exists
        migrated = auto_migrate_on_load(self)
        if migrated:
            # Migration successful, return early
            return
        
        # Create default layer track spanning all frames
        if pattern and pattern.frames:
            default_track = LayerTrack(name="Layer 1", z_index=0)
            width = pattern.metadata.width
            height = pattern.metadata.height
            expected_pixels = width * height
            
            for idx, frame in enumerate(pattern.frames):
                # Initialize frame data from existing frame pixels
                frame_pixels = list(frame.pixels)
                if len(frame_pixels) < expected_pixels:
                    frame_pixels += [(0, 0, 0)] * (expected_pixels - len(frame_pixels))
                elif len(frame_pixels) > expected_pixels:
                    frame_pixels = frame_pixels[:expected_pixels]
                
                layer_frame = LayerFrame(pixels=frame_pixels)
                default_track.set_frame(idx, layer_frame)
            
            self._layer_tracks.append(default_track)

    # NEW METHODS: Layer Track API
    
    def get_layer_tracks(self) -> List[LayerTrack]:
        """Get all layer tracks (new API)."""
        return list(self._layer_tracks)
    
    def get_layer_track(self, track_index: int) -> Optional[LayerTrack]:
        """Get a specific layer track by index."""
        if 0 <= track_index < len(self._layer_tracks):
            return self._layer_tracks[track_index]
        return None
    
    def get_animation_manager(self):
        """Get the animation manager for setting layer animations."""
        return self._animation_manager
    
    def set_layer_animation(self, track_index: int, animation) -> None:
        """Set animation for a layer track."""
        self._animation_manager.set_animation(track_index, animation)
        # Emit signal to update UI
        self.layers_changed.emit(-1)  # -1 = all frames
    
    def add_layer_track(self, name: Optional[str] = None, insert_at: Optional[int] = None) -> int:
        """Add a new layer track (new API)."""
        width = self._state.width()
        height = self._state.height()
        blank_pixels = [(0, 0, 0)] * (width * height)
        
        layer_name = name or f"Layer {len(self._layer_tracks) + 1}"
        new_track = LayerTrack(
            name=layer_name,
            z_index=len(self._layer_tracks)  # New layers go on top
        )
        
        # Initialize with blank frames for all existing frames
        if self._state.pattern():
            for idx in range(len(self._state.pattern().frames)):
                layer_frame = LayerFrame(pixels=list(blank_pixels))
                new_track.set_frame(idx, layer_frame)
        
        if insert_at is None:
            self._layer_tracks.append(new_track)
            track_index = len(self._layer_tracks) - 1
        else:
            self._layer_tracks.insert(insert_at, new_track)
            track_index = insert_at
            # Update z_index for all tracks
            for i, track in enumerate(self._layer_tracks):
                track.z_index = i
        
        self.layer_track_added.emit(track_index)
        self.layers_changed.emit(-1)  # -1 = all frames changed
        return track_index
    
    def remove_layer_track(self, track_index: int) -> bool:
        """Remove a layer track (new API)."""
        if len(self._layer_tracks) <= 1:
            return False  # Can't remove last layer
        
        if 0 <= track_index < len(self._layer_tracks):
            del self._layer_tracks[track_index]
            # Update z_index for remaining tracks
            for i, track in enumerate(self._layer_tracks):
                track.z_index = i
            self.layer_track_removed.emit(track_index)
            self.layers_changed.emit(-1)  # -1 = all frames changed
            return True
        return False
    
    def move_layer_track(self, from_index: int, to_index: int) -> bool:
        """Move a layer track to a new position (new API)."""
        if 0 <= from_index < len(self._layer_tracks) and 0 <= to_index < len(self._layer_tracks):
            track = self._layer_tracks.pop(from_index)
            self._layer_tracks.insert(to_index, track)
            # Update z_index for all tracks
            for i, track in enumerate(self._layer_tracks):
                track.z_index = i
            self.layer_track_moved.emit(from_index, to_index)
            self.layers_changed.emit(-1)  # -1 = all frames changed
            return True
        return False
    
    # BACKWARD COMPATIBILITY METHODS: Per-frame layer API
    
    def get_layers(self, frame_index: int) -> List[Layer]:
        """
        Get all layers for a frame (backward compatibility).
        
        This converts LayerTracks to per-frame Layers for compatibility.
        """
        # Convert layer tracks to per-frame layers
        layers = []
        for track in self._layer_tracks:
            layer_frame = track.get_frame(frame_index)
            if layer_frame:
                # Convert LayerTrack + LayerFrame to Layer
                layer = Layer(
                    name=track.name,
                    pixels=list(layer_frame.pixels),
                    visible=track.get_effective_visibility(frame_index),
                    opacity=track.get_effective_opacity(frame_index),
                    blend_mode=track.blend_mode,
                    group_id=track.group_id,
                    mask=layer_frame.mask,
                    locked=track.locked
                )
                layers.append(layer)
            else:
                # Frame doesn't exist in track, create blank layer
                width = self._state.width()
                height = self._state.height()
                blank_pixels = [(0, 0, 0)] * (width * height)
                layer = Layer(
                    name=track.name,
                    pixels=blank_pixels,
                    visible=track.visible,
                    opacity=track.opacity,
                    blend_mode=track.blend_mode,
                    group_id=track.group_id,
                    locked=track.locked
                )
                layers.append(layer)
        
        return layers

    def add_layer(self, frame_index: int, name: Optional[str] = None, insert_at: Optional[int] = None) -> int:
        """
        Add a new layer to a frame (backward compatibility).
        
        This creates a new LayerTrack and initializes it for all frames.
        """
        # Create new layer track
        track_index = self.add_layer_track(name, insert_at)
        
        # Emit backward compatibility signal
        self.layer_added.emit(frame_index, track_index)
        return track_index

    def remove_layer(self, frame_index: int, layer_index: int) -> bool:
        """
        Remove a layer from a frame (backward compatibility).
        
        This removes the entire LayerTrack (since layers span frames).
        """
        # Remove layer track (layers span frames, so removing from one frame removes entirely)
        result = self.remove_layer_track(layer_index)
        if result:
            # Emit backward compatibility signal
            self.layer_removed.emit(frame_index, layer_index)
        return result

    def move_layer(self, frame_index: int, from_index: int, to_index: int) -> bool:
        """
        Move a layer to a new position (backward compatibility).
        
        This moves the LayerTrack (since layers span frames).
        """
        result = self.move_layer_track(from_index, to_index)
        if result:
            # Emit backward compatibility signal
            self.layer_moved.emit(frame_index, from_index, to_index)
        return result

    def set_layer_visible(self, frame_index: int, layer_index: int, visible: bool) -> None:
        """
        Set layer visibility (backward compatibility).
        
        This sets frame-specific visibility override if different from global,
        otherwise sets global visibility.
        """
        if 0 <= layer_index < len(self._layer_tracks):
            track = self._layer_tracks[layer_index]
            # If setting to global value, remove override
            if visible == track.visible:
                layer_frame = track.get_frame(frame_index)
                if layer_frame:
                    layer_frame.visible = None  # Use global
            else:
                # Set frame-specific override
                layer_frame = track.get_or_create_frame(
                    frame_index, self._state.width(), self._state.height()
                )
                layer_frame.visible = visible
            self.layers_changed.emit(frame_index)
    
    def set_layer_track_visible(self, layer_index: int, visible: bool) -> None:
        """
        Set global visibility for a layer track (affects all frames unless overridden).
        
        This is the new API for setting global layer properties.
        """
        if 0 <= layer_index < len(self._layer_tracks):
            self._layer_tracks[layer_index].visible = visible
            self.layers_changed.emit(-1)  # -1 = all frames
    
    def set_layer_track_opacity(self, layer_index: int, opacity: float) -> None:
        """
        Set global opacity for a layer track (affects all frames unless overridden).
        
        This is the new API for setting global layer properties.
        """
        opacity = max(0.0, min(1.0, opacity))
        if 0 <= layer_index < len(self._layer_tracks):
            self._layer_tracks[layer_index].opacity = opacity
            self.layers_changed.emit(-1)  # -1 = all frames

    def set_layer_opacity(self, frame_index: int, layer_index: int, opacity: float) -> None:
        """
        Set layer opacity (0.0 to 1.0) (backward compatibility).
        
        This sets frame-specific opacity override if different from global,
        otherwise sets global opacity.
        """
        opacity = max(0.0, min(1.0, opacity))
        if 0 <= layer_index < len(self._layer_tracks):
            track = self._layer_tracks[layer_index]
            # If setting to global value, remove override
            if abs(opacity - track.opacity) < 0.001:  # Float comparison
                layer_frame = track.get_frame(frame_index)
                if layer_frame:
                    layer_frame.opacity = None  # Use global
            else:
                # Set frame-specific override
                layer_frame = track.get_or_create_frame(
                    frame_index, self._state.width(), self._state.height()
                )
                layer_frame.opacity = opacity
            self.layers_changed.emit(frame_index)
    
    def set_layer_locked(self, frame_index: int, layer_index: int, locked: bool) -> None:
        """Set layer lock state (backward compatibility)."""
        if 0 <= layer_index < len(self._layer_tracks):
            self._layer_tracks[layer_index].locked = locked
            self.layers_changed.emit(-1)  # Lock affects all frames
    
    def is_layer_locked(self, frame_index: int, layer_index: int) -> bool:
        """Check if layer is locked (backward compatibility)."""
        if 0 <= layer_index < len(self._layer_tracks):
            return self._layer_tracks[layer_index].locked
        return False

    def set_layer_name(self, frame_index: int, layer_index: int, name: str) -> None:
        """Set layer name (backward compatibility)."""
        if 0 <= layer_index < len(self._layer_tracks):
            self._layer_tracks[layer_index].name = name
            self.layers_changed.emit(-1)  # Name affects all frames

    def get_composite_pixels(self, frame_index: int) -> List[Color]:
        """
        Get composite pixels from all visible layer tracks using blend modes, groups, and masks.
        
        Render flow for each layer:
        1. Check layer visibility (skip if invisible)
        2. Get base pixels from LayerFrame
        3. Apply animation transformations (non-destructive)
        4. Apply mask if present
        5. Blend with composite using opacity and blend mode
        
        This composites all LayerTracks for the specified frame, respecting:
        - Layer visibility (global and per-frame overrides) - checked first
        - Layer opacity (global and per-frame overrides)
        - Blend modes
        - Layer groups
        - Per-pixel masks
        - Z-order (rendering order)
        - Layer animations (applied per-frame at render time)
        """
        try:
            from domain.layer_blending.blending import BlendMode, blend_pixels
        except ImportError:
            # Fallback to simple alpha blend if blending module not available
            return self._get_composite_pixels_simple(frame_index)
        
        width = self._state.width()
        height = self._state.height()
        expected = width * height
        
        # Start with black background
        composite = [(0, 0, 0)] * expected
        
        # Sort layer tracks by z_index (lower = bottom, higher = top)
        sorted_tracks = sorted(self._layer_tracks, key=lambda t: t.z_index)
        
        # Blend visible layers from bottom to top
        for track in sorted_tracks:
            # Check layer timing (skip if frame is outside layer's range)
            if track.start_frame is not None and frame_index < track.start_frame:
                continue
            if track.end_frame is not None and frame_index > track.end_frame:
                continue
            
            # Check layer visibility (global or per-frame override)
            if not track.get_effective_visibility(frame_index):
                continue
            
            # Check group visibility
            if track.group_id and track.group_id in self._groups:
                group = self._groups[track.group_id]
                if not group.visible:
                    continue
            
            # Get frame data for this layer track
            layer_frame = track.get_frame(frame_index)
            if not layer_frame:
                # Frame doesn't exist in track, skip
                continue
            
            layer_pixels = list(layer_frame.pixels[:expected])
            if len(layer_pixels) < expected:
                layer_pixels += [(0, 0, 0)] * (expected - len(layer_pixels))
            
            # Apply layer animation transformations (scroll, rotate, etc.)
            track_index = sorted_tracks.index(track)
            layer_pixels = self._apply_layer_animation(
                track, track_index, frame_index, layer_pixels, width, height
            )
            
            # Apply mask if present
            if layer_frame.mask:
                layer_pixels = layer_frame.apply_mask(width, height)
            
            # Apply group opacity
            effective_opacity = track.get_effective_opacity(frame_index)
            if track.group_id and track.group_id in self._groups:
                effective_opacity *= self._groups[track.group_id].opacity
            
            # Convert blend_mode string to enum
            blend_mode_map = {
                "normal": BlendMode.NORMAL,
                "add": BlendMode.ADD,
                "multiply": BlendMode.MULTIPLY,
                "screen": BlendMode.SCREEN,
            }
            blend_mode = blend_mode_map.get(track.blend_mode, BlendMode.NORMAL)
            
            # Blend each pixel using blend mode
            for i in range(expected):
                composite[i] = blend_pixels(
                    bottom=composite[i],
                    top=layer_pixels[i],
                    opacity=effective_opacity,
                    blend_mode=blend_mode
                )
        
        return composite
    
    def _apply_layer_animation(
        self,
        track: LayerTrack,
        track_index: int,
        frame_index: int,
        pixels: List[Color],
        width: int,
        height: int
    ) -> List[Color]:
        """
        Apply layer animation transformations (scroll, rotate, etc.) to pixels.
        
        This transforms the pixel positions based on animation keyframes,
        allowing independent animations per layer.
        """
        animation = self._animation_manager.get_animation(track_index)
        if not animation or animation.animation_type.value == "none":
            return pixels
        
        from domain.layer_animation import AnimationType
        
        # Get animation properties at this frame
        total_frames = len(self._state.pattern().frames) if self._state.pattern() else 1
        offset_x = animation.get_property_at_frame(frame_index, total_frames, "offset_x")
        offset_y = animation.get_property_at_frame(frame_index, total_frames, "offset_y")
        rotation = animation.get_property_at_frame(frame_index, total_frames, "rotation")
        scale = animation.get_property_at_frame(frame_index, total_frames, "scale")
        
        # Apply speed multiplier to offset values (not keyframe progression)
        if offset_x is not None:
            offset_x = offset_x * animation.speed
        if offset_y is not None:
            offset_y = offset_y * animation.speed
        
        # Apply scroll animation
        if animation.animation_type == AnimationType.SCROLL:
            if offset_x is not None or offset_y is not None:
                pixels = self._scroll_pixels(
                    pixels, width, height,
                    offset_x or 0.0, offset_y or 0.0
                )
        
        # Apply rotation (if implemented)
        if animation.animation_type == AnimationType.ROTATE and rotation is not None:
            # Rotation would be implemented here
            pass
        
        # Apply scale (if implemented)
        if animation.animation_type == AnimationType.SCALE and scale is not None:
            # Scale would be implemented here
            pass
        
        return pixels
    
    def _scroll_pixels(
        self,
        pixels: List[Color],
        width: int,
        height: int,
        offset_x: float,
        offset_y: float
    ) -> List[Color]:
        """
        Scroll pixels by offset amount with wrapping at edges.
        
        Args:
            pixels: Source pixel array
            width: Matrix width
            height: Matrix height
            offset_x: Horizontal scroll offset (normalized: 1.0 = full width right, -1.0 = full width left)
            offset_y: Vertical scroll offset (normalized: 1.0 = full height down, -1.0 = full height up)
        
        Returns:
            Scrolled pixel array (new array, original pixels unchanged)
            
        Note:
            Scroll animations wrap pixels at edges (circular scroll). Pixels that
            go off one edge appear on the opposite edge. This creates a seamless
            looping effect. The original pixel array is not modified.
        """
        if offset_x == 0.0 and offset_y == 0.0:
            return pixels
        
        result = [pixels[i] for i in range(len(pixels))]
        
        # Convert normalized offset to pixel distance
        # Handle negative offsets (left/up)
        distance_x = int(offset_x * width)
        distance_y = int(offset_y * height)
        
        # Apply horizontal scroll
        if distance_x != 0:
            for y in range(height):
                for x in range(width):
                    # For right scroll (positive): move pixels left, read from right
                    # For left scroll (negative): move pixels right, read from left
                    src_x = (x - distance_x) % width
                    if src_x < 0:
                        src_x += width
                    src_idx = y * width + src_x
                    dst_idx = y * width + x
                    if 0 <= src_idx < len(pixels) and 0 <= dst_idx < len(result):
                        result[dst_idx] = pixels[src_idx]
            pixels = result
            result = [pixels[i] for i in range(len(pixels))]
        
        # Apply vertical scroll
        if distance_y != 0:
            for y in range(height):
                for x in range(width):
                    # For down scroll (positive): move pixels up, read from down
                    # For up scroll (negative): move pixels down, read from up
                    src_y = (y - distance_y) % height
                    if src_y < 0:
                        src_y += height
                    src_idx = src_y * width + x
                    dst_idx = y * width + x
                    if 0 <= src_idx < len(pixels) and 0 <= dst_idx < len(result):
                        result[dst_idx] = pixels[src_idx]
        
        return result
    
    def _get_composite_pixels_simple(self, frame_index: int) -> List[Color]:
        """Simple alpha blend fallback (works with LayerTracks)"""
        width = self._state.width()
        height = self._state.height()
        expected = width * height
        
        composite = [(0, 0, 0)] * expected
        
        # Sort layer tracks by z_index
        sorted_tracks = sorted(self._layer_tracks, key=lambda t: t.z_index)
        
        for track in sorted_tracks:
            if not track.get_effective_visibility(frame_index):
                continue
            
            layer_frame = track.get_frame(frame_index)
            if not layer_frame:
                continue
            
            layer_pixels = list(layer_frame.pixels[:expected])
            if len(layer_pixels) < expected:
                layer_pixels += [(0, 0, 0)] * (expected - len(layer_pixels))
            
            opacity = track.get_effective_opacity(frame_index)
            for i in range(expected):
                r1, g1, b1 = composite[i]
                r2, g2, b2 = layer_pixels[i]
                r = int(r1 * (1 - opacity) + r2 * opacity)
                g = int(g1 * (1 - opacity) + g2 * opacity)
                b = int(b1 * (1 - opacity) + b2 * opacity)
                composite[i] = (r, g, b)
        
        return composite

    def apply_pixel(self, frame_index: int, x: int, y: int, colour: Optional[Color], width: int, height: int, layer_index: int = 0) -> None:
        """
        Apply pixel change to a specific layer track at a specific frame.
        
        This updates the LayerFrame pixels for the specified layer track and frame.
        """
        if 0 <= layer_index < len(self._layer_tracks):
            track = self._layer_tracks[layer_index]
            layer_frame = track.get_or_create_frame(frame_index, width, height)
            
            idx = y * width + x
            if idx < len(layer_frame.pixels):
                layer_frame.pixels[idx] = colour or (0, 0, 0)
                # Sync frame from layers after pixel change
                self.sync_frame_from_layers(frame_index)
                self.pixel_changed.emit(frame_index, x, y, colour or (0, 0, 0))
                self.layers_changed.emit(frame_index)

    def replace_pixels(self, frame_index: int, pixels, layer_index: int = 0) -> None:
        """Replace pixels in a specific layer track at a specific frame."""
        if 0 <= layer_index < len(self._layer_tracks):
            track = self._layer_tracks[layer_index]
            layer_frame = track.get_or_create_frame(
                frame_index, self._state.width(), self._state.height()
            )
            layer_frame.pixels = list(pixels)
            self.frame_pixels_changed.emit(frame_index)
            self.layers_changed.emit(frame_index)

    def resize_pixels(self, width: int, height: int) -> None:
        """Resize all layer tracks to new dimensions."""
        # Update pattern metadata first so get_composite_pixels uses correct dimensions
        if self._state.pattern():
            self._state.pattern().metadata.width = width
            self._state.pattern().metadata.height = height
        
        expected = width * height
        for track in self._layer_tracks:
            for frame_idx, layer_frame in track.frames.items():
                pixels = list(layer_frame.pixels[:expected])
                if len(pixels) < expected:
                    pixels += [(0, 0, 0)] * (expected - len(pixels))
                layer_frame.pixels = pixels
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
    
    # Layer Group Methods (updated for LayerTracks - groups span frames)
    def create_group(self, frame_index: int, name: str = "Group") -> str:
        """
        Create a new layer group (backward compatibility).
        
        Groups now span across all frames (not per-frame).
        """
        import uuid
        group_id = str(uuid.uuid4())
        self._groups[group_id] = LayerGroup(group_id, name)
        self.group_changed.emit(-1)  # -1 = all frames
        return group_id
    
    def remove_group(self, frame_index: int, group_id: str) -> bool:
        """
        Remove a layer group and ungroup its layers (backward compatibility).
        
        Groups span frames, so removing affects all frames.
        """
        if group_id in self._groups:
            # Ungroup all layer tracks in this group
            for track in self._layer_tracks:
                if track.group_id == group_id:
                    track.group_id = None
            del self._groups[group_id]
            self.group_changed.emit(-1)  # -1 = all frames
            self.layers_changed.emit(-1)  # -1 = all frames
            return True
        return False
    
    def add_layer_to_group(self, frame_index: int, layer_index: int, group_id: str) -> bool:
        """Add a layer track to a group (backward compatibility)."""
        if 0 <= layer_index < len(self._layer_tracks) and group_id in self._groups:
            self._layer_tracks[layer_index].group_id = group_id
            self.group_changed.emit(-1)  # -1 = all frames
            self.layers_changed.emit(-1)  # -1 = all frames
            return True
        return False
    
    def remove_layer_from_group(self, frame_index: int, layer_index: int) -> bool:
        """Remove a layer track from its group (backward compatibility)."""
        if 0 <= layer_index < len(self._layer_tracks):
            self._layer_tracks[layer_index].group_id = None
            self.group_changed.emit(-1)  # -1 = all frames
            self.layers_changed.emit(-1)  # -1 = all frames
            return True
        return False
    
    def set_group_visible(self, frame_index: int, group_id: str, visible: bool) -> None:
        """Set group visibility (backward compatibility - groups span frames)."""
        if group_id in self._groups:
            self._groups[group_id].visible = visible
            self.group_changed.emit(-1)  # -1 = all frames
            self.layers_changed.emit(-1)  # -1 = all frames
    
    def set_group_opacity(self, frame_index: int, group_id: str, opacity: float) -> None:
        """Set group opacity (backward compatibility - groups span frames)."""
        if group_id in self._groups:
            self._groups[group_id].opacity = max(0.0, min(1.0, opacity))
            self.group_changed.emit(-1)  # -1 = all frames
            self.layers_changed.emit(-1)  # -1 = all frames
    
    def get_groups(self, frame_index: int) -> Dict[str, LayerGroup]:
        """Get all groups (backward compatibility - groups span frames)."""
        return self._groups.copy()
    
    # Layer Mask Methods (updated for LayerTracks)
    def set_layer_mask(self, frame_index: int, layer_index: int, mask: List[float]) -> bool:
        """Set mask for a layer track at a specific frame."""
        if 0 <= layer_index < len(self._layer_tracks):
            track = self._layer_tracks[layer_index]
            layer_frame = track.get_or_create_frame(
                frame_index, self._state.width(), self._state.height()
            )
            # Clamp mask values to 0.0-1.0
            clamped_mask = [max(0.0, min(1.0, v)) for v in mask]
            layer_frame.mask = clamped_mask
            self.layers_changed.emit(frame_index)
            return True
        return False
    
    def clear_layer_mask(self, frame_index: int, layer_index: int) -> bool:
        """Clear mask for a layer track at a specific frame."""
        if 0 <= layer_index < len(self._layer_tracks):
            track = self._layer_tracks[layer_index]
            layer_frame = track.get_frame(frame_index)
            if layer_frame:
                layer_frame.mask = None
                self.layers_changed.emit(frame_index)
                return True
        return False
    
    def get_layer_mask(self, frame_index: int, layer_index: int) -> Optional[List[float]]:
        """Get mask for a layer track at a specific frame."""
        if 0 <= layer_index < len(self._layer_tracks):
            track = self._layer_tracks[layer_index]
            layer_frame = track.get_frame(frame_index)
            if layer_frame:
                return layer_frame.mask
        return None
    
    def copy_layer_to_frames(self, source_frame: int, source_layer: int, target_frames: List[int]) -> None:
        """
        Copy a layer track's frame data from one frame to multiple target frames.
        
        Args:
            source_frame: Index of source frame
            source_layer: Index of source layer track
            target_frames: List of target frame indices
        """
        if source_layer < 0 or source_layer >= len(self._layer_tracks):
            return
        
        source_track = self._layer_tracks[source_layer]
        source_layer_frame = source_track.get_frame(source_frame)
        
        if not source_layer_frame:
            return
        
        # Copy frame data to each target frame
        for target_frame in target_frames:
            if target_frame == source_frame:
                continue  # Skip copying to same frame
            
            # Copy the layer frame
            copied_frame = source_layer_frame.copy()
            source_track.set_frame(target_frame, copied_frame)
            
            # Emit signals
            self.layers_changed.emit(target_frame)
    
    def are_layers_synced(self, frame_index: int) -> bool:
        """
        Check if layers are in sync with frame pixels.
        
        Returns True if composite of all visible layers matches frame.pixels,
        False otherwise. Allows small tolerance for rounding differences.
        
        Args:
            frame_index: Index of frame to check
            
        Returns:
            True if synced, False otherwise
        """
        if not self._state.pattern() or frame_index >= len(self._state.pattern().frames):
            return True  # Consider synced if no pattern/frame
        
        # Get composite from layers
        composite = self.get_composite_pixels(frame_index)
        
        # Get frame pixels
        frame = self._state.pattern().frames[frame_index]
        frame_pixels = list(frame.pixels)
        
        # Ensure same length
        expected = len(composite)
        if len(frame_pixels) != expected:
            return False
        
        # Compare pixel-by-pixel with tolerance for rounding
        tolerance = 1  # Allow 1 pixel difference per channel for rounding
        for i in range(expected):
            comp_r, comp_g, comp_b = composite[i]
            frame_r, frame_g, frame_b = frame_pixels[i]
            
            if (abs(comp_r - frame_r) > tolerance or
                abs(comp_g - frame_g) > tolerance or
                abs(comp_b - frame_b) > tolerance):
                return False
        
        return True