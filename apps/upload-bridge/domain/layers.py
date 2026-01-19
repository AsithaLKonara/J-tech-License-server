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
import logging
from enum import Enum
from typing import Optional, Tuple, List, Dict
from copy import deepcopy
from PySide6.QtCore import QObject, Signal
from core.pattern import Frame, Pattern
from domain.pattern_state import PatternState

Color = Tuple[int, int, int]


class BlendMode(Enum):
    """Blend modes for layer compositing (Photoshop-style)."""
    NORMAL = "normal"
    MULTIPLY = "multiply"
    SCREEN = "screen"
    OVERLAY = "overlay"
    ADD = "add"
    SUBTRACT = "subtract"
    DIFFERENCE = "difference"
    COLOR_DODGE = "color_dodge"
    COLOR_BURN = "color_burn"


def blend_pixels(base: Color, blend: Color, mode: str, opacity: float = 1.0) -> Color:
    """
    Blend two pixels using the specified blend mode.
    
    Args:
        base: Base layer pixel (r, g, b)
        blend: Blend layer pixel (r, g, b)
        mode: Blend mode ("normal", "multiply", "screen", etc.)
        opacity: Blend layer opacity (0.0-1.0)
    
    Returns:
        Blended pixel (r, g, b)
    """
    if opacity <= 0:
        return base
    
    br, bg, bb = base
    tr, tg, tb = blend
    
    # Normalize to 0-1 range for calculations
    br_n, bg_n, bb_n = br / 255.0, bg / 255.0, bb / 255.0
    tr_n, tg_n, tb_n = tr / 255.0, tg / 255.0, tb / 255.0
    
    # Apply blend mode
    if mode == "multiply":
        r_n = br_n * tr_n
        g_n = bg_n * tg_n
        b_n = bb_n * tb_n
    elif mode == "screen":
        r_n = 1 - (1 - br_n) * (1 - tr_n)
        g_n = 1 - (1 - bg_n) * (1 - tg_n)
        b_n = 1 - (1 - bb_n) * (1 - tb_n)
    elif mode == "overlay":
        r_n = 2 * br_n * tr_n if br_n < 0.5 else 1 - 2 * (1 - br_n) * (1 - tr_n)
        g_n = 2 * bg_n * tg_n if bg_n < 0.5 else 1 - 2 * (1 - bg_n) * (1 - tg_n)
        b_n = 2 * bb_n * tb_n if bb_n < 0.5 else 1 - 2 * (1 - bb_n) * (1 - tb_n)
    elif mode == "add":
        r_n = min(1.0, br_n + tr_n)
        g_n = min(1.0, bg_n + tg_n)
        b_n = min(1.0, bb_n + tb_n)
    elif mode == "subtract":
        r_n = max(0.0, br_n - tr_n)
        g_n = max(0.0, bg_n - tg_n)
        b_n = max(0.0, bb_n - tb_n)
    elif mode == "difference":
        r_n = abs(br_n - tr_n)
        g_n = abs(bg_n - tg_n)
        b_n = abs(bb_n - tb_n)
    elif mode == "color_dodge":
        r_n = min(1.0, br_n / (1 - tr_n + 0.001))
        g_n = min(1.0, bg_n / (1 - tg_n + 0.001))
        b_n = min(1.0, bb_n / (1 - tb_n + 0.001))
    elif mode == "color_burn":
        r_n = 1 - min(1.0, (1 - br_n) / (tr_n + 0.001))
        g_n = 1 - min(1.0, (1 - bg_n) / (tg_n + 0.001))
        b_n = 1 - min(1.0, (1 - bb_n) / (tb_n + 0.001))
    else:  # normal
        r_n, g_n, b_n = tr_n, tg_n, tb_n
    
    # Apply opacity (blend between base and result)
    r_n = br_n + (r_n - br_n) * opacity
    g_n = bg_n + (g_n - bg_n) * opacity
    b_n = bb_n + (b_n - bb_n) * opacity
    
    # Convert back to 0-255 range and clamp
    r = max(0, min(255, int(r_n * 255)))
    g = max(0, min(255, int(g_n * 255)))
    b = max(0, min(255, int(b_n * 255)))
    
    return (r, g, b)

# LMS Automation Execution Order (fixed priority)
# Actions are sorted by this priority before applying (lower priority = applied first)
ACTION_PRIORITY = {
    "scroll": 10,
    "rotate": 20,
    "mirror": 30,
    "flip": 30,
    "bounce": 40,
    "wipe": 50,
    "reveal": 60,
    "radial": 70,
    "colour_cycle": 80,
    "invert": 90,
}

# Import LayerAction for per-layer automation
try:
    from domain.automation.layer_action import LayerAction, get_action_step
