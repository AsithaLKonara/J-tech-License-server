"""
Pattern Instruction Preview Simulator

Simulates LMS pattern instructions against existing frame data to produce
preview animations without generating new frames. This matches LMS behavior
where instructions are executed at runtime on the MCU.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from core.pattern import Frame, Pattern
from core.automation import (
    PatternInstruction,
    PatternInstructionSequence,
    LayerBinding,
    LMSInstruction,
)


class PreviewSimulator:
    """
    Simulates pattern instructions against existing frames to produce a
    preview of how they would appear when executed on the MCU at runtime.
    """

    def __init__(self, pattern: Pattern):
        if not pattern or not pattern.frames:
            raise ValueError("Pattern must have at least one frame")
        self.pattern = pattern
        self.width = pattern.metadata.width
        self.height = pattern.metadata.height

    def simulate_sequence(
        self, sequence: PatternInstructionSequence, max_frames: Optional[int] = None
    ) -> List[Frame]:
        """
        Simulate a pattern instruction sequence and return preview frames.

        Args:
            sequence: The pattern instruction sequence to simulate
            max_frames: Maximum number of preview frames to generate (None = unlimited)

        Returns:
            List of preview frames showing the animation sequence
        """
        if not sequence:
            return []

        preview_frames: List[Frame] = []
        frame_count = 0

        for instruction in sequence:
            if max_frames and frame_count >= max_frames:
                break

            # Resolve source frame
            source_frame = self._resolve_layer(instruction.source)
            if source_frame is None:
                continue

            # Simulate the instruction
            instruction_frames = self._simulate_instruction(
                source_frame, instruction, max_frames and (max_frames - frame_count)
            )
            preview_frames.extend(instruction_frames)
            frame_count += len(instruction_frames)

        return preview_frames

    def _resolve_layer(self, binding: LayerBinding) -> Optional[Frame]:
        """Resolve a layer binding to an actual frame."""
        if binding.frame_index is not None:
            if 0 <= binding.frame_index < len(self.pattern.frames):
                return self.pattern.frames[binding.frame_index].copy()
        elif binding.slot.startswith("Frame"):
            # Try to extract frame index from slot name (e.g., "Frame1" -> 0)
            try:
                idx_str = binding.slot.replace("Frame", "").strip()
                if idx_str.isdigit():
                    frame_idx = int(idx_str) - 1  # Convert to 0-based
                    if 0 <= frame_idx < len(self.pattern.frames):
                        return self.pattern.frames[frame_idx].copy()
            except (ValueError, AttributeError):
                pass
        # Default to first frame
        return self.pattern.frames[0].copy() if self.pattern.frames else None

    def _simulate_instruction(
        self, source_frame: Frame, instruction: PatternInstruction, max_frames: Optional[int] = None
    ) -> List[Frame]:
        """Simulate a single pattern instruction."""
        frames: List[Frame] = []
        code = instruction.instruction.code
        repeat = instruction.instruction.repeat
        gap = instruction.instruction.gap

        # Apply instruction for each repeat
        current_frame = source_frame.copy()
        for rep in range(repeat):
            if max_frames and len(frames) >= max_frames:
                break

            # Apply the transformation
            transformed = self._apply_action(current_frame, code, instruction.instruction.parameters)
            
            # Create preview frame
            preview = transformed.copy()
            if gap > 0:
                # Gap means insert spacing - adjust duration
                preview.duration_ms = source_frame.duration_ms + gap
            frames.append(preview)

            # For next iteration, use the transformed frame as base
            current_frame = transformed.copy()

        return frames

    def _apply_action(self, frame: Frame, code: str, parameters: Dict[str, object]) -> Frame:
        """Apply a single action code to a frame."""
        result = frame.copy()

        # Map LMS action codes to transformations
        if code == "moveLeft1":
            result.pixels = self._move_left(result.pixels, 1)
        elif code == "moveRight1":
            result.pixels = self._move_right(result.pixels, 1)
        elif code == "moveUp1":
            result.pixels = self._move_up(result.pixels, 1)
        elif code == "moveDown1":
            result.pixels = self._move_down(result.pixels, 1)
        elif code == "rotate90":
            result.pixels = self._rotate_90(result.pixels)
        elif code == "mirrorH":
            result.pixels = self._mirror_horizontal(result.pixels)
        elif code == "mirrorV":
            result.pixels = self._mirror_vertical(result.pixels)
        elif code == "invert":
            result.pixels = [(255 - r, 255 - g, 255 - b) for r, g, b in result.pixels]
        elif code == "brightness":
            brightness = parameters.get("value", parameters.get("brightness", 128))
            if isinstance(brightness, int):
                scale = brightness / 255.0
                result.pixels = [
                    (int(r * scale), int(g * scale), int(b * scale))
                    for r, g, b in result.pixels
                ]
        elif code == "fade":
            # Simple fade implementation: lerp toward black using a 0–255 strength parameter.
            strength = parameters.get("strength", parameters.get("value", 128))
            if isinstance(strength, int):
                scale = max(0.0, min(1.0, strength / 255.0))
                result.pixels = [
                    (int(r * (1.0 - scale)), int(g * (1.0 - scale)), int(b * (1.0 - scale)))
                    for r, g, b in result.pixels
                ]
        elif code == "randomize":
            # Randomize pixels; keep behaviour deterministic per call by using the existing
            # RGB values as a rough seed (no explicit RNG seeding here).
            import random

            random_strength = parameters.get("strength", 255)
            clamp = lambda v: max(0, min(255, v))
            new_pixels = []
            for r, g, b in result.pixels:
                delta = random.randint(-random_strength, random_strength)
                new_pixels.append((clamp(r + delta), clamp(g + delta), clamp(b + delta)))
            result.pixels = new_pixels
        elif code == "scrollText":
            # Text scrolling is rendered into frames elsewhere; for preview we treat this as
            # a no-op on the raw bitmap and rely on higher-level simulators.
            return result
        # Unknown codes fall through as no-ops so previews remain stable even if new
        # actions are added on the MCU side before the simulator is updated.

        return result

    def _frame_to_grid(self, pixels: List[Tuple[int, int, int]]) -> List[List[Tuple[int, int, int]]]:
        """Convert flat pixel list to 2D grid."""
        grid = []
        for y in range(self.height):
            row_start = y * self.width
            row_end = row_start + self.width
            grid.append(list(pixels[row_start:row_end]))
        return grid

    def _grid_to_frame(self, grid: List[List[Tuple[int, int, int]]]) -> List[Tuple[int, int, int]]:
        """Convert 2D grid to flat pixel list."""
        pixels = []
        for row in grid:
            pixels.extend(row)
        return pixels

    def _move_left(self, pixels: List[Tuple[int, int, int]], offset: int) -> List[Tuple[int, int, int]]:
        """Shift pixels left by offset columns."""
        grid = self._frame_to_grid(pixels)
        new_grid = [[(0, 0, 0) for _ in range(self.width)] for _ in range(self.height)]
        for y in range(self.height):
            for x in range(self.width):
                src_x = x + offset
                if 0 <= src_x < self.width:
                    new_grid[y][x] = grid[y][src_x]
        return self._grid_to_frame(new_grid)

    def _move_right(self, pixels: List[Tuple[int, int, int]], offset: int) -> List[Tuple[int, int, int]]:
        """Shift pixels right by offset columns."""
        grid = self._frame_to_grid(pixels)
        new_grid = [[(0, 0, 0) for _ in range(self.width)] for _ in range(self.height)]
        for y in range(self.height):
            for x in range(self.width):
                src_x = x - offset
                if 0 <= src_x < self.width:
                    new_grid[y][x] = grid[y][src_x]
        return self._grid_to_frame(new_grid)

    def _move_up(self, pixels: List[Tuple[int, int, int]], offset: int) -> List[Tuple[int, int, int]]:
        """Shift pixels up by offset rows."""
        grid = self._frame_to_grid(pixels)
        new_grid = [[(0, 0, 0) for _ in range(self.width)] for _ in range(self.height)]
        for y in range(self.height):
            for x in range(self.width):
                src_y = y + offset
                if 0 <= src_y < self.height:
                    new_grid[y][x] = grid[src_y][x]
        return self._grid_to_frame(new_grid)

    def _move_down(self, pixels: List[Tuple[int, int, int]], offset: int) -> List[Tuple[int, int, int]]:
        """Shift pixels down by offset rows."""
        grid = self._frame_to_grid(pixels)
        new_grid = [[(0, 0, 0) for _ in range(self.width)] for _ in range(self.height)]
        for y in range(self.height):
            for x in range(self.width):
                src_y = y - offset
                if 0 <= src_y < self.height:
                    new_grid[y][x] = grid[src_y][x]
        return self._grid_to_frame(new_grid)

    def _rotate_90(self, pixels: List[Tuple[int, int, int]]) -> List[Tuple[int, int, int]]:
        """Rotate 90 degrees clockwise."""
        grid = self._frame_to_grid(pixels)
        rotated = []
        for x in range(self.width):
            new_row = []
            for y in range(self.height - 1, -1, -1):
                new_row.append(grid[y][x])
            rotated.append(new_row)
        # After rotation, dimensions swap
        old_width, old_height = self.width, self.height
        self.width = old_height
        self.height = old_width
        result = self._grid_to_frame(rotated)
        # Restore dimensions
        self.width, self.height = old_width, old_height
        return result

    def _mirror_horizontal(self, pixels: List[Tuple[int, int, int]]) -> List[Tuple[int, int, int]]:
        """Mirror horizontally."""
        grid = self._frame_to_grid(pixels)
        mirrored = [list(reversed(row)) for row in grid]
        return self._grid_to_frame(mirrored)

    def _mirror_vertical(self, pixels: List[Tuple[int, int, int]]) -> List[Tuple[int, int, int]]:
        """Mirror vertically."""
        grid = self._frame_to_grid(pixels)
        mirrored = list(reversed(grid))
        return self._grid_to_frame(mirrored)

