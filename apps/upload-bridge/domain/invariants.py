"""
Runtime Invariants - Proof System

This module implements Phase 7 of the E2E fixing plan:
Runtime invariants that crash if isolation is violated.

These are HARD CHECKS that make violations impossible in development.
"""

from __future__ import annotations
from typing import Dict, Any, Set
import logging

logger = logging.getLogger(__name__)


class InvariantViolation(Exception):
    """Raised when a runtime invariant is violated."""
    pass


class LayerInvariants:
    """
    Runtime invariants for layer isolation.
    
    These checks PROVE that isolation is maintained.
    """
    
    @staticmethod
    def assert_single_layer_write(
        target_layer_id: str,
        active_layer_id: str
    ) -> None:
        """
        Invariant I1 - Single Write Target
        
        Only the active layer may be written to.
        
        Args:
            target_layer_id: Layer being targeted
            active_layer_id: Currently active layer
            
        Raises:
            InvariantViolation: If target != active
        """
        if target_layer_id != active_layer_id:
            raise InvariantViolation(
                f"INVARIANT I1 VIOLATED: Attempted to write to layer {target_layer_id}, "
                f"but active layer is {active_layer_id}"
            )
    
    @staticmethod
    def assert_no_cross_layer_mutation(
        before_snapshot: Dict[str, Any],
        after_snapshot: Dict[str, Any],
        active_layer_id: str
    ) -> None:
        """
        Invariant I2 - No Cross-Layer Frame Mutation
        
        Only the active layer's frames may change.
        
        Args:
            before_snapshot: Layer state before operation
            after_snapshot: Layer state after operation
            active_layer_id: ID of active layer
            
        Raises:
            InvariantViolation: If non-active layers changed
        """
        for layer_id, before_frames in before_snapshot.items():
            if layer_id == active_layer_id:
                continue  # Active layer is allowed to change
            
            after_frames = after_snapshot.get(layer_id, {})
            
            if before_frames != after_frames:
                raise InvariantViolation(
                    f"INVARIANT I2 VIOLATED: Layer {layer_id} was mutated, "
                    f"but active layer is {active_layer_id}"
                )
    
    @staticmethod
    def assert_no_implicit_frame_creation(
        before_frame_count: int,
        after_frame_count: int,
        expected_change: int = 0
    ) -> None:
        """
        Invariant I3 - No Implicit Frame Creation
        
        Frame count should only change via explicit create_frame() calls.
        
        Args:
            before_frame_count: Frame count before operation
            after_frame_count: Frame count after operation
            expected_change: Expected change (0 for no creation, 1 for create, -1 for delete)
            
        Raises:
            InvariantViolation: If frame count changed unexpectedly
        """
        actual_change = after_frame_count - before_frame_count
        
        if actual_change != expected_change:
            raise InvariantViolation(
                f"INVARIANT I3 VIOLATED: Frame count changed by {actual_change}, "
                f"expected {expected_change}"
            )
    
    @staticmethod
    def assert_render_readonly(
        before_snapshot: Dict[str, Any],
        after_snapshot: Dict[str, Any]
    ) -> None:
        """
        Invariant I4 - Render is Read-Only
        
        Rendering must never mutate any layer.
        
        Args:
            before_snapshot: All layer states before render
            after_snapshot: All layer states after render
            
        Raises:
            InvariantViolation: If any layer changed during render
        """
        if before_snapshot != after_snapshot:
            raise InvariantViolation(
                "INVARIANT I4 VIOLATED: Layer data was mutated during rendering"
            )


class InvariantChecker:
    """
    Automatic invariant checking wrapper.
    
    Use this to wrap operations and automatically verify invariants.
    """
    
    def __init__(self, layer_manager):
        self.layer_manager = layer_manager
        self._enabled = True  # Can be disabled in production
    
    def enable(self):
        """Enable invariant checking."""
        self._enabled = True
    
    def disable(self):
        """Disable invariant checking (for production)."""
        self._enabled = False
    
    def snapshot_all_layers(self) -> Dict[str, Dict]:
        """
        Take a snapshot of all layer frame data.
        
        Returns:
            Dict mapping layer_id -> frame data
        """
        snapshot = {}
        for track in self.layer_manager.get_layer_tracks():
            snapshot[track.id] = {
                idx: {
                    'pixels': list(frame.pixels),
                    'alpha': list(frame.alpha) if frame.alpha else None
                }
                for idx, frame in track.frames.items()
            }
        return snapshot
    
    def check_edit_operation(
        self,
        operation_func,
        active_layer_id: str,
        *args,
        **kwargs
    ):
        """
        Wrap an edit operation with invariant checks.
        
        Args:
            operation_func: Function to execute
            active_layer_id: ID of active layer
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Result of operation_func
            
        Raises:
            InvariantViolation: If invariants violated
        """
        if not self._enabled:
            return operation_func(*args, **kwargs)
        
        # Take snapshot before
        before = self.snapshot_all_layers()
        
        # Execute operation
        result = operation_func(*args, **kwargs)
        
        # Take snapshot after
        after = self.snapshot_all_layers()
        
        # Check invariant I2 (no cross-layer mutation)
        LayerInvariants.assert_no_cross_layer_mutation(
            before, after, active_layer_id
        )
        
        logger.debug(f"✓ Invariant check passed for operation on layer {active_layer_id}")
        
        return result
    
    def check_render_operation(
        self,
        render_func,
        *args,
        **kwargs
    ):
        """
        Wrap a render operation with invariant checks.
        
        Args:
            render_func: Render function to execute
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Result of render_func
            
        Raises:
            InvariantViolation: If rendering mutated data
        """
        if not self._enabled:
            return render_func(*args, **kwargs)
        
        # Take snapshot before
        before = self.snapshot_all_layers()
        
        # Execute render
        result = render_func(*args, **kwargs)
        
        # Take snapshot after
        after = self.snapshot_all_layers()
        
        # Check invariant I4 (render is read-only)
        LayerInvariants.assert_render_readonly(before, after)
        
        logger.debug("✓ Render invariant check passed (no mutations)")
        
        return result


# Global invariant checker (initialized by LayerManager)
_global_checker: InvariantChecker = None


def set_global_checker(checker: InvariantChecker):
    """Set the global invariant checker."""
    global _global_checker
    _global_checker = checker


def get_global_checker() -> InvariantChecker:
    """Get the global invariant checker."""
    return _global_checker


def check_edit(operation_func, active_layer_id: str, *args, **kwargs):
    """Convenience function to check edit operation."""
    if _global_checker:
        return _global_checker.check_edit_operation(
            operation_func, active_layer_id, *args, **kwargs
        )
    return operation_func(*args, **kwargs)


def check_render(render_func, *args, **kwargs):
    """Convenience function to check render operation."""
    if _global_checker:
        return _global_checker.check_render_operation(
            render_func, *args, **kwargs
        )
    return render_func(*args, **kwargs)
