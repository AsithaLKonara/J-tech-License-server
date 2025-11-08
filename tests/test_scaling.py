import os
import time

import pytest

from core.dimension_scorer import score_dimensions


@pytest.mark.slow
def test_large_file_performance():
    width = 64
    height = 32
    frames = 10
    data = os.urandom(width * height * frames * 3)

    start = time.perf_counter()
    result = score_dimensions(data)
    duration = time.perf_counter() - start

    assert duration < 0.5  # heuristic bound
    assert result[0] > 0
    assert result[1] > 0
    assert result[2] >= 1
    assert 0.0 <= result[3] <= 1.0

