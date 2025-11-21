from __future__ import annotations

import pytest

try:
    from hypothesis import given, strategies as st
except ImportError:  # pragma: no cover
    pytest.skip("hypothesis not installed", allow_module_level=True)

from domain.actions import DesignAction
from domain.automation.queue import AutomationQueueManager


@given(st.lists(st.sampled_from(["scroll", "rotate", "flip", "invert"]), max_size=12))
def test_queue_roundtrip_property(action_types):
    manager = AutomationQueueManager()
    for idx, action_type in enumerate(action_types):
        manager.append(DesignAction(name=f"Action {idx}", action_type=action_type, params={}))

    assert len(manager.actions()) == len(action_types)

    manager.clear()
    assert manager.actions() == []

