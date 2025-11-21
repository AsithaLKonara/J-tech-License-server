from __future__ import annotations

from domain.actions import DesignAction


def test_design_action_equality_and_mutation():
    action = DesignAction(name="Scroll", action_type="scroll", params={"direction": "Right"})
    clone = DesignAction(name="Scroll", action_type="scroll", params={"direction": "Right"})

    assert action == clone
    action.params["direction"] = "Left"
    assert action != clone

