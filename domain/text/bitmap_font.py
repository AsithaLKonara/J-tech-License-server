from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


def _slugify(value: str) -> str:
    slug = "".join(c.lower() if c.isalnum() else "-" for c in value)
    slug = "-".join(filter(None, slug.split("-")))
    return slug or "font"


@dataclass
class BitmapFont:
    """Simple bitmap font representation."""

    name: str
    width: int = 5
    height: int = 7
    glyphs: Dict[str, List[List[bool]]] = field(default_factory=dict)

    def glyph(self, char: str) -> List[List[bool]]:
        """Return glyph grid (copy) for character."""
        char_key = char.upper()
        grid = self.glyphs.get(char_key)
        if grid:
            return [row[: self.width] + [False] * max(0, self.width - len(row)) for row in grid[: self.height]] + [
                [False] * self.width for _ in range(max(0, self.height - len(grid)))
            ]
        return [[False] * self.width for _ in range(self.height)]

    def update_glyph(self, char: str, grid: List[List[bool]]) -> None:
        """Update glyph data (grid of booleans)."""
        normalized: List[List[bool]] = []
        for row in grid[: self.height]:
            padded = list(row[: self.width])
            if len(padded) < self.width:
                padded.extend([False] * (self.width - len(padded)))
            normalized.append(padded)
        while len(normalized) < self.height:
            normalized.append([False] * self.width)
        self.glyphs[char.upper()] = normalized

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "glyphs": {
                char: ["".join("1" if cell else "0" for cell in row) for row in grid]
                for char, grid in self.glyphs.items()
            },
        }

    @staticmethod
    def from_dict(data: Dict) -> "BitmapFont":
        glyphs = {}
        for char, rows in data.get("glyphs", {}).items():
            glyphs[char.upper()] = [[c == "1" for c in row] for row in rows]
        return BitmapFont(
            name=data.get("name", "Custom Font"),
            width=data.get("width", 5),
            height=data.get("height", 7),
            glyphs=glyphs,
        )


class BitmapFontRepository:
    """JSON-backed font storage."""

    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def list_fonts(self) -> List[str]:
        return sorted(p.stem for p in self.base_path.glob("*.json"))

    def load_font(self, name: str) -> BitmapFont:
        path = self._font_path(name)
        if not path.exists():
            raise FileNotFoundError(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        return BitmapFont.from_dict(data)

    def save_font(self, font: BitmapFont) -> Path:
        path = self._font_path(font.name)
        path.write_text(json.dumps(font.to_dict(), indent=2), encoding="utf-8")
        return path

    def font_exists(self, name: str) -> bool:
        return self._font_path(name).exists()

    def _font_path(self, name: str) -> Path:
        return self.base_path / f"{_slugify(name)}.json"

