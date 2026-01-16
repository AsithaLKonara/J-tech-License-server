"""
Gradient Editor Widget - Interactive multi-stop gradient editor.
"""

from PySide6.QtCore import Qt, Signal, QPoint, QRect, QSize
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QMouseEvent, QLinearGradient
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QColorDialog
from core.gradient import Gradient, GradientStop, GradientType
from typing import List, Optional, Tuple


class GradientEditorWidget(QWidget):
    """
    Interactive gradient editor with draggable stops.
    
    Features:
    - Visual gradient bar preview
    - Draggable stop markers
    - Click to add stop
    - Right-click to delete stop
    - Double-click to edit color
    """
    
    gradient_changed = Signal(object)  # Emits Gradient object
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._gradient: Optional[Gradient] = None
        self._selected_stop_index: Optional[int] = None
        self._dragging: bool = False
        self._bar_height = 20
        self._margin = 15
        
        self.setMinimumHeight(60)
        self.setMinimumWidth(200)
    
    def set_gradient(self, gradient: Gradient):
        """Set the gradient to edit."""
        self._gradient = gradient
        self.update()
    
    def get_gradient(self) -> Optional[Gradient]:
        """Get the current gradient."""
        return self._gradient
    
    def _get_bar_rect(self) -> QRect:
        """Calculate the rectangle for the gradient bar."""
        w = self.width() - 2 * self._margin
        return QRect(self._margin, self._margin, w, self._bar_height)
    
    def paintEvent(self, event):
        """Draw gradient bar and stop markers."""
        if not self._gradient:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        bar_rect = self._get_bar_rect()
        
        # Draw gradient bar
        grad = QLinearGradient(bar_rect.topLeft(), bar_rect.topRight())
        for stop in self._gradient.stops:
            grad.setColorAt(stop.position, QColor(*stop.color))
        
        painter.fillRect(bar_rect, grad)
        painter.setPen(QPen(Qt.black, 1))
        painter.drawRect(bar_rect)
        
        # Draw stop markers (triangles)
        for i, stop in enumerate(self._gradient.stops):
            x = bar_rect.x() + int(stop.position * bar_rect.width())
            y = bar_rect.y() + bar_rect.height() + 2
            
            # Highlight selected stop
            if i == self._selected_stop_index:
                painter.setPen(QPen(Qt.yellow, 2))
            else:
                painter.setPen(QPen(Qt.black, 1))
            
            painter.setBrush(QBrush(QColor(*stop.color)))
            
            # Draw triangle marker pointing up
            poly = [
                QPoint(x, y),
                QPoint(x - 6, y + 10),
                QPoint(x + 6, y + 10)
            ]
            painter.drawPolygon(poly)
            
            # Draw a small line connecting stop to bar for precision
            painter.setPen(QPen(Qt.black, 1))
            painter.drawLine(x, bar_rect.y() + bar_rect.height(), x, y)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle stop selection and addition."""
        if not self._gradient:
            return
        
        bar_rect = self._get_bar_rect()
        pos = event.position().toPoint()
        
        # Check if right click to delete
        if event.button() == Qt.RightButton:
            for i, stop in enumerate(self._gradient.stops):
                x = bar_rect.x() + int(stop.position * bar_rect.width())
                y = bar_rect.y() + bar_rect.height() + 2
                
                # Check hit box
                if abs(pos.x() - x) < 8 and y <= pos.y() <= y + 15:
                    if self._gradient.remove_stop(i):
                        self._selected_stop_index = None
                        self.update()
                        self.gradient_changed.emit(self._gradient)
                    return
            return

        # Check if clicking on existing stop to drag/select
        for i, stop in enumerate(self._gradient.stops):
            x = bar_rect.x() + int(stop.position * bar_rect.width())
            y = bar_rect.y() + bar_rect.height() + 2
            
            # Check hit box
            if abs(pos.x() - x) < 8 and y <= pos.y() <= y + 15:
                self._selected_stop_index = i
                self._dragging = True
                self.update()
                return
        
        # Check if clicking on bar (add new stop)
        if bar_rect.contains(pos):
            t = (pos.x() - bar_rect.x()) / bar_rect.width()
            t = max(0.0, min(1.0, t))
            color = self._gradient.get_color_at(t)
            self._gradient.add_stop(t, color)
            self._selected_stop_index = None # Reset selection to newly added stop? 
            # Find the new index
            for idx, s in enumerate(self._gradient.stops):
                if s.position == t:
                    self._selected_stop_index = idx
                    break
            
            self.update()
            self.gradient_changed.emit(self._gradient)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle stop dragging."""
        if self._dragging and self._selected_stop_index is not None and self._gradient:
            bar_rect = self._get_bar_rect()
            t = (event.position().x() - bar_rect.x()) / bar_rect.width()
            t = max(0.0, min(1.0, t))
            
            # Update position
            self._gradient.stops[self._selected_stop_index].position = t
            # Note: add_stop handles sorting, but here we are mutating. 
            # We should re-sort to keep logic consistent.
            self._gradient.stops = sorted(self._gradient.stops, key=lambda s: s.position)
            
            # Re-find selected index if it changed due to sorting
            for idx, s in enumerate(self._gradient.stops):
                if s.position == t:
                    self._selected_stop_index = idx
                    break
                    
            self.update()
            self.gradient_changed.emit(self._gradient)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """End dragging."""
        self._dragging = False
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Open color picker for stop."""
        if not self._gradient:
            return
            
        bar_rect = self._get_bar_rect()
        pos = event.position().toPoint()
        
        for i, stop in enumerate(self._gradient.stops):
            x = bar_rect.x() + int(stop.position * bar_rect.width())
            y = bar_rect.y() + bar_rect.height() + 2
            
            if abs(pos.x() - x) < 8 and y <= pos.y() <= y + 15:
                # Open color dialog
                color = QColorDialog.getColor(QColor(*stop.color), self, "Select Stop Color")
                if color.isValid():
                    stop.color = (color.red(), color.green(), color.blue())
                    self.update()
                    self.gradient_changed.emit(self._gradient)
                return
    
    def sizeHint(self) -> QSize:
        return QSize(250, 60)
