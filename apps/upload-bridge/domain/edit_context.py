"""
Edit Context - Single Source of Truth for Layer Editing

This module enforces strict layer isolation by providing a single,
authoritative context for all edit operations.

RULES ENFORCED:
- R1: Only the active layer may be mutated
- R2: Frames never auto-create in any layer
- R3: Compositing and automation are read-only operations
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class EditContext:
    """
    Single authoritative edit context.
    
    This context represents the ONLY valid target for mutations.
    All edit operations must accept and validate this context.
    
    Attributes:
        active_layer_id: UUID of the layer being edited
        active_frame_index: Frame index being edited
        pattern_width: Matrix width (for validation)
        pattern_height: Matrix height (for validation)
    """
    active_layer_id: str
    active_frame_index: int
    pattern_width: int
    pattern_height: int
    
    def validate(self) -> None:
        """
        Validate edit context.
        
        Raises:
            ValueError: If context is invalid
        """
        if not self.active_layer_id:
            raise ValueError("EditContext: active_layer_id cannot be empty")
        if self.active_frame_index < 0:
            raise ValueError(f"EditContext: active_frame_index must be >= 0, got {self.active_frame_index}")
        if self.pattern_width <= 0 or self.pattern_height <= 0:
            raise ValueError(f"EditContext: invalid pattern dimensions {self.pattern_width}x{self.pattern_height}")
    
    def assert_layer_match(self, target_layer_id: str) -> None:
        """
        Assert that target layer matches active layer.
        
        This is the core enforcement of Rule R1.
        
        Args:
            target_layer_id: Layer ID being targeted
            
        Raises:
            AssertionError: If target doesn't match active layer
        """
        assert target_layer_id == self.active_layer_id, \
            f"ISOLATION VIOLATION: Attempted to edit layer {target_layer_id}, but active layer is {self.active_layer_id}"
    
    def assert_frame_match(self, target_frame_index: int) -> None:
        """
        Assert that target frame matches active frame.
        
        Args:
            target_frame_index: Frame index being targeted
            
        Raises:
            AssertionError: If target doesn't match active frame
        """
        assert target_frame_index == self.active_frame_index, \
            f"ISOLATION VIOLATION: Attempted to edit frame {target_frame_index}, but active frame is {self.active_frame_index}"


class EditContextManager:
    """
    Manages the global edit context.
    
    This ensures there is always a single, authoritative edit context
    that all operations must respect.
    """
    
    def __init__(self):
        self._context: Optional[EditContext] = None
        self._is_rendering: bool = False
    
    def set_context(self, context: EditContext) -> None:
        """Set the active edit context."""
        context.validate()
        self._context = context
    
    def get_context(self) -> EditContext:
        """
        Get the current edit context.
        
        Returns:
            Current EditContext
            
        Raises:
            RuntimeError: If no context is set
        """
        if self._context is None:
            raise RuntimeError("No edit context set. Cannot perform edit operations.")
        return self._context
    
    def enter_render_mode(self) -> None:
        """
        Enter read-only render mode.
        
        While in render mode, edit operations are forbidden.
        """
        self._is_rendering = True
    
    def exit_render_mode(self) -> None:
        """Exit render mode."""
        self._is_rendering = False
    
    def assert_not_rendering(self) -> None:
        """
        Assert that we are not in render mode.
        
        Raises:
            AssertionError: If currently rendering
        """
        assert not self._is_rendering, \
            "ISOLATION VIOLATION: Cannot perform edit operations during rendering"
    
    def is_rendering(self) -> bool:
        """Check if currently in render mode."""
        return self._is_rendering


# Global edit context manager
_global_context_manager = EditContextManager()


def get_edit_context() -> EditContext:
    """Get the global edit context."""
    return _global_context_manager.get_context()


def set_edit_context(context: EditContext) -> None:
    """Set the global edit context."""
    _global_context_manager.set_context(context)


def enter_render_mode() -> None:
    """Enter read-only render mode."""
    _global_context_manager.enter_render_mode()


def exit_render_mode() -> None:
    """Exit render mode."""
    _global_context_manager.exit_render_mode()


def assert_not_rendering() -> None:
    """Assert not in render mode."""
    _global_context_manager.assert_not_rendering()


def is_rendering() -> bool:
    """Check if in render mode."""
    return _global_context_manager.is_rendering()
