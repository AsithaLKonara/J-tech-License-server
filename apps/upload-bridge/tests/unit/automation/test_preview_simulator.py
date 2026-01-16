from __future__ import annotations

from core.automation import LayerBinding, LMSInstruction, PatternInstruction, PatternInstructionSequence, PreviewSimulator
from core.pattern import Frame, Pattern, PatternMetadata


def _make_pattern(width: int = 4, height: int = 1) -> Pattern:
    pixels = [
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
        (0, 0, 0),
    ]
    frame = Frame(pixels=pixels[: width * height], duration_ms=50)
    metadata = PatternMetadata(width=width, height=height)
    return Pattern(name="PreviewTest", metadata=metadata, frames=[frame])


def test_preview_simulator_shift_left() -> None:
    pattern = _make_pattern()
    sequence = PatternInstructionSequence(
        [
            PatternInstruction(
                source=LayerBinding(slot="Frame1", frame_index=0),
                instruction=LMSInstruction(code="moveLeft1", repeat=1),
            )
        ]
    )

    simulator = PreviewSimulator(pattern)
    frames = simulator.simulate_sequence(sequence)

    assert len(frames) == 1
    preview_pixels = frames[0].pixels
    # Left shift drops the first pixel and fills with black at the end
    assert preview_pixels[0] == (0, 255, 0)
    assert preview_pixels[-1] == (0, 0, 0)


def test_preview_simulator_multiple_repeats() -> None:
    pattern = _make_pattern()
    sequence = PatternInstructionSequence(
        [
            PatternInstruction(
                source=LayerBinding(slot="Frame1", frame_index=0),
                instruction=LMSInstruction(code="mirrorH", repeat=2),
            )
        ]
    )

    simulator = PreviewSimulator(pattern)
    frames = simulator.simulate_sequence(sequence)

    # Repeat=2 should produce two preview frames
    assert len(frames) == 2
    first, second = frames

    # Mirror horizontally twice -> returns to original
    assert first.pixels != pattern.frames[0].pixels
    assert second.pixels == pattern.frames[0].pixels


def test_preview_simulator_brightness_parameter_aliases() -> None:
    pattern = _make_pattern()
    # Use "brightness" instead of "value" to ensure both keys are respected.
    instruction = LMSInstruction(code="brightness", parameters={"brightness": 128}, repeat=1)
    sequence = PatternInstructionSequence(
        [PatternInstruction(source=LayerBinding(slot="Frame1", frame_index=0), instruction=instruction)]
    )

    simulator = PreviewSimulator(pattern)
    frames = simulator.simulate_sequence(sequence)

    assert len(frames) == 1
    preview_pixels = frames[0].pixels
    # First pixel was full red; at ~50% brightness it should be roughly half.
    r, g, b = preview_pixels[0]
    assert g == 0 and b == 0
    assert 110 <= r <= 130


def test_preview_simulator_fade_towards_black() -> None:
    pattern = _make_pattern()
    instruction = LMSInstruction(code="fade", parameters={"strength": 255}, repeat=1)
    sequence = PatternInstructionSequence(
        [PatternInstruction(source=LayerBinding(slot="Frame1", frame_index=0), instruction=instruction)]
    )

    simulator = PreviewSimulator(pattern)
    frames = simulator.simulate_sequence(sequence)

    assert len(frames) == 1
    preview_pixels = frames[0].pixels
    # Full-strength fade should drive all pixels to (0,0,0).
    assert all(px == (0, 0, 0) for px in preview_pixels)


def test_preview_simulator_randomize_changes_pixels() -> None:
    pattern = _make_pattern()
    instruction = LMSInstruction(code="randomize", parameters={"strength": 64}, repeat=1)
    sequence = PatternInstructionSequence(
        [PatternInstruction(source=LayerBinding(slot="Frame1", frame_index=0), instruction=instruction)]
    )

    simulator = PreviewSimulator(pattern)
    frames = simulator.simulate_sequence(sequence)

    assert len(frames) == 1
    preview_pixels = frames[0].pixels
    # With randomization enabled, at least one pixel should differ from the original.
    assert any(a != b for a, b in zip(preview_pixels, pattern.frames[0].pixels))


def test_preview_simulator_scroll_text_is_noop() -> None:
    pattern = _make_pattern()
    instruction = LMSInstruction(code="scrollText", parameters={"speed": 1}, repeat=1)
    sequence = PatternInstructionSequence(
        [PatternInstruction(source=LayerBinding(slot="Frame1", frame_index=0), instruction=instruction)]
    )

    simulator = PreviewSimulator(pattern)
    frames = simulator.simulate_sequence(sequence)

    assert len(frames) == 1
    # For preview simulator, scrollText should not mutate the underlying bitmap.
    assert frames[0].pixels == pattern.frames[0].pixels
