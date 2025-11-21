from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from domain.actions import DesignAction
from ui.tabs.design_tools_tab import DesignToolsTab


def test_automation_queue_updates_timeline(qtbot, pattern_factory):
    tab = DesignToolsTab()
    qtbot.addWidget(tab)
    pattern = pattern_factory(frame_count=4)
    tab.load_pattern(pattern)

    action = DesignAction(name="Scroll Right", action_type="scroll", params={"direction": "Right"})
    tab.automation_manager.set_actions([action])

    overlays = tab._build_timeline_overlays(tab.state.frame_count())
    assert len(overlays) == 1
    assert overlays[0].label == "Scroll Right"

    qtbot.mouseClick(tab.playback_play_btn, Qt.LeftButton)
    qtbot.wait(100)
    tab.playback_stop_btn.click()
    tab.deleteLater()


def test_preset_roundtrip(qtbot, pattern_factory, tmp_path, monkeypatch):
    tab = DesignToolsTab()
    qtbot.addWidget(tab)
    pattern = pattern_factory(frame_count=2)
    tab.load_pattern(pattern)
    tab.preset_repo = tab.preset_repo.__class__(tmp_path / "automation_presets.json")
    tab._refresh_preset_combo()

    action = DesignAction(name="Mirror", action_type="mirror", params={"axis": "horizontal"})
    tab.automation_manager.set_actions([action])
    tab.preset_combo.setEditText("MirrorPreset")
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Yes)

    tab._on_save_preset()

    tab.automation_manager.clear()
    tab.preset_combo.setCurrentText("MirrorPreset")
    tab._on_apply_preset()

    actions = tab.automation_manager.actions()
    assert len(actions) == 1
    assert actions[0].action_type == "mirror"
    tab.deleteLater()