except (ImportError, AttributeError):
    # Fallback if module not available
    LayerAction = None
    get_action_step = None

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
    - Per-pixel alpha channel (0-255, 255 = fully opaque)
    - Override visibility (None = use layer default)
    - Override opacity (None = use layer default)
    - Per-pixel mask (0.0-1.0, for additional masking effects)
    
    Pixel Storage Model:
    - Each LayerFrame stores its own pixel array
    - Pixels are stored per frame (not shared across frames)
    - Animations transform pixels at render time without modifying stored pixels
    - This allows the same base pixels to be transformed differently per frame
    
    Alpha Channel Model:
    - alpha: List[int] where alpha[i] = alpha value (0-255) for pixels[i]
    - 255 = fully opaque (pixel visible)
    - 0 = fully transparent (pixel invisible, compositing will skip)
    - If alpha is None or shorter than pixels, defaults to 255 (fully opaque) for missing entries
    - Alpha is separate from RGB color - black pixels (0,0,0) can be visible if alpha > 0
    """
    
    def __init__(
        self,
        pixels: Optional[List[Color]] = None,
        alpha: Optional[List[int]] = None,  # Per-pixel alpha (0-255, 255 = opaque)
        visible: Optional[bool] = None,  # None = use layer default
        opacity: Optional[float] = None,  # None = use layer default
        mask: Optional[List[float]] = None,  # Mask values 0.0-1.0 per pixel (additional masking)
    ):
        self.pixels = pixels or []
        self.alpha = alpha  # Per-pixel alpha channel (0-255)
        self.visible = visible  # None means inherit from layer
        self.opacity = opacity  # None means inherit from layer (clamped if set)
        if self.opacity is not None:
            self.opacity = max(0.0, min(1.0, self.opacity))
        self.mask = mask  # Per-pixel mask (0.0 = transparent, 1.0 = opaque) - for additional effects
    
    def get_pixel_alpha(self, index: int) -> int:
        """
        Get alpha value for a pixel at the given index.
        
        Args:
            index: Pixel index
            
        Returns:
            Alpha value (0-255), defaulting to 255 (opaque) if alpha array missing or too short
        """
        if self.alpha and index < len(self.alpha):
            return max(0, min(255, self.alpha[index]))
        return 255  # Default: fully opaque
    
    def ensure_alpha(self, pixel_count: int) -> None:
        """
        Ensure alpha array exists and has correct length.
        
        Args:
            pixel_count: Expected number of pixels
        """
        if self.alpha is None:
            self.alpha = [255] * pixel_count  # Default: fully opaque
        elif len(self.alpha) < pixel_count:
            # Extend with opaque alpha
            self.alpha.extend([255] * (pixel_count - len(self.alpha)))
        elif len(self.alpha) > pixel_count:
            # Truncate to match pixel count
            self.alpha = self.alpha[:pixel_count]
    
    def copy(self) -> 'LayerFrame':
        """Create a deep copy of this layer frame."""
        return LayerFrame(
            pixels=deepcopy(self.pixels),
            alpha=deepcopy(self.alpha) if self.alpha else None,
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
    - Frame data (Dict[int, LayerFrame]) - one LayerFrame per frame (sparse - only created frames exist)
    - Global properties (visible, opacity, blend_mode) - can be overridden per-frame
    - Layer metadata (name, z_index, group_id, locked)
    - Automation actions - applied at render time (non-destructive)
    
    FRAME INHERITANCE MODEL:
    - Frames are stored sparsely (only frames that have been created exist)
    - Missing frames return None from get_frame() and are skipped during rendering (treated as transparent)
    - Default frame values when created via get_or_create_frame():
      * pixels: All black (0, 0, 0)
      * alpha: All fully opaque (255)
      * visible: None (inherits from track.visible)
      * opacity: None (inherits from track.opacity)
    - Per-frame overrides (visible, opacity) take precedence over track defaults
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
        automation: Optional[List] = None,  # Per-layer automation actions
        id: Optional[str] = None,  # Unique ID for this layer track (to avoid index instability)
    ):
        import uuid
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.frames: Dict[int, LayerFrame] = frames or {}
        self.visible = visible  # Global visibility (can be overridden per-frame)
        self.opacity = max(0.0, min(1.0, opacity))  # Global opacity (can be overridden per-frame) - kept for backward compat, ignored in order-only render
        self.blend_mode = blend_mode  # "normal", "add", "multiply", "screen" - kept for backward compat, ignored in order-only render
        self.group_id = group_id  # ID of layer group this layer belongs to
        self.locked = locked  # Lock layer to prevent editing
        self.z_index = z_index  # Rendering order
        self.start_frame = start_frame  # Layer timing: start frame
        self.end_frame = end_frame  # Layer timing: end frame (inclusive)
        self.automation: List = automation or []  # Per-layer automation actions (LayerAction objects)
    
    @property
    def order(self) -> int:
        """Alias for z_index for clarity (order-only rendering)."""
        return self.z_index
    
    @order.setter
    def order(self, value: int) -> None:
        """Set order (updates z_index)."""
        self.z_index = value
    
    def add_automation(self, action) -> None:
        """Add an automation action to this layer."""
        if LayerAction is not None and not isinstance(action, LayerAction):
            raise TypeError(f"Expected LayerAction, got {type(action)}")
        self.automation.append(action)
    
    def remove_automation(self, index: int) -> None:
        """Remove an automation action by index."""
        if 0 <= index < len(self.automation):
            del self.automation[index]
    
    def get_automation(self) -> List:
        """Get all automation actions for this layer."""
        return list(self.automation)
    
    def get_frame(self, frame_index: int) -> Optional[LayerFrame]:
        """
        Get frame data for a specific frame index.
        
        Returns None if:
        - Frame is outside layer's timing range (start_frame/end_frame)
        - Frame doesn't exist in this track
        
        DEFAULT BEHAVIOR:
        - Missing frames return None (not automatically created)
        - render_frame() skips layers with missing frames (treats as transparent)
        - Use get_or_create_frame() to create frames with default values
        
        Default frame values:
        - pixels: All black (0, 0, 0)
        - alpha: All fully opaque (255)
        - visible: Inherits from track.visible
        - opacity: Inherits from track.opacity
        """
        # Check if frame is outside layer's timing range
        if self.start_frame is not None and frame_index < self.start_frame:
            return None
        if self.end_frame is not None and frame_index > self.end_frame:
            return None
        return self.frames.get(frame_index)
    
    def get_or_create_frame(self, frame_index: int, width: int, height: int) -> LayerFrame:
        """
        Get frame data, creating it if it doesn't exist.
        
        This method ensures a LayerFrame exists for the given frame_index.
        If the frame doesn't exist, it creates a new one with default values.
        
        DEFAULT FRAME VALUES:
        - pixels: All black (0, 0, 0) with correct pixel count (width * height)
        - alpha: All fully opaque (255) with same count as pixels
        - visible: None (inherits from track.visible)
        - opacity: None (inherits from track.opacity)
        - mask: None (no mask applied)
        
        Args:
            frame_index: Frame index
            width: Matrix width (for pixel count calculation)
            height: Matrix height (for pixel count calculation)
            
        Returns:
            LayerFrame (existing or newly created)
        """
        if frame_index not in self.frames:
            blank_pixels = [(0, 0, 0)] * (width * height)
            # Initialize with fully transparent alpha (0) for all pixels
            blank_alpha = [0] * (width * height)
            self.frames[frame_index] = LayerFrame(pixels=blank_pixels, alpha=blank_alpha)
        else:
            # Ensure existing frame has alpha channel
            frame = self.frames[frame_index]
            frame.ensure_alpha(width * height)
        return self.frames[frame_index]
    
    def set_frame(self, frame_index: int, layer_frame: LayerFrame) -> None:
        """Set frame data for a specific frame index."""
        self.frames[frame_index] = layer_frame
    
    def get_frame_count(self) -> int:
        """Get the number of frames in this layer track."""
        if not self.frames:
            return 0
        # Return max frame index + 1 (frames are 0-indexed)
        return max(self.frames.keys()) + 1 if self.frames else 0
    
    def get_effective_visibility(self, frame_index: int) -> bool:
        """Get effective visibility for a frame (frame override or layer default)."""
        frame = self.get_frame(frame_index)
        try:
            if frame and frame.visible is not None:
                return frame.visible
        except AttributeError:
            pass
        return self.visible
    
    def get_effective_opacity(self, frame_index: int) -> float:
        """Get effective opacity for a frame (frame override or layer default)."""
        frame = self.get_frame(frame_index)
        try:
            if frame and frame.opacity is not None:
                return max(0.0, min(1.0, frame.opacity))
        except AttributeError:
            pass
        return self.opacity
    
    def copy(self) -> 'LayerTrack':
        """Create a deep copy of this layer track."""
        copied_frames = {
            idx: frame.copy() for idx, frame in self.frames.items()
        }
        copied_automation = [deepcopy(action) for action in self.automation] if self.automation else None
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
            automation=copied_automation,
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
        locked: bool = False,  # Lock layer to prevent editing
        id: Optional[str] = None  # Unique ID for tracking
    ):
        self.id = id
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
        
        # Initialize invariant checker
        try:
            from domain.invariants import InvariantChecker, set_global_checker
            self._invariant_checker = InvariantChecker(self)
            set_global_checker(self._invariant_checker)
        except ImportError:
            self._invariant_checker = None
        
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
        Also migrates old LayerAnimation objects to new LayerAction system.
        """
        self._state.set_pattern(pattern)
        self._layer_tracks = []
        self._groups = {}
        self._legacy_layers = None
        self._legacy_groups = None
        self._use_legacy_mode = False
        
        # Try to auto-migrate if old structure exists
        migrated = auto_migrate_on_load(self)
        
        # Create default layer track spanning all frames (if not migrated)
        if not migrated and pattern and pattern.frames:
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
                
                # Initialize with fully opaque alpha
                pixel_count = len(frame_pixels)
                frame_alpha = [255] * pixel_count
                layer_frame = LayerFrame(pixels=frame_pixels, alpha=frame_alpha)
                default_track.set_frame(idx, layer_frame)
            
            self._layer_tracks.append(default_track)
        
        # Migrate old LayerAnimation objects to LayerAction system
        # This happens after layer tracks are set up (either migrated or default)
        try:
            from core.migration.animation_migration import migrate_animation_manager_to_layer_automation
            total_frames = len(pattern.frames) if pattern else 0
            if total_frames > 0 and hasattr(self, '_animation_manager') and self._layer_tracks:
                migrate_animation_manager_to_layer_automation(
                    self._animation_manager,
                    self,
                    total_frames
                )
        except ImportError:
            # Migration module not available - skip animation migration
            pass
        except Exception:
            # Migration failed - continue without migrating animations
            pass
        
        # Migrate old LayerAnimation objects to LayerAction system
        # This happens after layer tracks are set up
        try:
            from core.migration.animation_migration import migrate_animation_manager_to_layer_automation
            total_frames = len(pattern.frames) if pattern else 0
            if total_frames > 0 and hasattr(self, '_animation_manager') and self._layer_tracks:
                migrate_animation_manager_to_layer_automation(
                    self._animation_manager,
                    self,
                    total_frames
                )
        except ImportError:
            # Migration module not available - skip animation migration
            pass
        except Exception:
            # Migration failed - continue without migrating animations
            pass

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
        """Set animation for a layer track (backward compatibility)."""
        if 0 <= track_index < len(self._layer_tracks):
            track = self._layer_tracks[track_index]
            self._animation_manager.set_animation(track.id, animation)
            # Emit signal to update UI
            self.layers_changed.emit(-1)  # -1 = all frames
    
    def set_layer_automation(self, layer_index: int, actions: List) -> None:
        """
        Set automation actions for a layer track.
        
        Args:
            layer_index: Index of the layer track
            actions: List of LayerAction objects
        """
        if 0 <= layer_index < len(self._layer_tracks):
            track = self._layer_tracks[layer_index]
            track.automation = list(actions) if actions else []
            # Emit signal to update UI
            self.layers_changed.emit(-1)  # -1 = all frames
    
    def get_layer_automation(self, layer_index: int) -> List:
        """
        Get automation actions for a layer track.
        
        Args:
            layer_index: Index of the layer track
            
        Returns:
            List of LayerAction objects
        """
        if 0 <= layer_index < len(self._layer_tracks):
            return self._layer_tracks[layer_index].get_automation()
        return []
    
    def add_layer_automation(self, layer_index: int, action) -> None:
        """
        Add an automation action to a layer track.
        
        Args:
            layer_index: Index of the layer track
            action: LayerAction object to add
        """
        if 0 <= layer_index < len(self._layer_tracks):
            track = self._layer_tracks[layer_index]
            track.add_automation(action)
            # Emit signal to update UI
            self.layers_changed.emit(-1)  # -1 = all frames
    
    def remove_layer_automation(self, layer_index: int, action_index: int) -> None:
        """
        Remove an automation action from a layer track.
        
        Args:
            layer_index: Index of the layer track
            action_index: Index of the action to remove
        """
        if 0 <= layer_index < len(self._layer_tracks):
            track = self._layer_tracks[layer_index]
            track.remove_automation(action_index)
            # Emit signal to update UI
            self.layers_changed.emit(-1)  # -1 = all frames
    
    def remove_layer_animation(self, layer_index: int) -> None:
        """Remove animation from a layer track (backward compatibility)."""
        if 0 <= layer_index < len(self._layer_tracks):
            track = self._layer_tracks[layer_index]
            self._animation_manager.remove_animation(track.id)
            # Emit signal to update UI
            self.layers_changed.emit(-1)
    
    def is_layer_active(self, track: LayerTrack, frame_index: int) -> bool:
        """
        Check if a layer track is active at a given frame index.
        
        CRITICAL LAYER ISOLATION ENFORCEMENT:
        - Each layer has its own local frame range (start_frame to end_frame)
        - Layer 1: 0-11, Layer 2: 0-5 (NOT 12-17)
        - Layers are transparent outside their frame range
        
        Args:
            track: LayerTrack to check
            frame_index: Global frame index to check
            
        Returns:
            True if layer is active at this frame, False otherwise
        """
        # Check if frame is within layer's active window
        if track.start_frame is not None and frame_index < track.start_frame:
            return False
        if track.end_frame is not None and frame_index > track.end_frame:
            return False
        return True
    
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
                # Initialize with fully transparent alpha so proper composting happens
                pixel_count = len(blank_pixels)
                # Create a fresh alpha list per frame to avoid sharing state
                blank_alpha = [0] * pixel_count
                layer_frame = LayerFrame(pixels=list(blank_pixels), alpha=blank_alpha)
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
    
    def merge_layer_tracks(
        self, 
        source_indices: List[int], 
        target_index: Optional[int] = None,
        merge_mode: str = "composite"
    ) -> int:
        """
        Merge multiple layer tracks into one.
        
        Args:
            source_indices: List of layer track indices to merge
            target_index: Target layer index (None = merge into first source)
            merge_mode: "composite" (blend layers) or "replace" (use top layer)
        
        Returns:
            Index of merged layer track
        """
        if not source_indices or len(source_indices) < 2:
            raise ValueError("Need at least 2 layers to merge")
        
        # Validate indices
        for idx in source_indices:
            if idx < 0 or idx >= len(self._layer_tracks):
                raise IndexError(f"Invalid layer index: {idx}")
        
        # Determine target layer (first source if not specified)
        if target_index is None:
            target_index = min(source_indices)
        
        if target_index not in source_indices:
            raise ValueError(f"Target layer {target_index} must be in source_indices")
        
        target_track = self._layer_tracks[target_index]
        width = self._state.width()
        height = self._state.height()
        
        # Get all frames that exist in any source layer
        all_frame_indices = set()
        for idx in source_indices:
            track = self._layer_tracks[idx]
            all_frame_indices.update(track.frames.keys())
        
        # Merge layers frame by frame
        for frame_idx in all_frame_indices:
            target_frame = target_track.get_or_create_frame(frame_idx, width, height)
            target_pixels = list(target_frame.pixels)
            
            # Composite or replace with other source layers (in z-order)
            for idx in sorted(source_indices, key=lambda i: self._layer_tracks[i].z_index):
                if idx == target_index:
                    continue  # Skip target layer
                
                track = self._layer_tracks[idx]
                source_frame = track.get_frame(frame_idx)
                if source_frame and track.get_effective_visibility(frame_idx):
                    source_pixels = list(source_frame.pixels)
                    source_opacity = track.get_effective_opacity(frame_idx)
                    
                    if merge_mode == "composite":
                        # Composite: blend layers with opacity
                        for i in range(min(len(target_pixels), len(source_pixels))):
                            r1, g1, b1 = target_pixels[i]
                            r2, g2, b2 = source_pixels[i]
                            r = int(r1 * (1 - source_opacity) + r2 * source_opacity)
                            g = int(g1 * (1 - source_opacity) + g2 * source_opacity)
                            b = int(b1 * (1 - source_opacity) + b2 * source_opacity)
                            target_pixels[i] = (r, g, b)
                    else:  # replace mode - use top visible layer
                        # Replace: overwrite with source pixels (respecting visibility)
                        if source_opacity > 0.5:  # Only replace if mostly visible
                            target_pixels = source_pixels[:]
            
            target_frame.pixels = target_pixels
        
        # Remove merged layers (except target)
        layers_to_remove = [idx for idx in source_indices if idx != target_index]
        for idx in sorted(layers_to_remove, reverse=True):
            self.remove_layer_track(idx)
        
        # Update z_index for remaining layers
        for i, track in enumerate(self._layer_tracks):
            track.z_index = i
        
        self.layers_changed.emit(-1)
        return target_index
    
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
                    locked=track.locked,
                    id=track.id
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
                    locked=track.locked,
                    id=track.id
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
        Get composite pixels from all visible layer tracks.
        
        DEPRECATED: This method is kept for backward compatibility.
        New code should use render_frame() which uses order-only overwrite compositing.
        
        This method now delegates to render_frame() which implements
        the correct order-only rendering model (no blend modes, no opacity math).
        """
        # Use new render_frame() method (order-only overwrite)
        return self.render_frame(frame_index)
    
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
        animation = self._animation_manager.get_animation(track.id)
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
    
    def _pixels_to_grid(self, pixels: List[Color], width: int, height: int) -> List[List[Color]]:
        """Convert flat pixel array to 2D grid (row-major)."""
        grid = []
        for y in range(height):
            row = []
            for x in range(width):
                idx = y * width + x
                if idx < len(pixels):
                    row.append(pixels[idx])
                else:
                    row.append((0, 0, 0))
            grid.append(row)
        return grid
    
    def _grid_to_pixels(self, grid: List[List[Color]]) -> List[Color]:
        """Convert 2D grid to flat pixel array (row-major)."""
        pixels = []
        for row in grid:
            pixels.extend(row)
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
        Scroll pixels by offset amount (LMS-style: out-of-bounds = black).
        
        Pixels falling outside bounds become BLACK (0,0,0).
        No wrapping, no modulo, no clamp.
        
        Args:
            pixels: Source pixel array
            width: Matrix width
            height: Matrix height
            offset_x: Horizontal scroll offset (normalized: 1.0 = full width right, -1.0 = full width left)
            offset_y: Vertical scroll offset (normalized: 1.0 = full height down, -1.0 = full height up)
        
        Returns:
            Scrolled pixel array (new array, original pixels unchanged)
        """
        if offset_x == 0.0 and offset_y == 0.0:
            return pixels
        
        # Convert to grid for easier manipulation
        grid = self._pixels_to_grid(pixels, width, height)
        
        # Convert normalized offset to pixel distance
        distance_x = int(offset_x * width)
        distance_y = int(offset_y * height)
        
        # Create new grid (initialized to black)
        new_grid = [[(0, 0, 0) for _ in range(width)] for _ in range(height)]
        
        # Apply scroll: pixels that fall outside bounds become black
        for y in range(height):
            for x in range(width):
                src_x = x - distance_x
                src_y = y - distance_y
                
                # Check bounds: if source is within bounds, copy pixel; otherwise leave black
                if 0 <= src_x < width and 0 <= src_y < height:
                    new_grid[y][x] = grid[src_y][src_x]
                # else: remains (0, 0, 0) - LMS rule
        
        return self._grid_to_pixels(new_grid)
    
    def is_layer_active(self, track: LayerTrack, frame_index: int) -> bool:
        """
        Check if a layer track is active at the given frame index (LMS-style).
        
        Layer is fully inactive outside its window [start_frame, end_frame].
        Automation is skipped entirely if layer is inactive.
        
        Args:
            track: Layer track to check
            frame_index: Current frame index
            
        Returns:
            True if layer is active at this frame, False otherwise
        """
        if track.start_frame is not None and frame_index < track.start_frame:
            return False
        if track.end_frame is not None and frame_index > track.end_frame:
            return False
        return True
    
    def apply_opacity(self, pixels: List[Color], opacity: float) -> List[Color]:
        """
        Apply opacity as brightness scaling only (LMS-style).
        
        Opacity reduces brightness, not alpha. Black pixels remain black.
        No alpha blending or color mixing.
        
        Args:
            pixels: Source pixels
            opacity: Opacity value (0.0-1.0, 1.0 = fully opaque)
            
        Returns:
            Pixels with brightness scaled by opacity
        """
        if opacity >= 1.0:
            return pixels
        
        return [
            (int(r * opacity), int(g * opacity), int(b * opacity))
            for (r, g, b) in pixels
        ]
    
    def _overwrite_pixels(self, bottom: List[Color], top: List[Color], top_alpha: Optional[List[int]] = None, blend_mode: str = "normal", opacity: float = 1.0) -> List[Color]:
        """
        Layer compositing with blend mode support.
        
        Applies blend modes (Multiply, Screen, Overlay, etc.) when compositing layers.
        Pixels with alpha=0 are transparent (let lower layer show through).
        
        Args:
            bottom: Bottom layer pixels (will be blended with top)
            top: Top layer pixels (will blend onto bottom)
            top_alpha: Per-pixel alpha values for top layer (0-255). None = all opaque (255).
            blend_mode: Blend mode to use ("normal", "multiply", "screen", etc.)
            opacity: Layer opacity (0.0-1.0)
        
        Returns:
            Result pixels with top layer blended onto bottom
        """
        result = list(bottom)
        for i in range(min(len(top), len(result))):
            # Get alpha value for this pixel (default to 255 = opaque if not provided)
            alpha = top_alpha[i] if top_alpha and i < len(top_alpha) else 255
            
            # Skip fully transparent pixels
            if alpha == 0:
                continue
            
            # Apply blend mode with alpha and opacity
            alpha_normalized = (alpha / 255.0) * opacity
            result[i] = blend_pixels(bottom[i], top[i], blend_mode, alpha_normalized)
        
        return result
    
    def _apply_layer_automation(
        self,
        track: LayerTrack,
        frame_index: int,
        pixels: List[Color],
        width: int,
        height: int
    ) -> List[Color]:
        """
        Apply all automation actions for this layer at this frame.
        Only applies actions that are active at the given frame index.
        
        This is the new render-time automation system - actions are evaluated
        per frame without modifying stored pixels (non-destructive).
        
        Args:
            track: Layer track containing automation actions
            frame_index: Current frame index
            pixels: Base layer pixels (before automation)
            width: Matrix width
            height: Matrix height
            
        Returns:
            Transformed pixels after applying all active automation actions
        """
        # Check if automation system is available and has actions
        if not track.automation:
            # Fallback to old animation system for backward compatibility
            # Old system uses layer_track objects or indices as keys
            track_index = self._layer_tracks.index(track) if track in self._layer_tracks else -1
            if track_index >= 0:
                return self._apply_layer_animation(track, track_index, frame_index, pixels, width, height)
            return pixels
        
        # Start from base pixels (will be transformed by actions in pipeline)
        result = list(pixels)
        
        # Apply each automation action in LMS fixed priority order
        # This ensures consistent behavior regardless of insertion order
        sorted_actions = sorted(
            track.automation,
            key=lambda a: ACTION_PRIORITY.get(a.type.lower(), 100)
        )
        
        # ONE unified pipeline - all actions applied in priority order
        # Rotate/mirror/flip operate on the result of earlier actions in the same frame
        # They do NOT accumulate across frames (use base-frame time logic), but they DO
        # participate in the same-frame pipeline
        for action in sorted_actions:
            # Always check if action is active first (includes finalized check)
            if not action.is_active_at_frame(frame_index):
                continue
            
            # Then get step (both paths now consistent)
            if get_action_step:
                step = get_action_step(action, frame_index)
            else:
                # Fallback to method if function not available
                step = action.get_step(frame_index)
            
            if step is None:
                continue
            
            # Apply action to current pipeline result (not base pixels)
            result = self._apply_action_transform(
                result, action.type, action.params, step, width, height
            )
        
        return result
    
    def _apply_alpha_transform(
        self,
        track: LayerTrack,
        frame_index: int,
        alpha: List[int],
        width: int,
        height: int
    ) -> List[int]:
        """
        Apply alpha channel transformations to match pixel transformations.
        
        Alpha channel moves with pixels during transformations (scroll, rotate, etc.).
        This ensures transparency is preserved correctly after pixel transformations.
        
        Args:
            track: Layer track containing automation actions
            frame_index: Current frame index
            alpha: Base alpha channel (before automation)
            width: Matrix width
            height: Matrix height
            
        Returns:
            Transformed alpha channel after applying all active automation actions
        """
        if not track.automation or LayerAction is None:
            return alpha
        
        result = list(alpha)
        
        # Apply same transformations to alpha as pixels (sorted by LMS priority)
        sorted_actions = sorted(
            track.automation,
            key=lambda a: ACTION_PRIORITY.get(a.type.lower(), 100)
        )
        
        for action in sorted_actions:
            if get_action_step:
                step = get_action_step(action, frame_index)
            else:
                # Fallback to method if function not available
                if not action.is_active_at_frame(frame_index):
                    continue
                step = action.get_step(frame_index)
            
            if step is not None:
                # Transform alpha using same logic as pixels
                result = self._apply_alpha_action_transform(
                    result, action.type, action.params, step, width, height
                )
        
        return result
    
    def _apply_alpha_action_transform(
        self,
        alpha: List[int],
        action_type: str,
        params: Dict,
        step: int,
        width: int,
        height: int
    ) -> List[int]:
        """
        Apply action transformation to alpha channel (same as pixels but preserve alpha values).
        
        For most transformations, alpha moves with pixels. For effects that modify color
        (invert, colour_cycle), alpha is unchanged.
        
        Args:
            alpha: Source alpha channel
            action_type: Action type
            params: Action parameters
            step: Step number
            width: Matrix width
            height: Matrix height
            
        Returns:
            Transformed alpha channel
        """
        action_type_lower = action_type.lower()
        
        # Transformations that move pixels (alpha moves with pixels)
        if action_type_lower in ["scroll", "rotate", "mirror", "flip", "bounce"]:
            # Convert alpha to grid, apply same transformation as pixels, convert back
            alpha_grid = []
            idx = 0
            for _ in range(height):
                row = alpha[idx:idx + width]
                if len(row) < width:
                    row += [255] * (width - len(row))
                alpha_grid.append(row)
                idx += width
            
            if action_type_lower == "scroll":
                # Scroll alpha same as pixels
                direction = params.get("direction", "right").lower()
                offset_per_frame = max(1, int(params.get("offset", 1)))
                total_offset_pixels = step * offset_per_frame
                
                if direction in ["left", "right"]:
                    offset_x = (total_offset_pixels / width) if direction == "right" else (-total_offset_pixels / width)
                    offset_y = 0.0
                else:
                    offset_x = 0.0
                    offset_y = (total_offset_pixels / height) if direction == "down" else (-total_offset_pixels / height)
                
                # Apply scroll to alpha grid (simplified - same wrapping logic as pixels)
                new_grid = [[255] * width for _ in range(height)]
                distance_x = int(offset_x * width)
                distance_y = int(offset_y * height)
                
                for y in range(height):
                    for x in range(width):
                        src_x = (x - distance_x) % width
                        if src_x < 0:
                            src_x += width
                        src_y = (y - distance_y) % height
                        if src_y < 0:
                            src_y += height
                        new_grid[y][x] = alpha_grid[src_y][src_x]
                
                alpha_grid = new_grid
                
            elif action_type_lower == "rotate":
                # Rotate alpha same as pixels
                mode = params.get("mode", "90° Clockwise").lower()
                rotations = step % 4
                for _ in range(rotations):
                    if "clockwise" in mode:
                        rotated = []
                        for x in range(width):
                            new_row = []
                            for y in range(height - 1, -1, -1):
                                new_row.append(alpha_grid[y][x])
                            rotated.append(new_row)
                        alpha_grid = rotated
                    else:
                        rotated = []
                        for x in range(width - 1, -1, -1):
                            new_row = []
                            for y in range(height):
                                new_row.append(alpha_grid[y][x])
                            rotated.append(new_row)
                        alpha_grid = rotated
            
            elif action_type_lower in ["mirror", "flip", "bounce"]:
                # Mirror/flip/bounce alpha same as pixels
                axis = params.get("axis", "horizontal" if action_type_lower == "mirror" else "vertical").lower()
                if action_type_lower == "bounce" and step % 2 == 0:
                    pass  # No flip on even steps
                else:
                    if (axis == "horizontal" and action_type_lower != "flip") or (axis == "vertical" and action_type_lower == "flip"):
                        alpha_grid = [list(reversed(row)) for row in alpha_grid]
                    else:
                        alpha_grid = list(reversed(alpha_grid))
            
            # Convert back to flat list
            return [alpha_val for row in alpha_grid for alpha_val in row]
        
        # Effects that don't move pixels (wipe, reveal, radial) - alpha moves with pixels
        elif action_type_lower in ["wipe", "reveal", "radial"]:
            # These create new alpha values based on position, but we preserve existing alpha
            # For now, keep alpha unchanged (could enhance later to modify alpha based on effect)
            return alpha
        
        # Color-only effects (invert, colour_cycle) - alpha unchanged
        elif action_type_lower in ["invert", "colour_cycle"]:
            return alpha
        
        # Unknown - return unchanged
        return alpha
    
    def _apply_action_transform(
        self,
        pixels: List[Color],
        action_type: str,
        params: Dict,
        step: int,
        width: int,
        height: int
    ) -> List[Color]:
        """
        Apply a single action transformation to pixels.
        
        STATELESS FRAME-INDEX DRIVEN MODEL:
        - All transformations are stateless functions: transform(pixels, step, params)
        - step = frame_index - action.start_frame (number of frames since action started)
        - Progressive actions multiply: effective_value = base_value * step
        - Each frame calculates its transform independently from base pixels
        - No state accumulation - same base pixels + step always = same result
        
        Args:
            pixels: Source pixels (base layer pixels, unchanged by this method)
            action_type: Action type ("scroll", "rotate", "mirror", etc.)
            params: Action parameters
            step: Step number (frames since action started) - used for progressive calculations
            width: Matrix width
            height: Matrix height
            
        Returns:
            Transformed pixels (new array, original pixels unchanged)
        """
        action_type_lower = action_type.lower()
        
        if action_type_lower == "scroll":
            direction = params.get("direction", "right").lower()
            offset_per_frame = max(1, int(params.get("offset", 1)))
            # STATELESS: Progressive scroll - step * offset_per_frame
            # Frame 0 (step=0): no scroll, Frame 1 (step=1): 1*offset, Frame 2 (step=2): 2*offset, etc.
            total_offset_pixels = step * offset_per_frame
            
            # Calculate normalized offset for _scroll_pixels (which wraps)
            if direction in ["left", "right"]:
                offset_x = (total_offset_pixels / width) if direction == "right" else (-total_offset_pixels / width)
                offset_y = 0.0
            else:  # up, down
                offset_x = 0.0
                offset_y = (total_offset_pixels / height) if direction == "down" else (-total_offset_pixels / height)
            
            return self._scroll_pixels(pixels, width, height, offset_x, offset_y)
        
        elif action_type_lower == "rotate":
            mode = params.get("mode", "90° Clockwise").lower()
            # STATELESS: Progressive rotation - step % 4 rotations
            # Frame 0 (step=0): 0°, Frame 1 (step=1): 90°, Frame 2 (step=2): 180°, Frame 3 (step=3): 270°, Frame 4 (step=4): 0° (cycles)
            rotations = step % 4
            if "clockwise" in mode:
                for _ in range(rotations):
                    pixels = self._rotate_90_clockwise(pixels, width, height)
            elif "counter" in mode or "counter-clockwise" in mode:
                for _ in range(rotations):
                    pixels = self._rotate_90_counterclockwise(pixels, width, height)
            return pixels
        
        elif action_type_lower == "wipe":
            mode = params.get("mode", "Left to Right")
            offset_per_frame = max(1, int(params.get("offset", 1)))
            # STATELESS: Progressive wipe - step * offset_per_frame
            wipe_pos = step * offset_per_frame
            return self._wipe_pixels(pixels, width, height, mode, wipe_pos)
        
        elif action_type_lower == "reveal":
            direction = params.get("direction", "Left")
            offset_per_frame = max(1, int(params.get("offset", 1)))
            # STATELESS: Progressive reveal - step * offset_per_frame
            reveal_pos = step * offset_per_frame
            return self._reveal_pixels(pixels, width, height, direction, reveal_pos)
        
        elif action_type_lower == "bounce":
            axis = params.get("axis", "Horizontal")
            # STATELESS: Alternating bounce - step % 2 determines flip
            # Even steps (0, 2, 4...): original, Odd steps (1, 3, 5...): flipped
            if step % 2 == 1:
                return self._bounce_pixels(pixels, width, height, axis)
            else:
                return pixels  # Return original for even steps
        
        elif action_type_lower == "colour_cycle":
            mode = params.get("mode", "RGB")
            # STATELESS: Color cycle (no frame dependency, but included for completeness)
            return self._colour_cycle_pixels(pixels, mode)
        
        elif action_type_lower == "radial":
            type_str = params.get("type", "Spiral")
            # STATELESS: Radial effects (may have frame dependency in future via step)
            return self._radial_pixels(pixels, width, height, type_str, step)
        
        elif action_type_lower == "mirror":
            axis = params.get("axis", "horizontal").lower()
            # STATELESS: Mirror (no frame dependency - same result every frame)
            if axis == "horizontal":
                return self._mirror_horizontal(pixels, width, height)
            else:  # vertical
                return self._mirror_vertical(pixels, width, height)
        
        elif action_type_lower == "flip":
            axis = params.get("axis", "vertical").lower()
            # STATELESS: Flip (alias for mirror, no frame dependency)
            if axis == "horizontal":
                return self._mirror_horizontal(pixels, width, height)
            else:  # vertical
                return self._mirror_vertical(pixels, width, height)
        
        elif action_type_lower == "invert":
            # STATELESS: Invert (no frame dependency - same result every frame)
            return [(255 - r, 255 - g, 255 - b) for r, g, b in pixels]
        
        # Unknown action type - log warning and return unchanged
        known_types = ["scroll", "rotate", "wipe", "reveal", "bounce", "colour_cycle", "radial", "mirror", "flip", "invert"]
        if action_type_lower not in known_types:
            logging.warning(f"Unknown action type in _apply_action_transform: {action_type}. Action not applied.")
        return pixels
    
    def _rotate_90_clockwise(self, pixels: List[Color], width: int, height: int) -> List[Color]:
        """Rotate pixels 90° clockwise."""
        result = [(0, 0, 0)] * len(pixels)
        for y in range(height):
            for x in range(width):
                src_idx = y * width + x
                # Rotate 90° clockwise: (x, y) -> (height-1-y, x)
                new_x = height - 1 - y
                new_y = x
                if 0 <= new_x < height and 0 <= new_y < width:
                    dst_idx = new_y * width + new_x
                    if 0 <= src_idx < len(pixels) and 0 <= dst_idx < len(result):
                        result[dst_idx] = pixels[src_idx]
        return result
    
    def _rotate_90_counterclockwise(self, pixels: List[Color], width: int, height: int) -> List[Color]:
        """Rotate pixels 90° counter-clockwise."""
        result = [(0, 0, 0)] * len(pixels)
        for y in range(height):
            for x in range(width):
                src_idx = y * width + x
                # Rotate 90° counter-clockwise: (x, y) -> (y, width-1-x)
                new_x = y
                new_y = width - 1 - x
                if 0 <= new_x < height and 0 <= new_y < width:
                    dst_idx = new_y * width + new_x
                    if 0 <= src_idx < len(pixels) and 0 <= dst_idx < len(result):
                        result[dst_idx] = pixels[src_idx]
        return result
    
    def _mirror_horizontal(self, pixels: List[Color], width: int, height: int) -> List[Color]:
        """Mirror pixels horizontally."""
        result = list(pixels)
        for y in range(height):
            for x in range(width):
                src_x = width - 1 - x
                src_idx = y * width + src_x
                dst_idx = y * width + x
                if 0 <= src_idx < len(pixels) and 0 <= dst_idx < len(result):
                    result[dst_idx] = pixels[src_idx]
        return result
    
    def _mirror_vertical(self, pixels: List[Color], width: int, height: int) -> List[Color]:
        """Mirror pixels vertically."""
        result = list(pixels)
        for y in range(height):
            for x in range(width):
                src_y = height - 1 - y
                src_idx = src_y * width + x
                dst_idx = y * width + x
                if 0 <= src_idx < len(pixels) and 0 <= dst_idx < len(result):
                    result[dst_idx] = pixels[src_idx]
        return result
    
    def _wipe_pixels(self, pixels: List[Color], width: int, height: int, mode: str, wipe_pos: int) -> List[Color]:
        """Apply wipe effect - fade out pixels beyond wipe position."""
        grid = self._pixels_to_grid(pixels, width, height)
        mode_lower = mode.lower()
        
        direction = "horizontal"
        forward = True
        if "left" in mode_lower and "right" in mode_lower:
            direction = "horizontal"
            forward = "left" in mode_lower.split("to")[0].lower()
        elif "top" in mode_lower or "bottom" in mode_lower:
            direction = "vertical"
            forward = "top" in mode_lower.split("to")[0].lower()
        
        if direction == "horizontal":
            for y in range(height):
                row = grid[y]
                ordered = row if forward else list(reversed(row))
                wipe_pos_clamped = min(wipe_pos, width)
                for x in range(width):
                    fade = 1.0 if x < wipe_pos_clamped else max(0.0, 1.0 - (x - wipe_pos_clamped) / max(1, width - wipe_pos_clamped))
                    r, g, b = ordered[x]
                    ordered[x] = (int(r * fade), int(g * fade), int(b * fade))
                if not forward:
                    ordered.reverse()
                grid[y] = ordered
        else:
            ordered_rows = grid if forward else list(reversed(grid))
            wipe_pos_clamped = min(wipe_pos, height)
            for idx, row in enumerate(ordered_rows):
                fade = 1.0 if idx < wipe_pos_clamped else max(0.0, 1.0 - (idx - wipe_pos_clamped) / max(1, height - wipe_pos_clamped))
                ordered_rows[idx] = [(int(r * fade), int(g * fade), int(b * fade)) for r, g, b in row]
            if not forward:
                ordered_rows.reverse()
            grid = ordered_rows
        
        return self._grid_to_pixels(grid)
    
    def _reveal_pixels(self, pixels: List[Color], width: int, height: int, direction: str, reveal_pos: int) -> List[Color]:
        """Apply reveal effect - show pixels up to reveal position, rest transparent (black)."""
        grid = self._pixels_to_grid(pixels, width, height)
        direction_lower = direction.lower()
        
        mask_grid = [[(0, 0, 0) for _ in range(width)] for _ in range(height)]
        if direction_lower == "left":
            reveal_width = min(reveal_pos, width)
            for y in range(height):
                for x in range(reveal_width):
                    mask_grid[y][x] = grid[y][x]
        elif direction_lower == "right":
            reveal_width = min(reveal_pos, width)
            for y in range(height):
                for x in range(width - reveal_width, width):
                    mask_grid[y][x] = grid[y][x]
        elif direction_lower == "top":
            reveal_height = min(reveal_pos, height)
            for y in range(reveal_height):
                mask_grid[y] = list(grid[y])
        elif direction_lower == "bottom":
            reveal_height = min(reveal_pos, height)
            for y in range(height - reveal_height, height):
                mask_grid[y] = list(grid[y])
        else:
            return pixels
        
        return self._grid_to_pixels(mask_grid)
    
    def _bounce_pixels(self, pixels: List[Color], width: int, height: int, axis: str) -> List[Color]:
        """Apply bounce effect - flip pixels along axis."""
        grid = self._pixels_to_grid(pixels, width, height)
        axis_lower = axis.lower()
        
        if axis_lower == "horizontal":
            new_grid = [list(reversed(row)) for row in grid]
        else:  # vertical
            new_grid = list(reversed(grid))
        
        return self._grid_to_pixels(new_grid)
    
    def _colour_cycle_pixels(self, pixels: List[Color], mode: str) -> List[Color]:
        """Apply color cycle - shift RGB channels."""
        mode_lower = mode.lower()
        
        if mode_lower == "rgb":
            return [(g, b, r) for r, g, b in pixels]
        elif mode_lower == "ryb":
            return [(b, r, g) for r, g, b in pixels]
        else:
            return [(b, r, g) for r, g, b in pixels]
    
    def _radial_pixels(self, pixels: List[Color], width: int, height: int, type_str: str, step: int) -> List[Color]:
        """Apply radial effect - spiral or pulse based on distance from center."""
        grid = self._pixels_to_grid(pixels, width, height)
        type_str_lower = type_str.lower()
        
        center_x = width / 2.0
        center_y = height / 2.0
        max_dist = ((center_x) ** 2 + (center_y) ** 2) ** 0.5
        
        new_grid = [[(0, 0, 0) for _ in range(width)] for _ in range(height)]
        
        if type_str_lower == "spiral":
            # Spiral rotation - use step for progressive rotation
            angle_offset = step * 0.1  # Progressive rotation per step
            for y in range(height):
                for x in range(width):
                    dx = x - center_x
                    dy = y - center_y
                    angle = (dx ** 2 + dy ** 2) ** 0.5 * 0.5 + angle_offset
                    new_x = int(center_x + dx * 0.9 - dy * 0.1)
                    new_y = int(center_y + dy * 0.9 + dx * 0.1)
                    if 0 <= new_x < width and 0 <= new_y < height:
                        new_grid[new_y][new_x] = grid[y][x]
        elif type_str_lower == "pulse":
            # Pulse intensity based on distance and step
            pulse_phase = (step % 10) / 10.0  # 0-1 cycle over 10 frames
            for y in range(height):
                for x in range(width):
                    dx = x - center_x
                    dy = y - center_y
                    dist = (dx ** 2 + dy ** 2) ** 0.5
                    dist_factor = dist / max_dist if max_dist > 0 else 0
                    pulse_factor = 0.5 + 0.5 * (1.0 - abs(pulse_phase - 0.5) * 2)  # Pulse 0.5-1.0
                    factor = (1.0 - dist_factor * 0.5) * pulse_factor
                    r, g, b = grid[y][x]
                    new_grid[y][x] = (
                        int(r * factor),
                        int(g * factor),
                        int(b * factor)
                    )
        else:  # Default: no change
            return pixels
        
        return self._grid_to_pixels(new_grid)
    
    def render_frame(self, frame_index: int) -> List[Color]:
        """
        Canonical LMS-exact render function (single source of truth).
        
        This function produces pixel-for-pixel identical output to LED Matrix Studio.
        
        LMS-EXACT RENDER PIPELINE (for each layer, bottom to top):
        1. Sort tracks by z_index (order)
        2. Check layer active window (is_layer_active) - skip if outside window
        3. Check layer visibility (get_effective_visibility) - skip if hidden
        4. Get layer frame (get_frame) - skip if missing
        5. Start from base_pixels (immutable reference from layer_frame.pixels)
        6. Sort automation by ACTION_PRIORITY (fixed LMS order)
        7. Apply automation with local steps (get_action_step) - frame-relative
        8. Apply opacity as brightness scaling (apply_opacity) - no alpha blending
        9. Composite using black=transparent overwrite (no blend math)
        
        LMS RULES ENFORCED:
        - Automation is frame-relative (local step, not global frame_index)
        - Automation order is fixed (ACTION_PRIORITY, not user-defined)
        - Rotate always uses base pixels (never accumulates)
        - Opacity scales brightness only (no alpha blending)
        - Black (0,0,0) = transparent (overwrite-only compositing)
        - Layer window completely blocks automation (is_layer_active check)
        - Out-of-bounds pixels become black (no wrap/modulo)
        
        Args:
            frame_index: Frame index to render
            
        Returns:
            Composite pixel array (RGB tuples)
        """
        width = self._state.width()
        height = self._state.height()
        expected = width * height
        
        # Start with black background
        final = [(0, 0, 0)] * expected
        
        # Sort layers by order (bottom to top)
        sorted_tracks = sorted(self._layer_tracks, key=lambda t: t.order)
        
        for track in sorted_tracks:
            # Check layer active window (LMS: layer is fully inactive outside window)
            if not self.is_layer_active(track, frame_index):
                continue
            
            # Check layer visibility
            if not track.get_effective_visibility(frame_index):
                continue
            
            # Check group visibility
            if track.group_id and track.group_id in self._groups:
                group = self._groups[track.group_id]
                if not group.visible:
                    continue
            
            # Get base pixels and alpha
            layer_frame = track.get_frame(frame_index)
            if not layer_frame:
                # MISSING FRAME BEHAVIOR:
                # If LayerFrame doesn't exist for this frame_index, skip this layer entirely.
                # This is treated as fully transparent (no pixels from this layer).
                # Use get_or_create_frame() if you want to create frames with default values.
                continue
            
            # Get base pixels (immutable reference - LMS base-frame rule)
            base_pixels = list(layer_frame.pixels[:expected])
            if len(base_pixels) < expected:
                base_pixels += [(0, 0, 0)] * (expected - len(base_pixels))
            
            # Start from base pixels (LMS: always recompute from base, never accumulate)
            pixels = base_pixels
            
            # Apply layer automation (render-time, non-destructive)
            # Transform pixels based on automation actions (sorted by LMS priority)
            pixels = self._apply_layer_automation(
                track, frame_index, pixels, width, height
            )
            
            # Apply opacity as brightness scaling (LMS-style: no alpha blending)
            effective_opacity = track.get_effective_opacity(frame_index)
            pixels = self.apply_opacity(pixels, effective_opacity)
            
            # Composite using black=transparent overwrite (LMS compositing)
            # Black pixels (0,0,0) are transparent and don't overwrite lower layers
            for i, pixel in enumerate(pixels):
                if pixel != (0, 0, 0):
                    final[i] = pixel
        
        return final
    
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
        
        This updates the LayerFrame pixels and alpha for the specified layer track and frame.
        When a pixel is set, its alpha is set to 255 (fully opaque) unless explicitly set otherwise.
        """
        # Enforce edit context if available (Phase 1 Integration)
        try:
            from domain.edit_context import get_edit_context, assert_not_rendering
            # Only check if context is set (legacy calls might not set it yet)
            # This throws if we're in render mode (Rule R3)
            assert_not_rendering()
        except ImportError:
            pass
            
        if 0 <= layer_index < len(self._layer_tracks):
            track = self._layer_tracks[layer_index]
            layer_frame = track.get_or_create_frame(frame_index, width, height)
            
            idx = y * width + x
            if idx < len(layer_frame.pixels):
                layer_frame.pixels[idx] = colour or (0, 0, 0)
                # Ensure alpha exists and set to fully opaque for new/modified pixels
                layer_frame.ensure_alpha(len(layer_frame.pixels))
                if layer_frame.alpha:
                    layer_frame.alpha[idx] = 255
                # Sync frame from layers after pixel change
                self.sync_frame_from_layers(frame_index)
                self.pixel_changed.emit(frame_index, x, y, colour or (0, 0, 0))
                self.layers_changed.emit(frame_index)

    def replace_pixels(self, frame_index: int, pixels, layer_index: int = 0) -> None:
        """
        Replace pixels in a specific layer track at a specific frame.
        
        Note: Alpha channel is preserved if it exists, otherwise defaults to fully opaque (255).
        """
        # Enforce edit context if available (Phase 1 Integration)
        try:
            from domain.edit_context import get_edit_context, assert_not_rendering
            assert_not_rendering()
        except ImportError:
            pass

        if 0 <= layer_index < len(self._layer_tracks):
            track = self._layer_tracks[layer_index]
            width = self._state.width()
            height = self._state.height()
            layer_frame = track.get_or_create_frame(frame_index, width, height)
            layer_frame.pixels = list(pixels)
            # Ensure alpha channel matches pixel count (default to opaque)
            layer_frame.ensure_alpha(len(pixels))
            self.sync_frame_from_layers(frame_index)
            self.frame_pixels_changed.emit(frame_index)
            self.layers_changed.emit(frame_index)

    def import_gif_to_layer(self, frames_data: List[List[Tuple[int, int, int]]], layer_index: int = 0, start_frame: int = 0, duration_ms: Optional[int] = None) -> None:
        """
        Bulk import multiple frames (e.g. from a GIF) into a specific layer track.
        
        Args:
            frames_data: List of pixel lists (one per frame)
            layer_index: Target layer index
            start_frame: Frame index to start importing at
            duration_ms: Optional duration to set for all imported frames
        """
        if not (0 <= layer_index < len(self._layer_tracks)):
            return
            
        track = self._layer_tracks[layer_index]
        width = self._state.width()
        height = self._state.height()
        
        for i, pixels in enumerate(frames_data):
            frame_idx = start_frame + i
            layer_frame = track.get_or_create_frame(frame_idx, width, height)
            layer_frame.pixels = list(pixels)
            layer_frame.ensure_alpha(len(pixels))
            
            # Sync composite pattern frame
            self.sync_frame_from_layers(frame_idx)
            
            # Update duration if provided
            if duration_ms is not None and self._state.pattern():
                if frame_idx < len(self._state.pattern().frames):
                    self._state.pattern().frames[frame_idx].duration_ms = duration_ms
        
        self.frame_pixels_changed.emit(-1)
        self.layers_changed.emit(-1)

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
        """
        Update frame pixels from composite of all layers.
        
        NOTE: This method stores composite pixels back into pattern.frames[].
        This should only be called when explicitly needed (e.g., export, preview generation).
        For normal rendering, use render_frame() which derives pixels without storing.
        
        The composite pixels are derived, not stored, in the new architecture.
        This method exists for backward compatibility and export/preview use cases.
        """
        if not self._state.pattern() or frame_index >= len(self._state.pattern().frames):
            return
        
        # Use render_frame() to get composite pixels
        composite = self.render_frame(frame_index)
        self._state.pattern().frames[frame_index].pixels = composite
    
    def _update_frame_cache(self, frame_index: int) -> None:
        """
        Internal method to update frame cache (alias for sync_frame_from_layers).
        Only call when explicitly needed (export, preview).
        """
        self.sync_frame_from_layers(frame_index)

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
            
        return True

    # TIMELINE SYNC HANDLERS: React to FrameManager changes ---------------------

    def handle_frame_inserted(self, index: int, count: int = 1) -> None:
        """Shift layer data to account for inserted frames."""
        for track in self._layer_tracks:
            # 1. Shift frame dictionary
            new_frames = {}
            for f_idx, frame in track.frames.items():
                if f_idx >= index:
                    new_frames[f_idx + count] = frame
                else:
                    new_frames[f_idx] = frame
            track.frames = new_frames
            
            # 2. Shift automation timing
            for action in track.automation:
                if action.start_frame >= index:
                    action.start_frame += count
                if action.end_frame is not None and action.end_frame >= index:
                    action.end_frame += count
            
            # 3. Shift track timing window
            if track.start_frame is not None and track.start_frame >= index:
                track.start_frame += count
            if track.end_frame is not None and track.end_frame >= index:
                track.end_frame += count
                
            # 4. Shift legacy animations
            anim = self._animation_manager.get_animation(track.id)
            if anim:
                if anim.start_frame >= index:
                    anim.start_frame += count
                if anim.end_frame is not None and anim.end_frame >= index:
                    anim.end_frame += count
        
        self.layers_changed.emit(-1)

    def handle_frame_deleted(self, index: int, count: int = 1) -> None:
        """Shift layer data to account for deleted frames."""
        for track in self._layer_tracks:
            # 1. Shift frame dictionary
            new_frames = {}
            for f_idx, frame in track.frames.items():
                if f_idx < index:
                    new_frames[f_idx] = frame
                elif f_idx >= index + count:
                    new_frames[f_idx - count] = frame
                # Else: frame is in deleted range, discarded
            track.frames = new_frames
            
            # 2. Shift automation timing
            for action in track.automation:
                # If action starts after deleted range, shift back
                if action.start_frame >= index + count:
                    action.start_frame -= count
                # If action ends after deleted range, shift back
                if action.end_frame is not None and action.end_frame >= index + count:
                    action.end_frame -= count
                # Clip actions sticking into deleted range
                elif action.end_frame is not None and action.end_frame >= index:
                    action.end_frame = max(action.start_frame, index - 1)
            
            # 3. Shift track timing window
            if track.start_frame is not None and track.start_frame >= index + count:
                track.start_frame -= count
            if track.end_frame is not None and track.end_frame >= index + count:
                track.end_frame -= count
            
            # 4. Shift legacy animations
            anim = self._animation_manager.get_animation(track.id)
            if anim:
                if anim.start_frame >= index + count:
                    anim.start_frame -= count
                if anim.end_frame is not None and anim.end_frame >= index + count:
                    anim.end_frame -= count
        
        self.layers_changed.emit(-1)

    def handle_frame_duplicated(self, src_index: int, dest_index: int) -> None:
        """Handle duplication of a frame in the timeline."""
        # 1. First make room (shift everything after dest_index)
        self.handle_frame_inserted(dest_index)
        
        # 2. Figure out where our source is now (it may have shifted)
        actual_src = src_index if src_index < dest_index else src_index + 1
        
        # 3. Copy layer data from src to dest
        for track in self._layer_tracks:
            source_layer_frame = track.get_frame(actual_src)
            if source_layer_frame:
                track.set_frame(dest_index, source_layer_frame.copy())
        
        self.layers_changed.emit(dest_index)

    def handle_frame_moved(self, src: int, dest: int) -> None:
        """Handle movement of a frame in the timeline."""
        if src == dest:
            return
            
        for track in self._layer_tracks:
            # Capture the data
            frame_data = track.frames.pop(src, None)
            
            # Collect current items as a list of (index, frame)
            items = sorted(track.frames.items())
            
            # Temporary list for re-indexing
            # This logic mimics list.pop / list.insert
            temp_list = [None] * (max(indices) + 2 if (indices := track.frames.keys()) else dest + 1)
            for idx, frame in items:
                temp_list[idx] = frame
            
            # The popped item is already gone from items, but we held it in frame_data
            # Now insert into the virtual list at dest
            # (Note: this is simplified, better to just shift indices directly)
            
            new_frames = {}
            shifted_keys = []
            
            # Shift indices correctly:
            if src < dest:
                # Everything between src and dest moves back 1
                for f_idx, f_data in track.frames.items():
                    if src < f_idx <= dest:
                        new_frames[f_idx - 1] = f_data
                    elif f_idx > dest or f_idx < src:
                        new_frames[f_idx] = f_data
                if frame_data:
                    new_frames[dest] = frame_data
            else:
                # Everything between dest and src moves forward 1
                for f_idx, f_data in track.frames.items():
                    if dest <= f_idx < src:
                        new_frames[f_idx + 1] = f_data
                    elif f_idx > src or f_idx < dest:
                        new_frames[f_idx] = f_data
                if frame_data:
                    new_frames[dest] = frame_data
            
            track.frames = new_frames
        
        self.layers_changed.emit(-1)