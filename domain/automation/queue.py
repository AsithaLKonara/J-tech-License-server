from __future__ import annotations

from typing import Iterable, List

from PySide6.QtCore import QObject, Signal

from domain.actions import DesignAction


class AutomationQueueManager(QObject):
    """
    Maintains the list of automation actions and emits change notifications.
    """

    queue_changed = Signal(list)

    def __init__(self):
        super().__init__()
        self._actions: List[DesignAction] = []

    def actions(self) -> List[DesignAction]:
        return list(self._actions)

    def set_actions(self, actions: Iterable[DesignAction]) -> None:
        self._actions = list(actions)
        self.queue_changed.emit(self.actions())

    def append(self, action: DesignAction) -> None:
        self._actions.append(action)
        self.queue_changed.emit(self.actions())

    def enqueue(self, action: DesignAction) -> None:
        """Alias for append() to match documented API."""
        self.append(action)

    def remove_at(self, index: int) -> None:
        if 0 <= index < len(self._actions):
            del self._actions[index]
            self.queue_changed.emit(self.actions())

    def clear(self) -> None:
        if self._actions:
            self._actions.clear()
            self.queue_changed.emit(self.actions())

