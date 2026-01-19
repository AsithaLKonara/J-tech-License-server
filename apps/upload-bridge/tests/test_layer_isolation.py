"""
Layer Isolation Tests - E2E Verification

This module implements Phase 8 of the E2E fixing plan:
Automated tests that PROVE layer isolation.

These tests will FAIL if isolation is violated.
"""

import pytest
from typing import List, Tuple
from domain.edit_context import EditContext, set_edit_context
from domain.frame_operations import create_frame, get_frame_for_edit
from domain.layers import LayerTrack, LayerFrame


Color = Tuple[int, int, int]


def create_test_layer(name: str, width: int, height: int) -> LayerTrack:
    """Create a test layer with one frame."""
    track = LayerTrack(name=name)
    # Manually create first frame
    track.frames[0] = LayerFrame(
        pixels=[(0, 0, 0)] * (width * height),
        alpha=[255] * (width * height)
    )
    return track


def snapshot_layer_frames(layer: LayerTrack) -> dict:
    """Take a snapshot of all frames in a layer."""
    return {
        idx: {
            'pixels': list(frame.pixels),
            'alpha': list(frame.alpha) if frame.alpha else None
        }
        for idx, frame in layer.frames.items()
    }


def assert_layers_identical(before: dict, after: dict, layer_name: str):
    """Assert that layer snapshots are identical."""
    assert before == after, f"Layer '{layer_name}' was modified when it shouldn't have been"


class TestEditIsolation:
    """Test 1 - Edit Isolation"""
    
    def test_edit_only_affects_active_layer(self):
        """
        Given 3 layers
        When editing Layer 2 Frame 5
        Then Layer 1 and Layer 3 are byte-identical
        """
        width, height = 12, 6
        
        # Create 3 layers
        layer1 = create_test_layer("Layer 1", width, height)
        layer2 = create_test_layer("Layer 2", width, height)
        layer3 = create_test_layer("Layer 3", width, height)
        
        # Take snapshots
        layer1_before = snapshot_layer_frames(layer1)
        layer3_before = snapshot_layer_frames(layer3)
        
        # Create edit context for Layer 2, Frame 5
        ctx = EditContext(
            active_layer_id=layer2.id,
            active_frame_index=5,
            pattern_width=width,
            pattern_height=height
        )
        set_edit_context(ctx)
        
        # Create frame 5 in layer 2
        create_frame(ctx, layer2)
        
        # Edit layer 2
        frame = get_frame_for_edit(ctx, layer2)
        frame.pixels[0] = (255, 0, 0)  # Red pixel
        
        # Take snapshots after
        layer1_after = snapshot_layer_frames(layer1)
        layer3_after = snapshot_layer_frames(layer3)
        
        # PROOF: Layer 1 and 3 are unchanged
        assert_layers_identical(layer1_before, layer1_after, "Layer 1")
        assert_layers_identical(layer3_before, layer3_after, "Layer 3")
        
        # Layer 2 should have changed
        assert layer2.frames[5].pixels[0] == (255, 0, 0)


class TestFrameNonCreation:
    """Test 2 - Frame Non-Creation"""
    
    def test_edit_does_not_create_frames_in_other_layers(self):
        """
        Edit Layer 1 Frame 10
        Layer 2 must NOT gain frame 10
        """
        width, height = 12, 6
        
        layer1 = create_test_layer("Layer 1", width, height)
        layer2 = create_test_layer("Layer 2", width, height)
        
        # Record initial frame counts
        layer2_frame_count_before = len(layer2.frames)
        
        # Create edit context for Layer 1, Frame 10
        ctx = EditContext(
            active_layer_id=layer1.id,
            active_frame_index=10,
            pattern_width=width,
            pattern_height=height
        )
        set_edit_context(ctx)
        
        # Create and edit frame 10 in layer 1
        create_frame(ctx, layer1)
        frame = get_frame_for_edit(ctx, layer1)
        frame.pixels[0] = (0, 255, 0)  # Green pixel
        
        # PROOF: Layer 2 frame count unchanged
        layer2_frame_count_after = len(layer2.frames)
        assert layer2_frame_count_after == layer2_frame_count_before
        
        # PROOF: Frame 10 does NOT exist in layer 2
        assert 10 not in layer2.frames


class TestLayerSwitchSafety:
    """Test 4 - Layer Switch Safety"""
    
    def test_layer_switch_preserves_previous_layer(self):
        """
        Edit Layer A
        Switch to Layer B
        Edit
        Layer A remains unchanged
        """
        width, height = 12, 6
        
        layerA = create_test_layer("Layer A", width, height)
        layerB = create_test_layer("Layer B", width, height)
        
        # Edit Layer A
        ctx_a = EditContext(
            active_layer_id=layerA.id,
            active_frame_index=0,
            pattern_width=width,
            pattern_height=height
        )
        set_edit_context(ctx_a)
        
        frame_a = get_frame_for_edit(ctx_a, layerA)
        frame_a.pixels[0] = (255, 0, 0)  # Red
        
        # Take snapshot of Layer A
        layerA_snapshot = snapshot_layer_frames(layerA)
        
        # Switch to Layer B
        ctx_b = EditContext(
            active_layer_id=layerB.id,
            active_frame_index=0,
            pattern_width=width,
            pattern_height=height
        )
        set_edit_context(ctx_b)
        
        # Edit Layer B
        frame_b = get_frame_for_edit(ctx_b, layerB)
        frame_b.pixels[0] = (0, 0, 255)  # Blue
        
        # PROOF: Layer A unchanged
        layerA_after = snapshot_layer_frames(layerA)
        assert_layers_identical(layerA_snapshot, layerA_after, "Layer A")


class TestContextValidation:
    """Test EditContext validation"""
    
    def test_cannot_edit_wrong_layer(self):
        """
        Attempting to edit a different layer than the active one
        should raise an AssertionError
        """
        width, height = 12, 6
        
        layer1 = create_test_layer("Layer 1", width, height)
        layer2 = create_test_layer("Layer 2", width, height)
        
        # Set context for Layer 1
        ctx = EditContext(
            active_layer_id=layer1.id,
            active_frame_index=0,
            pattern_width=width,
            pattern_height=height
        )
        set_edit_context(ctx)
        
        # Attempting to edit Layer 2 should fail
        with pytest.raises(AssertionError, match="ISOLATION VIOLATION"):
            get_frame_for_edit(ctx, layer2)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
