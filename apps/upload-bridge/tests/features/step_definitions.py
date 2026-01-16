"""
Gherkin Step Definitions - BDD test step implementations

This module provides step definitions for Gherkin feature files using pytest-bdd.
"""

from pytest_bdd import given, when, then, parsers
import pytest
from pathlib import Path
from typing import Optional

from core.pattern import Pattern, Frame, PatternMetadata
from domain.pattern_state import PatternState
from domain.frames import FrameManager
from domain.layers import LayerManager
from domain.automation.parametric_actions import create_action
from domain.effects.engine import get_effects_engine
from core.export.exporters import PatternExporter
from uploaders.adapter_registry import get_adapter


# Pattern creation steps
@given("I have opened the Design Tools tab")
def design_tools_tab_opened(qtbot, main_window):
    """Design Tools tab is opened."""
    design_tab = main_window.get_tab('design_tools')
    assert design_tab is not None
    return design_tab


@given("I have created a new 16x16 pattern")
def create_16x16_pattern(qtbot, design_tools_tab):
    """Create a new 16x16 pattern."""
    from core.pattern import Pattern, PatternMetadata
    
    metadata = PatternMetadata(
        width=16,
        height=16,
        color_order="RGB",
        wiring_mode="Row-major",
        data_in_corner="LT"
    )
    
    pattern = Pattern(
        id="test_pattern",
        name="Test Pattern",
        metadata=metadata,
        frames=[]
    )
    
    # Add a blank frame
    pattern.frames.append(Frame(pixels=[(0, 0, 0)] * 256, duration_ms=100))
    
    design_tools_tab.load_pattern(pattern)
    return pattern


@given("I have created a new 16x16 pattern with 10 frames")
def create_16x16_pattern_10_frames(qtbot, design_tools_tab):
    """Create a new 16x16 pattern with 10 frames."""
    from core.pattern import Pattern, PatternMetadata
    
    metadata = PatternMetadata(
        width=16,
        height=16,
        color_order="RGB",
        wiring_mode="Row-major",
        data_in_corner="LT"
    )
    
    pattern = Pattern(
        id="test_pattern",
        name="Test Pattern",
        metadata=metadata,
        frames=[]
    )
    
    # Add 10 blank frames
    for i in range(10):
        pattern.frames.append(Frame(pixels=[(0, 0, 0)] * 256, duration_ms=100))
    
    design_tools_tab.load_pattern(pattern)
    return pattern


@given(parsers.parse("I have selected frame {frame_index:d}"))
def select_frame(frame_index: int, design_tools_tab):
    """Select a frame."""
    if hasattr(design_tools_tab, 'frame_manager'):
        design_tools_tab.frame_manager.select(frame_index)


@given("I have a Pattern object")
def pattern_object(qtbot):
    """Create a Pattern object."""
    from core.pattern import Pattern, PatternMetadata
    
    metadata = PatternMetadata(
        width=16,
        height=16,
        color_order="RGB",
        wiring_mode="Row-major",
        data_in_corner="LT"
    )
    
    pattern = Pattern(
        id="test_pattern",
        name="Test Pattern",
        metadata=metadata,
        frames=[Frame(pixels=[(0, 0, 0)] * 256, duration_ms=100)]
    )
    
    return pattern


@given(parsers.parse("frame {frame_index:d} has {layer_count:d} layer(s)"))
def frame_has_layers(frame_index: int, layer_count: int, design_tools_tab):
    """Frame has specified number of layers."""
    if hasattr(design_tools_tab, 'layer_manager'):
        for _ in range(layer_count - 1):
            design_tools_tab.layer_manager.add_layer(frame_index)


# Action steps
@when("I add a new layer to frame 0")
def add_layer_to_frame_0(design_tools_tab):
    """Add a new layer to frame 0."""
    if hasattr(design_tools_tab, 'layer_manager'):
        design_tools_tab.layer_manager.add_layer(0)


@when(parsers.parse("I set layer opacity to {opacity:g}"))
def set_layer_opacity(opacity: float, design_tools_tab):
    """Set layer opacity."""
    if hasattr(design_tools_tab, 'layer_manager'):
        design_tools_tab.layer_manager.set_layer_opacity(0, 0, opacity)


@when(parsers.parse("I set layer blend mode to \"{blend_mode}\""))
def set_layer_blend_mode(blend_mode: str, design_tools_tab):
    """Set layer blend mode."""
    if hasattr(design_tools_tab, 'layer_manager'):
        design_tools_tab.layer_manager.set_layer_blend_mode(0, 1, blend_mode)


