import pytest

from core.pattern import Pattern, PatternMetadata, Frame
from ui.tabs.preview_tab import PreviewTab


@pytest.fixture
def preview_tab(qtbot):
    tab = PreviewTab()
    qtbot.addWidget(tab)
    return tab


def _make_pattern(width: int, height: int, confidence: float) -> Pattern:
    led_count = width * height
    frame = Frame(
        pixels=[(i % 256, (i * 2) % 256, (i * 3) % 256) for i in range(led_count)],
        duration_ms=50,
    )
    metadata = PatternMetadata(
        width=width,
        height=height,
        dimension_source="detector" if confidence < 1.0 else "header",
        dimension_confidence=confidence,
    )
    return Pattern(
        name="Test Pattern",
        metadata=metadata,
        frames=[frame],
    )


def test_preview_low_confidence_warning(preview_tab):
    pattern = _make_pattern(20, 10, confidence=0.4)
    preview_tab.load_pattern(pattern)
    assert "⚠" in preview_tab.info_label.text()


def test_preview_high_confidence_no_warning(preview_tab):
    pattern = _make_pattern(12, 6, confidence=0.95)
    preview_tab.load_pattern(pattern)
    assert "⚠" not in preview_tab.info_label.text()

