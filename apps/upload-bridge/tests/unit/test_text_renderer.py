import pytest

from domain.text.text_renderer import TextRenderer, TextRenderOptions, TextScrollOptions


def _count_lit_pixels(pixels):
    return sum(1 for r, g, b in pixels if (r, g, b) != (0, 0, 0))


def test_render_pixels_basic_text():
    renderer = TextRenderer()
    opts = TextRenderOptions(width=16, height=8, color=(255, 0, 0))
    pixels = renderer.render_pixels("A", opts)
    assert len(pixels) == 16 * 8
    assert _count_lit_pixels(pixels) > 0


def test_render_typing_frames_increase():
    renderer = TextRenderer()
    opts = TextRenderOptions(width=16, height=8, color=(255, 255, 255))
    frames = renderer.render_typing_frames("AB", opts, frames_per_char=1, frame_duration_ms=50)
    # Expect len(text)+1 frames
    assert len(frames) == 3
    assert frames[0] != frames[-1]


def test_render_scroll_frames_direction_changes():
    renderer = TextRenderer()
    opts = TextRenderOptions(width=12, height=8, color=(0, 255, 0))
    scroll_opts = TextScrollOptions(direction="left", step=2, padding=2)
    frames = renderer.render_scroll_frames("HELLO", opts, scroll_opts)
    assert len(frames) > 0
    assert frames[0] != frames[-1]


def test_outline_effect_adds_pixels():
    renderer = TextRenderer()
    base_opts = TextRenderOptions(width=14, height=10, color=(255, 255, 255))
    outlined_opts = TextRenderOptions(
        width=14,
        height=10,
        color=(255, 255, 255),
        outline=True,
        outline_color=(255, 0, 0),
    )
    plain = renderer.render_pixels("I", base_opts)
    outlined = renderer.render_pixels("I", outlined_opts)
    assert _count_lit_pixels(outlined) >= _count_lit_pixels(plain)
    assert outlined != plain

