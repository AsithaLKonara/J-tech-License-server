from __future__ import annotations

import pytest

from domain.layers import LayerManager
from domain.pattern_state import PatternState


def test_apply_pixel_updates_frame(layer_manager: LayerManager, pattern_state: PatternState):
    width = pattern_state.width()
    height = pattern_state.height()
    layer_manager.apply_pixel(0, 0, 0, (10, 20, 30), width, height)

    frame = pattern_state.frames()[0]
    assert frame.pixels[0] == (10, 20, 30)


def test_resize_pixels_pads_missing(layer_manager: LayerManager, pattern_state: PatternState):
    layer_manager.resize_pixels(3, 3)
    frame = pattern_state.frames()[0]
    assert len(frame.pixels) == 9
    assert frame.pixels[-1] == (0, 0, 0)


def test_are_layers_synced_initial_state(layer_manager: LayerManager, pattern_state: PatternState):
    """Test that layers are initially synced with frame."""
    frame_index = 0
    assert layer_manager.are_layers_synced(frame_index) is True


def test_are_layers_synced_after_frame_modification(layer_manager: LayerManager, pattern_state: PatternState):
    """Test that layers are detected as out of sync after frame modification."""
    frame_index = 0
    frame = pattern_state.frames()[frame_index]
    
    # Initially synced
    assert layer_manager.are_layers_synced(frame_index) is True
    
    # Modify frame pixels directly (simulating automation)
    original_pixel = frame.pixels[0]
    frame.pixels[0] = (255, 255, 255)
    
    # Should be out of sync now
    assert layer_manager.are_layers_synced(frame_index) is False


def test_are_layers_synced_after_sync(layer_manager: LayerManager, pattern_state: PatternState):
    """Test that layers are synced after calling sync_frame_from_layers."""
    frame_index = 0
    frame = pattern_state.frames()[frame_index]
    
    # Modify frame pixels
    frame.pixels[0] = (255, 255, 255)
    
    # Sync layers from frame
    layer_manager.sync_frame_from_layers(frame_index)
    
    # Should be synced now
    assert layer_manager.are_layers_synced(frame_index) is True


def test_copy_layer_to_frames(layer_manager: LayerManager, pattern_state: PatternState):
    """Test copying a layer to multiple frames."""
    # Ensure we have at least 3 frames
    while pattern_state.frame_count() < 3:
        pattern_state.add_frame()
    
    source_frame = 0
    target_frames = [1, 2]
    
    # Add a custom layer to source frame
    source_layer = layer_manager.add_layer(source_frame, "Custom Layer")
    
    # Set some pixels on this layer
    test_color = (100, 150, 200)
    width = pattern_state.width()
    height = pattern_state.height()
    pixels = [test_color] * (width * height)
    layer_manager.replace_pixels(source_frame, pixels, source_layer)
    
    # Copy layer to target frames
    layer_manager.copy_layer_to_frames(source_frame, source_layer, target_frames)
    
    # Verify layers exist in target frames
    frame1_layers = layer_manager.get_layers(1)
    frame2_layers = layer_manager.get_layers(2)
    
    # Check that target frames have the copied layer
    assert any(layer.name == "Custom Layer" for layer in frame1_layers)
    assert any(layer.name == "Custom Layer" for layer in frame2_layers)
    
    # Verify pixels were copied
    frame1_layer = next((l for l in frame1_layers if l.name == "Custom Layer"), None)
    frame2_layer = next((l for l in frame2_layers if l.name == "Custom Layer"), None)
    
    assert frame1_layer is not None
    assert frame2_layer is not None
    assert frame1_layer.pixels[0] == test_color
    assert frame2_layer.pixels[0] == test_color


def test_automation_layer_naming(layer_manager: LayerManager, pattern_state: PatternState):
    """Test that automation layers can be created with 'Auto:' prefix."""
    frame_index = 0
    
    # Create automation layers
    layer1 = layer_manager.add_layer(frame_index, "Auto: Scroll Left")
    layer2 = layer_manager.add_layer(frame_index, "Auto: Rotate 90")
    
    layers = layer_manager.get_layers(frame_index)
    
    assert layers[layer1].name.startswith("Auto:")
    assert layers[layer2].name.startswith("Auto:")
    assert layers[layer1].name == "Auto: Scroll Left"
    assert layers[layer2].name == "Auto: Rotate 90"


def test_multiple_automation_layers(layer_manager: LayerManager, pattern_state: PatternState):
    """Test that multiple automation layers can coexist."""
    frame_index = 0
    
    # Create multiple automation layers
    layer1 = layer_manager.add_layer(frame_index, "Auto: Scroll Left")
    layer2 = layer_manager.add_layer(frame_index, "Auto: Rotate 90")
    layer3 = layer_manager.add_layer(frame_index, "Auto: Mirror X")
    
    layers = layer_manager.get_layers(frame_index)
    auto_layers = [l for l in layers if l.name.startswith("Auto:")]
    
    assert len(auto_layers) == 3
    assert len(layers) >= 4  # At least 1 default + 3 automation layers
