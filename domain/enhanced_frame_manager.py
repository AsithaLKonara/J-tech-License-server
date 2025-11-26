"""
Enhanced Frame Manager - Multi-select, bulk operations, frame presets

Extends FrameManager with advanced frame management features.
"""

from typing import List, Optional, Set, Dict, Any
from PySide6.QtCore import QObject, Signal

from core.pattern import Frame, Pattern
from core.schemas.pattern_converter import PatternConverter
from domain.pattern_state import PatternState
from domain.frames import FrameManager


class EnhancedFrameManager(FrameManager):
    """
    Enhanced FrameManager with multi-select, bulk operations, and presets.
    """
    
    frames_selected = Signal(Set[int])  # Emitted when selection changes
    frames_bulk_updated = Signal()  # Emitted after bulk operations
    
    def __init__(self, state: PatternState):
        super().__init__(state)
        self._selected_indices: Set[int] = set()
        self._frame_presets: List[Frame] = []
        self._preset_names: List[str] = []  # Store preset names separately
    
    def select_multiple(self, indices: List[int]) -> None:
        """
        Select multiple frames.
        
        Args:
            indices: List of frame indices to select
        """
        pattern = self._state.pattern()
        valid_indices = {
            idx for idx in indices
            if 0 <= idx < len(pattern.frames)
        }
        
        if valid_indices != self._selected_indices:
            self._selected_indices = valid_indices
            self.frames_selected.emit(self._selected_indices)
    
    def get_selected_indices(self) -> Set[int]:
        """Get currently selected frame indices"""
        return self._selected_indices.copy()
    
    def clear_selection(self) -> None:
        """Clear frame selection"""
        if self._selected_indices:
            self._selected_indices.clear()
            self.frames_selected.emit(self._selected_indices)
    
    def add_to_selection(self, index: int) -> None:
        """Add frame to selection"""
        pattern = self._state.pattern()
        if 0 <= index < len(pattern.frames):
            self._selected_indices.add(index)
            self.frames_selected.emit(self._selected_indices)
    
    def remove_from_selection(self, index: int) -> None:
        """Remove frame from selection"""
        if index in self._selected_indices:
            self._selected_indices.remove(index)
            self.frames_selected.emit(self._selected_indices)
    
    def delete_selected(self) -> None:
        """Delete all selected frames"""
        if not self._selected_indices:
            return
        
        pattern = self._state.pattern()
        if len(pattern.frames) <= len(self._selected_indices):
            # Can't delete all frames
            return
        
        # Delete in reverse order to maintain indices
        sorted_indices = sorted(self._selected_indices, reverse=True)
        for idx in sorted_indices:
            if len(pattern.frames) > 1:
                del pattern.frames[idx]
        
        # Update current index
        if self._current_index >= len(pattern.frames):
            self._current_index = len(pattern.frames) - 1
        
        self._selected_indices.clear()
        self.frames_changed.emit()
        self.frame_index_changed.emit(self._current_index)
        self.frames_bulk_updated.emit()
    
    def duplicate_selected(self) -> None:
        """Duplicate all selected frames"""
        if not self._selected_indices:
            return
        
        pattern = self._state.pattern()
        new_indices = []
        
        # Duplicate in forward order
        sorted_indices = sorted(self._selected_indices)
        offset = 0
        
        for idx in sorted_indices:
            frame_copy = pattern.frames[idx].copy()
            insert_at = idx + 1 + offset
            pattern.frames.insert(insert_at, frame_copy)
            new_indices.append(insert_at)
            offset += 1
        
        # Update selection to new frames
        self._selected_indices = set(new_indices)
        self.frames_changed.emit()
        self.frames_selected.emit(self._selected_indices)
        self.frames_bulk_updated.emit()
    
    def set_duration_selected(self, duration_ms: int) -> None:
        """Set duration for all selected frames"""
        if not self._selected_indices:
            return
        
        pattern = self._state.pattern()
        for idx in self._selected_indices:
            if 0 <= idx < len(pattern.frames):
                pattern.frames[idx].duration_ms = duration_ms
                self.frame_duration_changed.emit(idx, duration_ms)
        
        self.frames_bulk_updated.emit()
    
    def copy_frame_sequence(self, start: int, end: int) -> List[Frame]:
        """
        Copy frame sequence for paste operation.
        
        Args:
            start: Start frame index
            end: End frame index (inclusive)
            
        Returns:
            List of copied frames
        """
        pattern = self._state.pattern()
        start = max(0, min(len(pattern.frames) - 1, start))
        end = max(start, min(len(pattern.frames) - 1, end))
        
        copied = []
        for idx in range(start, end + 1):
            copied.append(pattern.frames[idx].copy())
        
        return copied
    
    def paste_frame_sequence(self, frames: List[Frame], insert_at: Optional[int] = None) -> None:
        """
        Paste frame sequence.
        
        Args:
            frames: List of frames to paste
            insert_at: Insert position (uses current index if None)
        """
        if not frames:
            return
        
        pattern = self._state.pattern()
        if insert_at is None:
            insert_at = self._current_index + 1
        
        insert_at = max(0, min(len(pattern.frames), insert_at))
        
        # Insert frames
        for i, frame in enumerate(frames):
            pattern.frames.insert(insert_at + i, frame.copy())
        
        self._current_index = insert_at
        self.frames_changed.emit()
        self.frame_index_changed.emit(self._current_index)
        self.frames_bulk_updated.emit()
    
    def move_frames(self, src_indices: List[int], dest_index: int) -> None:
        """
        Move frames to new position.
        
        Args:
            src_indices: Source frame indices
            dest_index: Destination index
        """
        pattern = self._state.pattern()
        
        # Remove frames (in reverse order)
        sorted_src = sorted(src_indices, reverse=True)
        moved_frames = []
        for idx in sorted_src:
            if 0 <= idx < len(pattern.frames):
                moved_frames.insert(0, pattern.frames.pop(idx))
        
        # Insert at destination
        dest_index = max(0, min(len(pattern.frames), dest_index))
        for i, frame in enumerate(moved_frames):
            pattern.frames.insert(dest_index + i, frame)
        
        self._current_index = dest_index
        self.frames_changed.emit()
        self.frame_index_changed.emit(self._current_index)
        self.frames_bulk_updated.emit()
    
    def save_preset(self, name: str, frame: Frame) -> None:
        """Save frame as preset"""
        preset = frame.copy()
        self._frame_presets.append(preset)
        self._preset_names.append(name)
    
    def load_preset(self, preset_index: int, insert_at: Optional[int] = None) -> None:
        """Load frame preset"""
        if 0 <= preset_index < len(self._frame_presets):
            preset = self._frame_presets[preset_index].copy()
            self.paste_frame_sequence([preset], insert_at)
    
    def get_presets(self) -> List[str]:
        """Get list of preset names"""
        if len(self._preset_names) == len(self._frame_presets):
            return self._preset_names.copy()
        # Fallback if names don't match
        return [f"Preset {i+1}" for i in range(len(self._frame_presets))]
    
    def get_preset(self, index: int) -> Optional[Frame]:
        """Get preset frame by index"""
        if 0 <= index < len(self._frame_presets):
            return self._frame_presets[index].copy()
        return None
    
    def delete_preset(self, index: int) -> None:
        """Delete preset by index"""
        if 0 <= index < len(self._frame_presets):
            del self._frame_presets[index]
            if index < len(self._preset_names):
                del self._preset_names[index]
    
    def to_presets_dict(self) -> List[Dict[str, Any]]:
        """Convert presets to dictionary for saving"""
        presets = []
        for i, (preset, name) in enumerate(zip(self._frame_presets, self._preset_names)):
            presets.append({
                "name": name,
                "frame": PatternConverter.frame_to_json(preset),
                "index": i
            })
        return presets
    
    def load_presets_from_dict(self, presets_data: List[Dict[str, Any]]) -> None:
        """Load presets from dictionary"""
        self._frame_presets.clear()
        self._preset_names.clear()
        
        for preset_data in presets_data:
            name = preset_data.get("name", f"Preset {len(self._frame_presets) + 1}")
            frame_data = preset_data.get("frame", {})
            try:
                frame = PatternConverter.frame_from_json(frame_data)
                self._frame_presets.append(frame)
                self._preset_names.append(name)
            except Exception:
                # Skip invalid presets
                continue