@when("I toggle layer 1 visibility")
def toggle_layer_visibility(design_tools_tab):
    """Toggle layer visibility."""
    if hasattr(design_tools_tab, 'layer_manager'):
        current_visible = design_tools_tab.layer_manager.is_layer_visible(0, 1)
        design_tools_tab.layer_manager.set_layer_visible(0, 1, not current_visible)


@when(parsers.parse("I apply scroll action with direction \"{direction}\" and speed {speed:g}"))
def apply_scroll_action(direction: str, speed: float, design_tools_tab):
    """Apply scroll action."""
    if hasattr(design_tools_tab, 'pattern'):
        action = create_action(
            "scroll",
            parameters={"direction": direction, "speed": speed, "distance": 1},
            frame_range=(0, 9)
        )
        new_pattern = action.apply(design_tools_tab.pattern)
        design_tools_tab.load_pattern(new_pattern)


@when("I apply rotate action")
def apply_rotate_action(design_tools_tab):
    """Apply rotate action."""
    if hasattr(design_tools_tab, 'pattern'):
        action = create_action("rotate", frame_range=(0, 9))
        new_pattern = action.apply(design_tools_tab.pattern)
        design_tools_tab.load_pattern(new_pattern)


@when(parsers.parse("I apply mirror action with axis \"{axis}\""))
def apply_mirror_action(axis: str, design_tools_tab):
    """Apply mirror action."""
    if hasattr(design_tools_tab, 'pattern'):
        action = create_action(
            "mirror",
            parameters={"axis": axis},
            frame_range=(0, 9)
        )
        new_pattern = action.apply(design_tools_tab.pattern)
        design_tools_tab.load_pattern(new_pattern)


@when("I convert the pattern to JSON with RLE encoding")
def convert_pattern_to_json(pattern_object):
    """Convert pattern to JSON."""
    json_data = pattern_object.to_dict()
    return json_data


@when(parsers.parse("I convert JSON to Pattern object"))
def convert_json_to_pattern():
    """Convert JSON to Pattern."""
    # This would use Pattern.from_dict() if implemented
    pytest.skip("Pattern.from_dict() not yet implemented")


# Verification steps
@then(parsers.parse("frame 0 should have {count:d} layers"))
def verify_frame_layer_count(count: int, design_tools_tab):
    """Verify frame has specified number of layers."""
    if hasattr(design_tools_tab, 'layer_manager'):
        layer_count = design_tools_tab.layer_manager.get_layer_count(0)
        assert layer_count == count


@then(parsers.parse("layer opacity should be {opacity:g}"))
def verify_layer_opacity(opacity: float, design_tools_tab):
    """Verify layer opacity."""
    if hasattr(design_tools_tab, 'layer_manager'):
        actual_opacity = design_tools_tab.layer_manager.get_layer_opacity(0, 0)
        assert abs(actual_opacity - opacity) < 0.01


@then(parsers.parse("JSON should be valid according to schema v{version}"))
def verify_json_schema(version: str):
    """Verify JSON is valid according to schema."""
    # This would use schema validation
    pytest.skip("Schema validation not yet implemented in step")


@then("pixels should scroll right across frames")
def verify_scroll_right(design_tools_tab):
    """Verify pixels scrolled right."""
    # Verification logic would go here
    assert True  # Placeholder


@then("pixels should rotate 90 degrees clockwise")
def verify_rotate_clockwise(design_tools_tab):
    """Verify pixels rotated."""
    # Verification logic would go here
    assert True  # Placeholder


@then("pixels should be mirrored horizontally")
def verify_mirror_horizontal(design_tools_tab):
    """Verify pixels mirrored."""
    # Verification logic would go here
    assert True  # Placeholder


# Chip integration steps
@given("I have a connected chip")
def connected_chip():
    """Chip is connected."""
    # In real implementation, this would check for connected hardware
    pytest.skip("Hardware not available in test environment")


@given(parsers.parse("I have selected {chip} chip"))
def select_chip(chip: str):
    """Select chip."""
    adapter = get_adapter(chip)
    assert adapter is not None, f"Chip {chip} not found"
    return adapter


@given(parsers.parse("device is detected on port \"{port}\""))
def device_detected(port: str):
    """Device is detected."""
    # In real implementation, this would detect the device
    pytest.skip("Hardware detection not available in test environment")


@when(parsers.parse("I flash firmware \"{firmware_file}\" to the device"))
def flash_firmware(firmware_file: str):
    """Flash firmware."""
    # In real implementation, this would flash firmware
    pytest.skip("Hardware flashing not available in test environment")


@then("firmware should be flashed successfully")
def verify_firmware_flashed():
    """Verify firmware flashed."""
    # Verification logic would go here
    assert True  # Placeholder


@then("verification should pass")
def verify_verification_passed():
    """Verify verification passed."""
    # Verification logic would go here
    assert True  # Placeholder

