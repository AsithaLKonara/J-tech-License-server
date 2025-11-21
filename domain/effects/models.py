from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Set


@dataclass(slots=True)
class EffectDefinition:
    """Lightweight description of a design effect.

    Attributes:
        identifier: Stable id (relative path or user supplied) used for hashing and lookups.
        name: Human readable display name.
        category: Logical category (e.g. "Linear", "Symmetrical").
        source_path: Absolute path to the effect asset (SWF/JSON/etc.).
        preview_path: Optional absolute path to a preview image.
        keywords: Normalised keywords derived from metadata/name for palette heuristics.
    """

    identifier: str
    name: str
    category: str
    source_path: Path
    preview_path: Path | None = None
    keywords: Set[str] = field(default_factory=set)

    def with_keywords(self, extra: Iterable[str]) -> "EffectDefinition":
        self.keywords.update(_normalise_keywords(extra))
        return self


def _normalise_keywords(words: Iterable[str]) -> Set[str]:
    cleaned: Set[str] = set()
    for word in words:
        normalised = (
            word.strip()
            .lower()
            .replace("_", " ")
            .replace("-", " ")
        )
        for token in normalised.split():
            token = token.strip()
            if token:
                cleaned.add(token)
    return cleaned


__all__ = ["EffectDefinition", "_normalise_keywords"]
