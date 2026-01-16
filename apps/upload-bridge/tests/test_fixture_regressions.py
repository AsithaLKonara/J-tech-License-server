import pytest

from core.dimension_scorer import score_dimensions
from tests.helpers import make_raw_rgb_payload


@pytest.fixture(params=[
    ("8x8_raw", make_raw_rgb_payload(8, 8)),
    ("20x10_raw", make_raw_rgb_payload(20, 10)),
    ("5x17_raw", make_raw_rgb_payload(5, 17)),
])
def fixture_payload(request):
    return request.param


def test_fixture_dimensions_and_confidence(fixture_payload):
    name, data = fixture_payload
    width, height, frames, confidence = score_dimensions(data, bytes_per_pixel=3)

    if "8x8" in name:
        assert (width, height, frames) == (8, 8, 1)
        assert confidence >= 0.6
    elif "20x10" in name:
        assert {width, height} == {20, 10}
        assert frames == 1
        assert confidence >= 0.6
    elif "5x17" in name:
        assert {width, height} == {5, 17}
        assert frames == 1
        assert confidence >= 0.45
    else:
        pytest.fail("Unknown fixture scenario")

    assert 0.0 <= confidence <= 1.0

