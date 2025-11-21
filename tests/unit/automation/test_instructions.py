from __future__ import annotations

import pytest

from core.automation import (
    KNOWN_LMS_ACTIONS,
    LayerBinding,
    LMSInstruction,
    PatternInstruction,
    PatternInstructionSequence,
)


def test_layer_binding_round_trip() -> None:
    binding = LayerBinding(slot="Frame3", frame_index=2, alias="Primary")
    result = LayerBinding.from_dict(binding.to_dict())
    assert result == binding


def test_lms_instruction_validation() -> None:
    instruction = LMSInstruction(code="moveLeft1", parameters={"speed": 2}, repeat=3, gap=1)
    payload = instruction.to_dict()
    clone = LMSInstruction.from_dict(payload)
    assert clone == instruction

    assert "moveLeft1" in KNOWN_LMS_ACTIONS

    with pytest.raises(ValueError):
        LMSInstruction(code="", repeat=1)
    with pytest.raises(ValueError):
        LMSInstruction(code="moveLeft1", repeat=0)
    with pytest.raises(ValueError):
        LMSInstruction(code="moveLeft1", repeat=1, gap=-1)


def test_pattern_instruction_sequence_summary() -> None:
    sequence = PatternInstructionSequence()
    binding = LayerBinding(slot="Frame1", frame_index=0)

    sequence.add(
        PatternInstruction(
            source=binding,
            instruction=LMSInstruction(code="moveLeft1", repeat=2, gap=0),
        )
    )
    sequence.add(
        PatternInstruction(
            source=binding,
            instruction=LMSInstruction(code="rotate90", repeat=1, gap=1),
        )
    )

    summary = sequence.summarize()
    assert summary["instruction_count"] == 2
    assert summary["total_repeats"] == 3
    assert summary["total_gap"] == 1
    assert summary["unique_actions"] == ["moveLeft1", "rotate90"]

    # Round-trip serialization
    restored = PatternInstructionSequence.from_list(sequence.to_list())
    assert len(restored) == len(sequence)
    assert restored[0].instruction.code == "moveLeft1"
    assert restored[1].instruction.code == "rotate90"

