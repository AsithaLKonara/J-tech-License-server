from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


# ---------------------------------------------------------------------------
# LMS Automation Action Definitions
# ---------------------------------------------------------------------------

KNOWN_LMS_ACTIONS: Dict[str, str] = {
    "moveLeft1": "Shift pixels left by one column",
    "moveRight1": "Shift pixels right by one column",
    "moveUp1": "Shift pixels up by one row",
    "moveDown1": "Shift pixels down by one row",
    "scrollText": "Scroll the active text buffer",
    "rotate90": "Rotate the frame 90° clockwise",
    "mirrorH": "Mirror horizontally (left/right)",
    "mirrorV": "Mirror vertically (top/bottom)",
    "invert": "Invert frame colours",
    "fade": "Apply fade effect using current palette",
    "brightness": "Adjust brightness by provided value",
    "randomize": "Randomize pixels (seed controlled)",
}


@dataclass(frozen=True)
class LayerBinding:
    """
    Reference to a bitmap source used by LMS pattern instructions.

    Attributes:
        slot: Human-friendly label (e.g. ``Frame1``) used when exporting.
        frame_index: Zero-based index into the pattern frames. ``None`` for
            dynamic bindings resolved during playback (e.g. live layers).
        alias: Optional name for UI display.
    """

    slot: str
    frame_index: Optional[int] = None
    alias: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "slot": self.slot,
            "frame_index": self.frame_index,
            "alias": self.alias,
        }

    @staticmethod
    def from_dict(data: Dict[str, object]) -> "LayerBinding":
        return LayerBinding(
            slot=str(data.get("slot", "")) or "Frame1",
            frame_index=data.get("frame_index"),
            alias=data.get("alias"),
        )


@dataclass
class LMSInstruction:
    """
    Represents a single MCU instruction (automation action) within LMS.

    The instruction code corresponds to a known MCU operation (e.g. ``moveLeft1``)
    and parameters are forwarded as-is during export.
    """

    code: str
    parameters: Dict[str, object] = field(default_factory=dict)
    repeat: int = 1
    gap: int = 0
    brightness_delta: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("Instruction code cannot be empty")
        if self.repeat < 1:
            raise ValueError("Repeat count must be >= 1")
        if self.gap < 0:
            raise ValueError("Gap must be >= 0 (represents frame spacing)")

    def to_dict(self) -> Dict[str, object]:
        return {
            "code": self.code,
            "parameters": dict(self.parameters),
            "repeat": self.repeat,
            "gap": self.gap,
            "brightness_delta": self.brightness_delta,
        }

    @staticmethod
    def from_dict(data: Dict[str, object]) -> "LMSInstruction":
        return LMSInstruction(
            code=str(data.get("code", "")),
            parameters=dict(data.get("parameters") or {}),
            repeat=int(data.get("repeat", 1) or 1),
            gap=int(data.get("gap", 0) or 0),
            brightness_delta=data.get("brightness_delta"),
        )


@dataclass
class PatternInstruction:
    """
    Full LMS pattern instruction tuple.

    Mirrors the LMS tuple format:

    ``(FrameSlot, Instruction, Layer2Slot, MaskSlot, Repeat)``
    """

    source: LayerBinding
    instruction: LMSInstruction
    layer2: Optional[LayerBinding] = None
    mask: Optional[LayerBinding] = None

    def to_tuple(self) -> tuple:
        """
        Return the raw tuple representation expected by LMS export routines.
        """
        return (
            self.source.slot,
            self.instruction.code,
            self.layer2.slot if self.layer2 else "NULL",
            self.mask.slot if self.mask else "NULL",
            self.instruction.repeat,
        )

    def to_dict(self) -> Dict[str, object]:
        return {
            "source": self.source.to_dict(),
            "instruction": self.instruction.to_dict(),
            "layer2": self.layer2.to_dict() if self.layer2 else None,
            "mask": self.mask.to_dict() if self.mask else None,
        }

    @staticmethod
    def from_dict(data: Dict[str, object]) -> "PatternInstruction":
        return PatternInstruction(
            source=LayerBinding.from_dict(data["source"]),
            instruction=LMSInstruction.from_dict(data["instruction"]),
            layer2=LayerBinding.from_dict(data["layer2"]) if data.get("layer2") else None,
            mask=LayerBinding.from_dict(data["mask"]) if data.get("mask") else None,
        )


class PatternInstructionSequence:
    """
    Ordered collection of pattern instructions that mirrors the LMS automation
    queue. The sequence is intentionally lightweight so it can be stored inside
    UI state, serialised for LEDS export, or consumed by preview simulators.
    """

    def __init__(self, instructions: Optional[Iterable[PatternInstruction]] = None):
        self._instructions: List[PatternInstruction] = list(instructions or [])

    def __len__(self) -> int:
        return len(self._instructions)

    def __iter__(self):
        return iter(self._instructions)

    def __getitem__(self, index: int) -> PatternInstruction:
        return self._instructions[index]

    def add(self, instruction: PatternInstruction) -> None:
        self._instructions.append(instruction)

    def insert(self, index: int, instruction: PatternInstruction) -> None:
        self._instructions.insert(index, instruction)

    def remove_at(self, index: int) -> None:
        if 0 <= index < len(self._instructions):
            del self._instructions[index]

    def clear(self) -> None:
        self._instructions.clear()

    def move(self, old_index: int, new_index: int) -> None:
        """
        Reorder instructions within the sequence.
        """
        if not (0 <= old_index < len(self._instructions)):
            return
        if not (0 <= new_index < len(self._instructions)):
            return
        if old_index == new_index:
            return
        inst = self._instructions.pop(old_index)
        self._instructions.insert(new_index, inst)

    def to_list(self) -> List[Dict[str, object]]:
        return [inst.to_dict() for inst in self._instructions]

    @staticmethod
    def from_list(payload: Iterable[Dict[str, object]]) -> "PatternInstructionSequence":
        return PatternInstructionSequence(PatternInstruction.from_dict(item) for item in payload)

    def summarize(self) -> Dict[str, object]:
        """
        Provide a compact summary useful for UI badges/counters.
        """
        total_repeats = sum(inst.instruction.repeat for inst in self._instructions)
        total_gap = sum(inst.instruction.gap for inst in self._instructions)
        unique_actions = sorted({inst.instruction.code for inst in self._instructions})
        return {
            "instruction_count": len(self._instructions),
            "total_repeats": total_repeats,
            "total_gap": total_gap,
            "unique_actions": unique_actions,
        }


def is_known_action(code: str) -> bool:
    """
    Quick helper to validate MCU instruction codes before export.
    """
    return code in KNOWN_LMS_ACTIONS



