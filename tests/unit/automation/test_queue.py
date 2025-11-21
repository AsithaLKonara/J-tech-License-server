from __future__ import annotations

from domain.actions import DesignAction
from domain.automation.queue import AutomationQueueManager


def test_queue_append_and_remove(automation_manager: AutomationQueueManager, sample_action: DesignAction):
    captured = []
    automation_manager.queue_changed.connect(captured.append)

    automation_manager.append(sample_action)
    assert automation_manager.actions() == [sample_action]
    assert captured[-1] == [sample_action]

    automation_manager.remove_at(0)
    assert automation_manager.actions() == []
    assert captured[-1] == []


def test_queue_clear(automation_manager: AutomationQueueManager, sample_action: DesignAction):
    automation_manager.set_actions([sample_action])
    assert automation_manager.actions()

    automation_manager.clear()
    assert automation_manager.actions() == []

