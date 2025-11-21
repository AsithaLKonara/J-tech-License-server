from __future__ import annotations

from typing import Dict, List, Tuple, Optional

from PySide6.QtCore import QObject, Signal

from domain.pattern_state import PatternState

Color = Tuple[int, int, int]


class ScratchpadMetadata:
    """Metadata for scratchpad entries"""
    def __init__(
        self,
        source_frame: Optional[int] = None,
        source_layer: Optional[int] = None,
        timestamp: Optional[str] = None,
        description: str = ""
    ):
        self.source_frame = source_frame
        self.source_layer = source_layer
        self.timestamp = timestamp
        self.description = description
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "source_frame": self.source_frame,
            "source_layer": self.source_layer,
            "timestamp": self.timestamp,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScratchpadMetadata':
        """Create from dictionary"""
        return cls(
            source_frame=data.get("source_frame"),
            source_layer=data.get("source_layer"),
            timestamp=data.get("timestamp"),
            description=data.get("description", "")
        )


class ScratchpadManager(QObject):
    """Manages up to N scratch buffers for quick copy/paste workflows with metadata."""

    scratchpad_changed = Signal(int)  # slot index

    def __init__(self, state: PatternState, max_slots: int = 10):
        super().__init__()
        self._state = state
        self._max_slots = max(1, max_slots)
        self._fallback_storage: Dict[str, List[Color]] = {}
        self._metadata_storage: Dict[str, ScratchpadMetadata] = {}

    @property
    def max_slots(self) -> int:
        return self._max_slots

    def slots(self) -> List[int]:
        return list(range(1, self._max_slots + 1))

    def is_slot_filled(self, slot: int) -> bool:
        storage = self._scratchpad_storage()
        return str(slot) in storage and len(storage[str(slot)]) > 0

    def copy_pixels(
        self,
        slot: int,
        pixels: List[Color],
        metadata: Optional[ScratchpadMetadata] = None
    ) -> None:
        """
        Store pixels in scratchpad with metadata.
        
        Args:
            slot: Scratchpad slot (1-max_slots)
            pixels: Pixel data to store
            metadata: Optional metadata (provenance)
        """
        from datetime import datetime
        
        storage = self._scratchpad_storage()
        storage[str(slot)] = list(pixels)
        
        # Store metadata
        if metadata is None:
            metadata = ScratchpadMetadata(
                timestamp=datetime.utcnow().isoformat() + 'Z'
            )
        else:
            if not metadata.timestamp:
                metadata.timestamp = datetime.utcnow().isoformat() + 'Z'
        
        self._metadata_storage[str(slot)] = metadata
        self.scratchpad_changed.emit(slot)
    
    def store(
        self,
        slot: int,
        pixels: List[Color],
        source_frame: Optional[int] = None,
        source_layer: Optional[int] = None,
        description: str = ""
    ) -> None:
        """
        Store pixels with metadata (convenience method).
        
        Args:
            slot: Scratchpad slot
            pixels: Pixel data
            source_frame: Source frame index
            source_layer: Source layer index
            description: Optional description
        """
        metadata = ScratchpadMetadata(
            source_frame=source_frame,
            source_layer=source_layer,
            description=description
        )
        self.copy_pixels(slot, pixels, metadata)
    
    def get_pixels(self, slot: int) -> Optional[List[Color]]:
        storage = self._scratchpad_storage()
        return list(storage.get(str(slot), []))
    
    def recall(self, slot: int) -> Optional[Tuple[List[Color], ScratchpadMetadata]]:
        """
        Recall pixels with metadata.
        
        Args:
            slot: Scratchpad slot
            
        Returns:
            Tuple of (pixels, metadata) or None if slot empty
        """
        pixels = self.get_pixels(slot)
        if pixels is None:
            return None
        
        metadata = self._metadata_storage.get(str(slot), ScratchpadMetadata())
        return (pixels, metadata)
    
    def get_metadata(self, slot: int) -> Optional[ScratchpadMetadata]:
        """Get metadata for scratchpad slot"""
        return self._metadata_storage.get(str(slot))

    def clear_slot(self, slot: int) -> None:
        storage = self._scratchpad_storage()
        if str(slot) in storage:
            del storage[str(slot)]
            self.scratchpad_changed.emit(slot)

    def _scratchpad_storage(self) -> Dict[str, List[Color]]:
        try:
            pattern = self._state.pattern()
        except RuntimeError:
            # During initial UI construction the pattern may not exist yet.
            # Return a local fallback so callers can safely treat slots as empty.
            return self._fallback_storage
        if not hasattr(pattern, "scratchpads") or pattern.scratchpads is None:
            pattern.scratchpads = {}
        return pattern.scratchpads

