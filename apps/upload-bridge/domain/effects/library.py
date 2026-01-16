from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List

from .models import EffectDefinition, _normalise_keywords

_SUPPORTED_ASSET_EXTENSIONS = {".swf", ".json", ".yaml", ".yml"}
_PREVIEW_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp"}


class EffectLibrary:
    """Discovers effect assets and exposes them as `EffectDefinition`s.

    The loader is intentionally forgiving: any supported file below the root
    directory is treated as an effect.  Metadata may be provided via adjacent
    JSON/YAML files – if present they can override name/category/keywords.
    Adding new effects is as simple as dropping files in the `Res/effects`
    folder and pressing refresh in the UI.
    """

    def __init__(self, root: Path):
        self._root = root
        self._effects: List[EffectDefinition] = []
        self.reload()

    @property
    def root(self) -> Path:
        return self._root

    def reload(self) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        self._effects = list(self._scan_effects())
        self._effects.sort(key=lambda eff: (eff.category.lower(), eff.name.lower()))

    def categories(self) -> List[str]:
        cats = sorted({e.category for e in self._effects})
        return cats

    def effects(self) -> List[EffectDefinition]:
        return list(self._effects)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _scan_effects(self) -> Iterable[EffectDefinition]:
        if not self._root.exists():
            return []

        encountered: Dict[str, EffectDefinition] = {}
        for path in self._root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in _SUPPORTED_ASSET_EXTENSIONS:
                continue

            rel_path = path.relative_to(self._root)
            identifier = str(rel_path).replace("\\", "/")
            if identifier in encountered:
                continue

            metadata = self._load_metadata(path)
            name = metadata.get("name") or path.stem.replace("_", " ").replace("-", " ")
            category = metadata.get("category") or self._derive_category(rel_path)
            keywords = _normalise_keywords(metadata.get("keywords", []))
            keywords.update(_normalise_keywords(name.split()))
            keywords.update(_normalise_keywords(category.split()))

            preview_path = self._find_preview_for_asset(path, metadata)

            effect = EffectDefinition(
                identifier=identifier,
                name=name,
                category=category,
                source_path=path,
                preview_path=preview_path,
                keywords=keywords,
            )
            encountered[identifier] = effect

        return encountered.values()

    def _derive_category(self, rel_path: Path) -> str:
        # Use the immediate parent (excluding language folders) as category fallback.
        parts = [part for part in rel_path.parts[:-1] if part.lower() not in {"effect_en", "effects"}]
        if parts:
            return parts[-1].replace("_", " ").replace("-", " ")
        return "Uncategorised"

    def _load_metadata(self, asset_path: Path) -> Dict[str, object]:
        meta_candidates = [
            asset_path.with_suffix(".json"),
            asset_path.with_suffix(".yaml"),
            asset_path.with_suffix(".yml"),
        ]
        for candidate in meta_candidates:
            if candidate.exists():
                try:
                    return json.loads(candidate.read_text(encoding="utf-8"))
                except Exception:
                    continue
        return {}

    def _find_preview_for_asset(self, asset_path: Path, metadata: Dict[str, object]) -> Path | None:
        if "preview" in metadata:
            preview_path = Path(metadata["preview"])  # type: ignore[arg-type]
            if not preview_path.is_absolute():
                preview_path = asset_path.parent / preview_path
            if preview_path.exists():
                return preview_path

        for ext in _PREVIEW_EXTENSIONS:
            candidate = asset_path.with_suffix(ext)
            if candidate.exists():
                return candidate

        # Look for generic preview.png in same folder
        generic = asset_path.parent / "preview.png"
        if generic.exists():
            return generic

        return None
