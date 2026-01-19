"""
Render Pipeline - Read-Only Compositing System

This module implements Phase 2 of the E2E fixing plan:
Hard wall between edit-time and render-time.

RULES:
- Rendering is ALWAYS read-only
- No LayerTrack mutations during render
- No LayerFrame creation during render
- Output lives only in memory
"""

from __future__ import annotations
from typing import List, Tuple, Optional
from dataclasses import dataclass
from domain.edit_context import enter_render_mode, exit_render_mode, is_rendering

Color = Tuple[int, int, int]


@dataclass
class PixelBuffer:
    """
    Immutable pixel buffer for render output.
    
    This is the ONLY output from rendering.
    It never writes back to layer data.
    """
    pixels: List[Color]
    width: int
    height: int
    
    def __post_init__(self):
        expected = self.width * self.height
        if len(self.pixels) != expected:
            raise ValueError(f"PixelBuffer: expected {expected} pixels, got {len(self.pixels)}")
    
    def copy(self) -> 'PixelBuffer':
        """Create a copy of this buffer."""
        return PixelBuffer(
            pixels=list(self.pixels),
            width=self.width,
            height=self.height
        )


class RenderPipeline:
    """
    Read-only rendering pipeline.
    
    This class enforces that rendering never mutates layer data.
    All operations are pure functions.
    """
    
    @staticmethod
    def render_composite_frame(
        layer_tracks: List,
        frame_index: int,
        width: int,
        height: int,
        blend_function
    ) -> PixelBuffer:
        """
        Render a composite frame from all layers.
        
        This is a PURE FUNCTION:
        - No layer mutations
        - No frame creation
        - Output only in memory
        
        Args:
            layer_tracks: List of LayerTrack objects
            frame_index: Frame to render
            width: Matrix width
            height: Matrix height
            blend_function: Function to blend pixels
            
        Returns:
            PixelBuffer with composite result
            
        Raises:
            AssertionError: If called during edit mode
        """
        # CRITICAL: Enter render mode (forbids edits)
        enter_render_mode()
        
        try:
            # Start with black background
            composite = [(0, 0, 0)] * (width * height)
            
            # Sort layers by z_index (bottom to top)
            sorted_layers = sorted(layer_tracks, key=lambda t: t.z_index)
            
            for track in sorted_layers:
                # Check if layer is active at this frame
                if not RenderPipeline._is_layer_active(track, frame_index):
                    continue
                
                # Get frame (READ ONLY - no creation)
                layer_frame = track.frames.get(frame_index)
                if layer_frame is None:
                    continue  # Missing frame = transparent
                
                # Get effective visibility
                visible = layer_frame.visible if layer_frame.visible is not None else track.visible
                if not visible:
                    continue
                
                # Get effective opacity
                opacity = layer_frame.opacity if layer_frame.opacity is not None else track.opacity
                
                # Blend this layer onto composite
                composite = blend_function(
                    bottom=composite,
                    top=layer_frame.pixels,
                    top_alpha=layer_frame.alpha,
                    blend_mode=track.blend_mode,
                    opacity=opacity
                )
            
            return PixelBuffer(pixels=composite, width=width, height=height)
            
        finally:
            # CRITICAL: Exit render mode
            exit_render_mode()
    
    @staticmethod
    def _is_layer_active(track, frame_index: int) -> bool:
        """
        Check if layer is active at frame (read-only).
        
        Args:
            track: LayerTrack to check
            frame_index: Frame index
            
        Returns:
            True if layer is active
        """
        if track.start_frame is not None and frame_index < track.start_frame:
            return False
        if track.end_frame is not None and frame_index > track.end_frame:
            return False
        return True
    
    @staticmethod
    def apply_automation_readonly(
        pixels: List[Color],
        automation_actions: List,
        frame_index: int,
        width: int,
        height: int,
        transform_function
    ) -> List[Color]:
        """
        Apply automation as a pure function.
        
        This NEVER mutates the input pixels.
        
        Args:
            pixels: Source pixels (not modified)
            automation_actions: List of automation actions
            frame_index: Current frame
            width: Matrix width
            height: Matrix height
            transform_function: Function to apply transformations
            
        Returns:
            New pixel array with transformations applied
        """
        assert is_rendering(), "Automation should only be applied during rendering"
        
        # Start with a copy (never mutate input)
        result = list(pixels)
        
        # Apply each automation action
        for action in automation_actions:
            result = transform_function(result, action, frame_index, width, height)
        
        return result


def assert_render_mode() -> None:
    """
    Assert that we are in render mode.
    
    Use this in functions that should ONLY be called during rendering.
    
    Raises:
        AssertionError: If not in render mode
    """
    assert is_rendering(), \
        "ISOLATION VIOLATION: This function can only be called during rendering"


def assert_edit_mode() -> None:
    """
    Assert that we are NOT in render mode.
    
    Use this in functions that perform edits.
    
    Raises:
        AssertionError: If in render mode
    """
    assert not is_rendering(), \
        "ISOLATION VIOLATION: Cannot perform edits during rendering"
