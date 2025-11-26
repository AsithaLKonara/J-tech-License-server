"""
Glyph Provider Utilities
------------------------

Provides reusable helpers for fetching bitmap glyphs either from the
built-in 5×7 font map or from user-defined bitmap fonts. The provider
also offers basic nearest-neighbour scaling so the same glyph data can
be rendered at multiple resolutions (e.g. 3×5, 5×7, 7×9).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from domain.text.bitmap_font import BitmapFont
from domain.text.glyph_map_5x7 import GLYPHS_5X7

GlyphMatrix = List[List[bool]]


@dataclass
class GlyphProvider:
    """Provides glyph matrices for characters with optional scaling."""

    bitmap_font: Optional[BitmapFont] = None
    width: int = 5
    height: int = 7

    def glyph(self, char: str) -> GlyphMatrix:
        """
        Return the bitmap glyph for a character.

        Args:
            char: Character to lookup.
        """
        if self.bitmap_font:
            return self._ensure_size(self.bitmap_font.glyph(char))
        base = GLYPHS_5X7.get(char.upper(), GLYPHS_5X7.get(" ", [[False] * 5 for _ in range(7)]))
        return self._scale(base, self.width, self.height)

    def with_size(self, width: int, height: int) -> "GlyphProvider":
        """Return a new provider configured for a different target size."""
        return GlyphProvider(bitmap_font=self.bitmap_font, width=width, height=height)

    def _ensure_size(self, glyph: GlyphMatrix) -> GlyphMatrix:
        """Pad or trim the glyph to match the provider's size."""
        return self._scale(glyph, self.width or len(glyph[0]), self.height or len(glyph))

    @staticmethod
    def _scale(glyph: GlyphMatrix, width: int, height: int) -> GlyphMatrix:
        """Scale glyph to requested size using nearest neighbour sampling."""
        if not glyph:
            return [[False] * width for _ in range(height)]

        src_height = len(glyph)
        src_width = max(len(row) for row in glyph) if src_height else 0
        if src_width == 0 or src_height == 0:
            return [[False] * width for _ in range(height)]

        scaled: GlyphMatrix = []
        for y in range(height):
            row: List[bool] = []
            src_y = int(y * src_height / height)
            src_y = min(src_y, src_height - 1)
            for x in range(width):
                src_x = int(x * src_width / width)
                src_x = min(src_x, len(glyph[src_y]) - 1)
                row.append(glyph[src_y][src_x])
            scaled.append(row)
        return scaled


def normalize_glyph(glyph: Sequence[Sequence[bool]], width: int = 5) -> GlyphMatrix:
    """Normalize glyph rows to a fixed width for compatibility."""
    normalized: GlyphMatrix = []
    for row in glyph:
        row_list = list(row)
        if len(row_list) < width:
            row_list.extend([False] * (width - len(row_list)))
        normalized.append(row_list[:width])
    return normalized


