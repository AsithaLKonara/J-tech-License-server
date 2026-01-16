import math

from core.dimension_scorer import (
    factor_pairs,
    layout_score,
    score_dimensions,
    generate_layout_candidates,
    infer_leds_and_frames,
)


def test_factor_pairs_basic():
    pairs = factor_pairs(200)
    assert (20, 10) in pairs
    assert all(width >= height for width, height in pairs)


def test_layout_score_prefers_common_aspect():
    wide = layout_score(16, 9)
    uncommon = layout_score(13, 7)
    assert wide > uncommon


def test_generate_layout_candidates_alignment_bonus():
    led_count = 20 * 10
    frame = [((idx * 3) % 255, (idx * 7) % 255, (idx * 11) % 255) for idx in range(led_count)]
    candidates = generate_layout_candidates(led_count, first_frame=frame, include_strips=False)
    top_width, top_height, _ = candidates[0]
    assert {top_width, top_height} == {20, 10}


def test_infer_leds_and_frames_counts_frames():
    width, height, frames = 12, 6, 5
    total_pixels = width * height * frames
    resolution = infer_leds_and_frames(total_pixels, preferred_led_counts=[width * height])
    assert resolution is not None
    assert resolution.frames == frames
    assert {resolution.width, resolution.height} == {width, height}


def test_score_dimensions_confidence_bounds():
    width, height, frames, conf = score_dimensions(bytes([1] * 3 * 8 * 8))
    assert width * height == 64
    assert frames >= 1
    assert 0.0 <= conf <= 1.0


def test_score_dimensions_with_non_square_payload():
    width, height = 20, 10
    frames = 3
    data = bytes([(idx * 13) % 256 for idx in range(width * height * frames * 3)])
    w, h, f, conf = score_dimensions(data, bytes_per_pixel=3)
    assert {w, h} == {20, 10}
    assert f == frames
    assert conf > 0.4

