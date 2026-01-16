from core.export_templates import available_templates, render_template
from core.pattern import Frame, Pattern, PatternMetadata


def _sample_pattern() -> Pattern:
    metadata = PatternMetadata(width=2, height=1)
    frames = [
        Frame(pixels=[(1, 2, 3), (4, 5, 6)], duration_ms=50),
        Frame(pixels=[(7, 8, 9), (10, 11, 12)], duration_ms=75),
    ]
    return Pattern(name="Sample", metadata=metadata, frames=frames)


def test_available_templates_not_empty():
    templates = available_templates()
    assert "Arduino PROGMEM" in templates
    assert len(templates) >= 2


def test_render_template_contains_frame_definitions():
    pattern = _sample_pattern()
    code = render_template("Arduino PROGMEM", pattern)
    assert "FRAME_000" in code
    assert "FRAME_001" in code
    assert "MATRIX_WIDTH" in code

