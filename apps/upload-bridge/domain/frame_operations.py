"""
Frame Operations - Explicit Frame Management

This module implements Phase 3 of the E2E fixing plan:
Frame creation becomes explicit only.

RULES:
- Frames are NEVER auto-created
- Frame creation requires explicit API call
- Frame creation validates EditContext
- All frame access checks for existence
"""

from __future__ import annotations
from typing import Optional
from domain.edit_context import EditContext, assert_not_rendering


class FrameAlreadyExistsError(Exception):
    """Raised when attempting to create a frame that already exists."""
    pass


class FrameNotFoundError(Exception):
    """Raised when attempting to access a non-existent frame."""
    pass


class FrameOperations:
    """
    Explicit frame management operations.
    
    This class enforces that frames are never implicitly created.
    """
    
    @staticmethod
    def create_frame(
        ctx: EditContext,
        layer_track,
        initial_pixels: Optional[list] = None
    ) -> None:
        """
        Explicitly create a new frame in the active layer.
        
        This is the ONLY way to create frames.
        
        Args:
            ctx: Edit context (validates active layer/frame)
            layer_track: LayerTrack to create frame in
            initial_pixels: Optional initial pixel data
            
        Raises:
            FrameAlreadyExistsError: If frame already exists
            AssertionError: If layer doesn't match context
        """
        # CRITICAL: Validate we're editing the right layer
        ctx.assert_layer_match(layer_track.id)
        
        # CRITICAL: Cannot create frames during rendering
        assert_not_rendering()
        
        # Check if frame already exists
        if ctx.active_frame_index in layer_track.frames:
            raise FrameAlreadyExistsError(
                f"Frame {ctx.active_frame_index} already exists in layer {layer_track.name}"
            )
        
        # Import LayerFrame here to avoid circular dependency
        from domain.layers import LayerFrame
        
        # Create frame with explicit pixel data
        pixel_count = ctx.pattern_width * ctx.pattern_height
        if initial_pixels is None:
            initial_pixels = [(0, 0, 0)] * pixel_count
        
        # Create with fully opaque alpha
        initial_alpha = [255] * pixel_count
        
        layer_track.frames[ctx.active_frame_index] = LayerFrame(
            pixels=initial_pixels,
            alpha=initial_alpha
        )
    
    @staticmethod
    def get_frame_for_edit(
        ctx: EditContext,
        layer_track
    ):
        """
        Get a frame for editing.
        
        This enforces that the frame must already exist.
        
        Args:
            ctx: Edit context
            layer_track: LayerTrack to get frame from
            
        Returns:
            LayerFrame
            
        Raises:
            FrameNotFoundError: If frame doesn't exist
            AssertionError: If layer doesn't match context
        """
        # CRITICAL: Validate we're editing the right layer
        ctx.assert_layer_match(layer_track.id)
        
        # CRITICAL: Cannot edit during rendering
        assert_not_rendering()
        
        # Get frame (no auto-creation)
        frame = layer_track.frames.get(ctx.active_frame_index)
        
        if frame is None:
            raise FrameNotFoundError(
                f"Frame {ctx.active_frame_index} does not exist in layer {layer_track.name}. "
                f"Use create_frame() to create it first."
            )
        
        return frame
    
    @staticmethod
    def get_frame_for_read(
        layer_track,
        frame_index: int
    ):
        """
        Get a frame for read-only access.
        
        This can be used during rendering.
        Returns None if frame doesn't exist.
        
        Args:
            layer_track: LayerTrack to read from
            frame_index: Frame index
            
        Returns:
            LayerFrame or None
        """
        return layer_track.frames.get(frame_index)
    
    @staticmethod
    def delete_frame(
        ctx: EditContext,
        layer_track
    ) -> None:
        """
        Explicitly delete a frame from the active layer.
        
        Args:
            ctx: Edit context
            layer_track: LayerTrack to delete from
            
        Raises:
            FrameNotFoundError: If frame doesn't exist
            AssertionError: If layer doesn't match context
        """
        # CRITICAL: Validate we're editing the right layer
        ctx.assert_layer_match(layer_track.id)
        
        # CRITICAL: Cannot delete during rendering
        assert_not_rendering()
        
        if ctx.active_frame_index not in layer_track.frames:
            raise FrameNotFoundError(
                f"Frame {ctx.active_frame_index} does not exist in layer {layer_track.name}"
            )
        
        del layer_track.frames[ctx.active_frame_index]
    
    @staticmethod
    def frame_exists(
        layer_track,
        frame_index: int
    ) -> bool:
        """
        Check if a frame exists (read-only).
        
        Args:
            layer_track: LayerTrack to check
            frame_index: Frame index
            
        Returns:
            True if frame exists
        """
        return frame_index in layer_track.frames
    
    @staticmethod
    def get_frame_count(layer_track) -> int:
        """
        Get number of frames in layer (read-only).
        
        Args:
            layer_track: LayerTrack to count
            
        Returns:
            Number of frames
        """
        return len(layer_track.frames)


# Convenience functions

def create_frame(ctx: EditContext, layer_track, initial_pixels=None) -> None:
    """Create a frame in the active layer."""
    FrameOperations.create_frame(ctx, layer_track, initial_pixels)


def get_frame_for_edit(ctx: EditContext, layer_track):
    """Get frame for editing (must exist)."""
    return FrameOperations.get_frame_for_edit(ctx, layer_track)


def get_frame_for_read(layer_track, frame_index: int):
    """Get frame for reading (returns None if missing)."""
    return FrameOperations.get_frame_for_read(layer_track, frame_index)


def delete_frame(ctx: EditContext, layer_track) -> None:
    """Delete frame from active layer."""
    FrameOperations.delete_frame(ctx, layer_track)


def frame_exists(layer_track, frame_index: int) -> bool:
    """Check if frame exists."""
    return FrameOperations.frame_exists(layer_track, frame_index)
