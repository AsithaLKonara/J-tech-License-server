from pathlib import Path

import pytest

from tests.helpers import (
    make_raw_rgb_payload,
    make_standard_binary,
    make_dimension_header_binary,
    write_fixture,
)

FIXTURE_DIR = Path("tests/fixtures")


@pytest.fixture(scope="module")
def fixtures(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("parser-fixtures")

    write_fixture(
        tmp_dir / "raw_20x10.bin",
        make_raw_rgb_payload(20, 10),
    )
    write_fixture(
        tmp_dir / "standard_8x8.bin",
        make_standard_binary(8, 8),
    )
    write_fixture(
        tmp_dir / "dimension_header_32x8.bin",
        make_dimension_header_binary(32, 8, frames=2),
    )
    return tmp_dir


@pytest.mark.parametrize(
    "filename,expected_dims,parser_factories",
    [
        ("raw_20x10.bin", (20, 10), ["enhanced", "raw"]),
        ("standard_8x8.bin", (8, 8), ["standard"]),
        ("dimension_header_32x8.bin", (32, 8), ["enhanced"]),
    ],
)
def test_parsers_produce_consistent_dimensions(fixtures, filename, expected_dims, parser_factories):
    file_path = fixtures / filename
    data = file_path.read_bytes()

    from parsers.enhanced_binary_parser import EnhancedBinaryParser
    from parsers.raw_rgb_parser import RawRGBParser
    from parsers.standard_format_parser import StandardFormatParser

    parser_map = {
        "enhanced": EnhancedBinaryParser,
        "raw": RawRGBParser,
        "standard": StandardFormatParser,
    }
    parsers = [parser_map[name]() for name in parser_factories]

    widths = set()
    heights = set()

    for parser in parsers:
        pattern = parser.parse(data)
        widths.add(pattern.metadata.width)
        heights.add(pattern.metadata.height)
        assert 0.0 <= pattern.metadata.dimension_confidence <= 1.0
        assert pattern.metadata.width > 0 and pattern.metadata.height > 0

    assert widths == {expected_dims[0]}
    assert heights == {expected_dims[1]}

