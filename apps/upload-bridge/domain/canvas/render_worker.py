"""
Render Worker Thread - Offload heavy rendering operations to worker thread

Provides worker thread for rendering operations to prevent UI blocking.
"""

from typing import Optional, Deque
from collections import deque
from PySide6.QtCore import QThread, Signal, QMutex, QWaitCondition
from PySide6.QtGui import QImage

from core.pattern import Frame, Pattern
from domain.canvas.canvas_renderer import CanvasRenderer

MAX_FRAME_BUFFER_SIZE = 10  # Maximum frames in buffer


class RenderWorker(QThread):
    """
    Worker thread for rendering operations.
    
    Uses a bounded frame buffer queue to prevent memory buildup while
    keeping UI responsive.
    """
    
    frame_ready = Signal(QImage, int)  # image, frame_index
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._renderer = CanvasRenderer()
        self._frame_queue: Deque[Tuple[Frame, int, int, int, int, float]] = deque(maxlen=MAX_FRAME_BUFFER_SIZE)
        self._mutex = QMutex()
        self._condition = QWaitCondition()
        self._running = True
        self._pattern: Optional[Pattern] = None
        self._current_frame_index = 0
        self._pixel_size = 24
        self._zoom = 1.0
    
    def set_pattern(self, pattern: Pattern):
        """Set pattern for rendering"""
        self._mutex.lock()
        try:
            self._pattern = pattern
        finally:
            self._mutex.unlock()
    
    def request_frame(
        self,
        frame: Frame,
        width: int,
        height: int,
        pixel_size: int,
        zoom: float,
        frame_index: int
    ):
        """
        Request frame rendering.
        
        Args:
            frame: Frame to render
            width: Matrix width
            height: Matrix height
            pixel_size: Pixel size
            zoom: Zoom factor
            frame_index: Frame index
        """
        self._mutex.lock()
        try:
            # Add to queue (will drop oldest if full)
            self._frame_queue.append((frame, width, height, pixel_size, zoom, frame_index))
            self._condition.wakeOne()
        finally:
            self._mutex.unlock()
    
    def set_pixel_size(self, pixel_size: int):
        """Set pixel size"""
        self._mutex.lock()
        try:
            self._pixel_size = pixel_size
        finally:
            self._mutex.unlock()
    
    def set_zoom(self, zoom: float):
        """Set zoom factor"""
        self._mutex.lock()
        try:
            self._zoom = zoom
        finally:
            self._mutex.unlock()
    
    def stop(self):
        """Stop worker thread"""
        self._mutex.lock()
        try:
            self._running = False
            self._condition.wakeAll()
        finally:
            self._mutex.unlock()
        
        self.wait()
    
    def run(self):
        """Worker thread main loop"""
        while self._running:
            self._mutex.lock()
            try:
                if not self._frame_queue:
                    self._condition.wait(self._mutex, 100)  # Wait max 100ms
                    continue
                
                # Get next frame to render
                frame, width, height, pixel_size, zoom, frame_index = self._frame_queue.popleft()
            finally:
                self._mutex.unlock()
            
            # Render frame
            try:
                image = self._renderer.render_frame(
                    frame=frame,
                    width=width,
                    height=height,
                    pixel_size=pixel_size,
                    zoom=zoom
                )
                self.frame_ready.emit(image, frame_index)
            except Exception as e:
                # Log error but continue
                print(f"Render error: {e}")

