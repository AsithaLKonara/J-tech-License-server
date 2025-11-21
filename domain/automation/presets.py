from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Iterable, List

from domain.actions import DesignAction


class PresetRepository:
    """
    Simple JSON-backed preset storage.
    """

    def __init__(self, path: Path):
        self._path = path
        self._presets: Dict[str, List[dict]] = {}
        self._load()

    @property
    def path(self) -> Path:
        return self._path

    def _load(self) -> None:
        if self._path.exists():
            try:
                self._presets = json.loads(self._path.read_text(encoding="utf-8"))
            except Exception:
                self._presets = {}
        else:
            self._presets = {}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._presets, indent=2), encoding="utf-8")

    def names(self) -> List[str]:
        return sorted(self._presets.keys())

    def get(self, name: str) -> List[DesignAction]:
        entries = self._presets.get(name, [])
        return [DesignAction(**entry) for entry in entries]

    def upsert(self, name: str, actions: Iterable[DesignAction]) -> None:
        name = name.strip()
        if not name:
            raise ValueError("Preset name cannot be empty.")
        self._presets[name] = [asdict(action) for action in actions]
        self._save()

    def delete(self, name: str) -> None:
        if name in self._presets:
            del self._presets[name]
            self._save()

    def exists(self, name: str) -> bool:
        return name in self._presets

    def rename(self, source: str, target: str, overwrite: bool = False) -> None:
        source = source.strip()
        target = target.strip()
        if source not in self._presets:
            raise KeyError(f"Preset '{source}' does not exist.")
        if not target:
            raise ValueError("New preset name cannot be empty.")
        if source == target:
            return
        if not overwrite and target in self._presets:
            raise ValueError(f"Preset '{target}' already exists.")
        self._presets[target] = deepcopy(self._presets[source])
        if target != source:
            del self._presets[source]
        self._save()

    def duplicate(self, source: str, target: str, overwrite: bool = False) -> None:
        source = source.strip()
        target = target.strip()
        if source not in self._presets:
            raise KeyError(f"Preset '{source}' does not exist.")
        if not target:
            raise ValueError("New preset name cannot be empty.")
        if not overwrite and target in self._presets:
            raise ValueError(f"Preset '{target}' already exists.")
        self._presets[target] = deepcopy(self._presets[source])
        self._save()

    def export_to_path(self, name: str, path: Path) -> None:
        if name not in self._presets:
            raise KeyError(f"Preset '{name}' does not exist.")
        path = Path(path)
        payload = {name: deepcopy(self._presets[name])}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def import_from_path(self, path: Path, overwrite: bool = False) -> List[str]:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            # Treat as anonymous preset with filename stem
            name = path.stem
            if not overwrite and name in self._presets:
                raise ValueError(f"Preset '{name}' already exists.")
            self._presets[name] = data
            imported = [name]
        elif isinstance(data, dict):
            imported = []
            for name, actions in data.items():
                if not overwrite and name in self._presets:
                    raise ValueError(f"Preset '{name}' already exists.")
                self._presets[name] = actions
                imported.append(name)
        else:
            raise ValueError("Invalid preset file format.")
        self._save()
        return imported

