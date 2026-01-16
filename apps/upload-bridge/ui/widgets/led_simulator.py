"""
LED Simulator Widget - Real-time pattern preview
Complete PySide6 implementation - NO PLACEHOLDERS!
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from PySide6.QtCore import QTimer, QRect, Qt, Signal
from typing import List, Tuple
import sys
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.pattern import Pattern


class LEDSimulatorWidget(QWidget):
    """
    Real-time LED pattern preview widget
    
    Features:
    - Renders LED matrix/strip visually
    - Animates patterns at correct FPS
    - Play/pause/scrub controls
    - Brightness adjustment
    """
    
    # Signals
    frame_changed = Signal(int)  # Emitted when current frame changes
    playback_finished = Signal()  # Emitted when playback completes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Pattern data
        self.pattern: Pattern = None
        self.current_frame_idx = 0
        
        # Display settings
        self.led_width = 1
        self.led_height = 1
        self.cell_size = 15  # Pixels per LED
        self.spacing = 3     # Pixels between LEDs
        self.brightness_multiplier = 1.0
        
        # Current frame pixels
        self.current_pixels: List[Tuple[int, int, int]] = []
        
        # Animation state
        self.playing = False
        self.loop = True
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._advance_frame)
        
        # Widget settings
        self.setMinimumSize(400, 300)
        self.setStyleSheet("background-color: #1a1a1a;")
    
    def load_pattern(self, pattern: Pattern):
        """
        Load pattern for preview
        
        Args:
            pattern: Pattern object to display
        """
        self.pattern = pattern
        self.led_width = pattern.metadata.width
        self.led_height = pattern.metadata.height
        self.current_frame_idx = 0
        
        # Set brightness from pattern metadata
        self.brightness_multiplier = pattern.metadata.brightness
        
        # Display first frame
        if pattern.frames:
            self.set_frame(0)
        
        self.update()
    
    def set_frame(self, frame_idx: int):
        """
        Display specific frame
        
        Args:
            frame_idx: Index of frame to display
        """
        if not self.pattern or frame_idx < 0 or frame_idx >= self.pattern.frame_count:
            return
        
        self.current_frame_idx = frame_idx
        self.current_pixels = self.pattern.frames[frame_idx].pixels
        self.frame_changed.emit(frame_idx)
        self.update()
    
    def play(self):
        """Start playback"""
        if not self.pattern or self.pattern.frame_count == 0:
            return
        
        self.playing = True
        self._schedule_next_frame()
    
    def pause(self):
        """Pause playback"""
        self.playing = False
        self.timer.stop()
    
    def stop(self):
        """Stop and reset to first frame"""
        self.pause()
        self.set_frame(0)
    
    def set_brightness(self, brightness: float):
        """
        Set display brightness multiplier
        
        Args:
            brightness: 0.0 to 1.0
        """
        self.brightness_multiplier = max(0.0, min(1.0, brightness))
        self.update()
    
    def set_loop(self, loop: bool):
        """Enable/disable looping"""
        self.loop = loop
    
    def _schedule_next_frame(self):
        """Schedule next frame display"""
        if not self.pattern or not self.playing:
            return
        
        frame = self.pattern.frames[self.current_frame_idx]
        delay_ms = max(1, min(frame.duration_ms, 10000))  # Cap at 10 seconds
        
        self.timer.start(delay_ms)
    
    def _advance_frame(self):
        """Advance to next frame"""
        if not self.pattern or not self.playing:
            return
        
        # Move to next frame
        self.current_frame_idx += 1
        
        if self.current_frame_idx >= self.pattern.frame_count:
            if self.loop:
                self.current_frame_idx = 0
            else:
                # Playback finished
                self.playing = False
                self.playback_finished.emit()
                return
        
        # Display frame
        self.set_frame(self.current_frame_idx)
        
        # Schedule next
        self._schedule_next_frame()
    
    def paintEvent(self, event):
        """Render LED grid"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(26, 26, 26))
        
        if not self.current_pixels:
            # No pattern loaded - show placeholder
            painter.setPen(QPen(QColor(100, 100, 100)))
            painter.drawText(self.rect(), Qt.AlignCenter, "No pattern loaded")
            return
        
        # Calculate layout
        total_width = self.led_width * (self.cell_size + self.spacing) - self.spacing
        total_height = self.led_height * (self.cell_size + self.spacing) - self.spacing
        
        # Center in widget
        offset_x = (self.width() - total_width) // 2
        offset_y = (self.height() - total_height) // 2
        
        # Draw LEDs
        for idx, (r, g, b) in enumerate(self.current_pixels):
            if idx >= self.led_width * self.led_height:
                break
            
            # Calculate position
            x = idx % self.led_width
            y = idx // self.led_width
            
            px = offset_x + x * (self.cell_size + self.spacing)
            py = offset_y + y * (self.cell_size + self.spacing)
            
            # Apply brightness
            r = int(r * self.brightness_multiplier)
            g = int(g * self.brightness_multiplier)
            b = int(b * self.brightness_multiplier)
            
            # Draw LED body
            color = QColor(r, g, b)
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(60, 60, 60), 1))
            
            # Circle for LED
            painter.drawEllipse(px, py, self.cell_size, self.cell_size)
            
            # Highlight effect for bright LEDs
            brightness = (r + g + b) / 3
            if brightness > 128:
                highlight_size = self.cell_size // 3
                highlight_x = px + self.cell_size // 3
                highlight_y = py + self.cell_size // 3
                
                painter.setBrush(QBrush(QColor(255, 255, 255, 80)))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(highlight_x, highlight_y, highlight_size, highlight_size)
        
        # Draw frame info overlay
        if self.pattern:
            painter.setPen(QPen(QColor(200, 200, 200)))
            info_text = f"Frame {self.current_frame_idx + 1}/{self.pattern.frame_count}"
            painter.drawText(10, self.height() - 10, info_text)
    
    def sizeHint(self):
        """Suggested size for widget"""
        from PySide6.QtCore import QSize
        width = self.led_width * (self.cell_size + self.spacing) + 100
        height = self.led_height * (self.cell_size + self.spacing) + 100
        return QSize(max(400, width), max(300, height))

