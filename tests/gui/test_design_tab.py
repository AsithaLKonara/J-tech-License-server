from __future__ import annotations

import pytest
from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import QMessageBox, QInputDialog
from PySide6.QtWidgets import QApplication

from core.pattern import Frame, Pattern, PatternMetadata
from domain.actions import DesignAction
from domain.automation.presets import PresetRepository
from ui.tabs.design_tools_tab import DesignToolsTab


def _make_pattern(frame_count: int = 3, width: int = 4, height: int = 1) -> Pattern:
    metadata = PatternMetadata(width=width, height=height)
    frames = []
    for idx in range(frame_count):
        pixels = [(idx * 10 + col, 0, 0) for col in range(width)]
        frames.append(Frame(pixels=pixels, duration_ms=50))
    return Pattern(name="Test Pattern", metadata=metadata, frames=frames)


def test_transport_step_forward_and_back(qtbot):
    tab = DesignToolsTab()
    qtbot.addWidget(tab)
    pattern = _make_pattern()
    tab.load_pattern(pattern)

    initial_index = tab._current_frame_index
    qtbot.mouseClick(tab.playback_next_btn, Qt.LeftButton)
    assert tab._current_frame_index == min(initial_index + 1, len(pattern.frames) - 1)

    qtbot.mouseClick(tab.playback_prev_btn, Qt.LeftButton)
    assert tab._current_frame_index == initial_index
    tab.deleteLater()


def test_transport_play_and_stop(qtbot):
    tab = DesignToolsTab()
    qtbot.addWidget(tab)
    pattern = _make_pattern()
    tab.load_pattern(pattern)

    tab.playback_fps_spin.setValue(60)
    qtbot.mouseClick(tab.playback_play_btn, Qt.LeftButton)
    qtbot.waitUntil(lambda: tab._current_frame_index != 0, timeout=1000)
    assert tab._playback_timer.isActive()

    qtbot.mouseClick(tab.playback_stop_btn, Qt.LeftButton)
    assert not tab._playback_timer.isActive()
    tab.deleteLater()


def test_timeline_click_selects_frame(qtbot):
    tab = DesignToolsTab()
    qtbot.addWidget(tab)
    pattern = _make_pattern(frame_count=5)
    tab.load_pattern(pattern)
    tab.show()
    qtbot.waitExposed(tab)

    timeline = tab.timeline
    total_frames = len(pattern.frames)
    frame_width = timeline._frame_width()  # type: ignore[attr-defined]
    target_index = 2
    x = int(timeline.LANE_PADDING + target_index * frame_width + frame_width / 2)
    y = timeline.height() // 2
    qtbot.mouseClick(timeline, Qt.LeftButton, pos=QPoint(x, y))

    assert tab._current_frame_index == target_index
    tab.deleteLater()


def test_timeline_overlay_click_selects_action(qtbot):
    tab = DesignToolsTab()
    qtbot.addWidget(tab)
    pattern = _make_pattern(frame_count=6)
    tab.load_pattern(pattern)
    tab._queue_action("Scroll Left", "scroll", {"direction": "Left"})
    tab.show()
    qtbot.waitExposed(tab)

    timeline = tab.timeline

    def overlay_rect_ready():
        timeline.update()
        QApplication.processEvents()
        return bool(getattr(timeline, "_overlay_rects", []))

    qtbot.waitUntil(overlay_rect_ready, timeout=1000)
    rect, _overlay = timeline._overlay_rects[0]
    pos = rect.center()
    qtbot.mouseClick(timeline, Qt.LeftButton, pos=pos)

    assert tab.action_list.currentRow() == 0
    assert timeline._selected_action_index == 0
    tab.deleteLater()


def test_action_validation_feedback(qtbot):
    tab = DesignToolsTab()
    qtbot.addWidget(tab)
    pattern = _make_pattern(frame_count=2)
    tab.load_pattern(pattern)
    tab.show()
    qtbot.waitExposed(tab)

    invalid_action = DesignAction(
        name="Scroll Invalid",
        action_type="scroll",
        params={"direction": "Left", "step": 0},
    )
    tab.automation_manager.set_actions([invalid_action])

    tab.action_list.setCurrentRow(0)
    qtbot.waitUntil(lambda: not tab.action_validation_label.isHidden(), timeout=1000)
    assert tab.action_list.item(0).text().startswith("⚠")
    tab.deleteLater()


def test_preset_duplicate_and_rename(qtbot, pattern_factory, tmp_path, monkeypatch):
    tab = DesignToolsTab()
    qtbot.addWidget(tab)
    pattern = pattern_factory(frame_count=2)
    tab.load_pattern(pattern)
    tab.preset_repo = PresetRepository(tmp_path / "automation_presets.json")
    tab._refresh_preset_combo()

    action = DesignAction(name="Scroll Right", action_type="scroll", params={"direction": "Right"})
    tab.automation_manager.set_actions([action])
    tab.preset_combo.setEditText("BasePreset")

    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Yes)

    tab._on_save_preset()
    assert tab.preset_repo.exists("BasePreset")

    monkeypatch.setattr(QInputDialog, "getText", lambda *args, **kwargs: ("BasePreset Copy", True))
    tab.preset_combo.setCurrentText("BasePreset")
    tab._on_duplicate_preset()
    assert tab.preset_repo.exists("BasePreset Copy")

    monkeypatch.setattr(QInputDialog, "getText", lambda *args, **kwargs: ("RenamedPreset", True))
    tab.preset_combo.setCurrentText("BasePreset Copy")
    tab._on_rename_preset()
    assert tab.preset_repo.exists("RenamedPreset")
    assert not tab.preset_repo.exists("BasePreset Copy")

    tab.deleteLater()
