from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional

from core.pattern import Frame, Pattern
from domain.actions import DesignAction


def _safe_int(value: object, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@dataclass
class ActionSchedule:
    action: DesignAction
    repeat: int
    gap_ms: int


@dataclass
class FrameExecutionResult:
    frame_index: int
    actions_applied: int
    added_delay_ms: int
    changed: bool


@dataclass
class AutomationSummary:
    frames: List[FrameExecutionResult]
    total_actions: int
    total_gap_ms: int
    schedule_length: int
    cancelled: bool = False


class AutomationEngine:
    """
    Interprets automation queues and applies them to pattern frames, honouring
    repeat / gap scheduling. Pixel-level transformations are delegated via a
    callback so the UI can provide concrete implementations.
    """

    def build_schedule(self, actions: Iterable[DesignAction]) -> List[ActionSchedule]:
        schedule: List[ActionSchedule] = []
        for action in actions:
            params = action.params or {}
            repeat = max(1, _safe_int(params.get("repeat", 1), 1))
            gap_ms = max(0, _safe_int(params.get("gap_ms", 0), 0))
            schedule.append(ActionSchedule(action=action, repeat=repeat, gap_ms=gap_ms))
        return schedule

    def apply_schedule_to_frame(
        self,
        pattern: Pattern,
        frame_index: int,
        schedule: Iterable[ActionSchedule],
        executor: Callable[[Frame, DesignAction], bool],
    ) -> FrameExecutionResult:
        if not pattern.frames or not (0 <= frame_index < len(pattern.frames)):
            return FrameExecutionResult(frame_index, 0, 0, False)

        frame = pattern.frames[frame_index]
        actions_applied = 0
        added_delay = 0
        changed = False

        for scheduled in schedule:
            for _ in range(scheduled.repeat):
                if executor(frame, scheduled.action):
                    actions_applied += 1
                    changed = True
            if scheduled.gap_ms > 0:
                frame.duration_ms = max(1, int(frame.duration_ms) + scheduled.gap_ms)
                added_delay += scheduled.gap_ms

        if added_delay > 0:
            changed = True

        return FrameExecutionResult(
            frame_index=frame_index,
            actions_applied=actions_applied,
            added_delay_ms=added_delay,
            changed=changed,
        )

    def apply_to_frames(
        self,
        pattern: Pattern,
        frame_indices: Iterable[int],
        actions: Iterable[DesignAction],
        executor: Callable[[Frame, DesignAction], bool],
        progress_callback: Optional[Callable[[int, int, FrameExecutionResult], bool]] = None,
    ) -> AutomationSummary:
        schedule = self.build_schedule(actions)
        results: List[FrameExecutionResult] = []
        total_actions = 0
        total_gap = 0
        cancelled = False

        if not schedule:
            return AutomationSummary(results, total_actions, total_gap, 0, cancelled=False)

        for idx, frame_index in enumerate(frame_indices):
            result = self.apply_schedule_to_frame(pattern, frame_index, schedule, executor)
            results.append(result)
            total_actions += result.actions_applied
            total_gap += result.added_delay_ms

            if progress_callback:
                should_continue = progress_callback(idx, frame_index, result)
                if should_continue is False:
                    cancelled = True
                    break

        return AutomationSummary(
            frames=results,
            total_actions=total_actions,
            total_gap_ms=total_gap,
            schedule_length=len(schedule),
            cancelled=cancelled,
        )


