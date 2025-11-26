"""
Canvas Controller Component.

Handles canvas operations and pixel manipulation.
Extracted from DesignToolsTab to improve maintainability.
"""

from typing import Optional, Tuple
from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QWidget

from core.pattern import Pattern
from domain.pattern_state import PatternState
from domain.canvas import CanvasController


class CanvasControllerComponent(QObject):
    """
    Component for canvas operations.
    
    This component handles:
    - Canvas rendering
    - Pixel manipulation
    - Matrix size management
    - Color management
    """
    
    # Signals
    canvas_updated = Signal()
    pixel_changed = Signal(int, int, Tuple[int, int, int])  # x, y, color
    matrix_size_changed = Signal(int, int)  # width, height
    color_changed = Signal(Tuple[int, int, int])  # color
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the canvas controller component.
        
        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.pattern_state: Optional[PatternState] = None
        self.canvas_controller: Optional[CanvasController] = None
        self._current_color: Tuple[int, int, int] = (255, 255, 255)
    
    def set_pattern(self, pattern: Pattern) -> None:
        """
        Set the pattern for canvas operations.
        
        Args:
            pattern: Pattern to work with
        """
        self.pattern_state = PatternState(pattern)
        self.canvas_controller = CanvasController(self.pattern_state)
        
        # Connect canvas controller signals
        if self.canvas_controller:
            self.canvas_controller.frame_ready.connect(self._on_frame_ready)
    
    def set_matrix_size(self, width: int, height: int) -> None:
        """
        Set matrix size.
        
        Args:
            width: Matrix width
            height: Matrix height
        """
        if self.canvas_controller:
            self.canvas_controller.set_matrix_size(width, height)
            self.matrix_size_changed.emit(width, height)
    
    def set_current_color(self, color: Tuple[int, int, int]) -> None:
        """
        Set current drawing color.
        
        Args:
            color: RGB color tuple
        """
        self._current_color = color
        if self.canvas_controller:
            self.canvas_controller.set_current_color(color)
        self.color_changed.emit(color)
    
    def get_current_color(self) -> Tuple[int, int, int]:
        """
        Get current drawing color.
        
        Returns:
            Current RGB color tuple
        """
        return self._current_color
    
    def apply_pixel(
        self,
        x: int,
        y: int,
        frame_index: Optional[int] = None,
        color: Optional[Tuple[int, int, int]] = None
    ) -> bool:
        """
        Apply a pixel change.
        
        Args:
            x: X coordinate
            y: Y coordinate
            frame_index: Frame index (None = current)
            color: Color to apply (None = current color)
        
        Returns:
            True if pixel was applied
        """
        if not self.canvas_controller:
            return False
        
        if color is None:
            color = self._current_color
        
        try:
            if frame_index is None and self.pattern_state:
                frame_index = self.pattern_state.current_frame_index()
            
            # Use layer manager if available, otherwise direct pixel access
            # This is a simplified version - full implementation would use LayerManager
            self.pixel_changed.emit(x, y, color)
            self.canvas_updated.emit()
            return True
        except Exception:
            return False
    
    def render_frame(self, frame_index: int) -> Optional[object]:
        """
        Render a frame to canvas.
        
        Args:
            frame_index: Index of frame to render
        
        Returns:
            Rendered frame data or None
        """
        if not self.canvas_controller:
            return None
        
        try:
            return self.canvas_controller.render_frame(frame_index)
        except Exception:
            return None
    
    def get_matrix_size(self) -> Tuple[int, int]:
        """
        Get current matrix size.
        
        Returns:
            Tuple of (width, height)
        """
        if not self.pattern_state:
            return (0, 0)
        return (self.pattern_state.width(), self.pattern_state.height())
    
    def _on_frame_ready(self, frame_data: object) -> None:
        """Handle frame ready signal from canvas controller."""
        self.canvas_updated.emit()

