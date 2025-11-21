from __future__ import annotations

from pathlib import Path

import pytest

from domain.actions import DesignAction
from domain.automation.presets import PresetRepository


def _make_action(name: str = "Scroll", direction: str = "Left") -> DesignAction:
    return DesignAction(name=name, action_type="scroll", params={"direction": direction, "step": 1})


def test_preset_duplicate_and_rename(tmp_path: Path):
    repo = PresetRepository(tmp_path / "presets.json")
    repo.upsert("Base", [_make_action()])

    repo.duplicate("Base", "Copy")
    assert "Copy" in repo.names()
    assert repo.get("Copy")[0].action_type == "scroll"

    repo.rename("Copy", "Renamed")
    assert "Renamed" in repo.names()
    assert "Copy" not in repo.names()

    with pytest.raises(ValueError):
        repo.duplicate("Renamed", "Base")


def test_preset_export_import(tmp_path: Path):
    repo = PresetRepository(tmp_path / "presets.json")
    repo.upsert("Original", [_make_action(direction="Right")])

    export_path = tmp_path / "exported.json"
    repo.export_to_path("Original", export_path)
    assert export_path.exists()

    imported_repo = PresetRepository(tmp_path / "imported.json")
    imported_names = imported_repo.import_from_path(export_path)
    assert imported_names == ["Original"]
    imported_actions = imported_repo.get("Original")
    assert imported_actions[0].params["direction"] == "Right"

    # importing again without overwrite should raise
    with pytest.raises(ValueError):
        imported_repo.import_from_path(export_path, overwrite=False)


