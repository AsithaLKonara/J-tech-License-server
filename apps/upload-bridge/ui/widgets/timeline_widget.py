from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict

from PySide6.QtCore import QEvent, QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QCursor,
    QHelpEvent,
    QImage,
    QMouseEvent,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import QToolTip, QWidget


@dataclass
class TimelineMarker:
    frame_index: int
    label: str = ""
    color: QColor = field(default_factory=lambda: QColor("#7A7CFF"))


@dataclass
class TimelineOverlay:
    start_frame: int
    end_frame: int
    label: str
    color: QColor = field(default_factory=lambda: QColor("#4C8BF5"))
    action_index: int = -1
    tooltip: Optional[str] = None


@dataclass
class TimelineLayerTrack:
    """
    Represents a single layer row beneath the main timeline.
    - name: Human-readable layer name.
    - states: Per-frame state (0 = no layer, 1 = hidden, 2 = visible).
    """

    name: str
    states: List[int] = field(default_factory=list)
    color: QColor = field(default_factory=lambda: QColor("#3FB983"))


class TimelineWidget(QWidget):
    """
    Lightweight timeline visualisation for frame-based animations.
    Supports zooming, playhead display, markers, and automation overlays.
    """

    frameSelected = Signal(int)
    framesSelected = Signal(list)  # Multi-select frames
    playheadDragged = Signal(int)
    contextMenuRequested = Signal(int)
    overlayActivated = Signal(int)
    overlayContextMenuRequested = Signal(int, int)
    layerTrackSelected = Signal(int)
    # CapCut-style signals
    frameMoved = Signal(int, int)  # from_index, to_index
    frameDurationChanged = Signal(int, int)  # frame_index, duration_ms
    layerMoved = Signal(int, int)  # from_layer_index, to_layer_index
    layerVisibilityToggled = Signal(int)  # layer_index

    MIN_FRAME_WIDTH = 20
    BASE_FRAME_WIDTH = 40
    FRAME_HEIGHT = 80
    LANE_PADDING = 6
    TRACK_HEIGHT = 28
    TRACK_GAP = 6

    DEFAULT_PALETTE: Dict[str, QColor] = {
        "background": QColor("#171717"),
        "frame_bg": QColor("#1F1F1F"),
        "frame_hover": QColor("#2A2A2A"),
        "frame_border": QColor("#2E2E2E"),
        "text": QColor("#DDDDDD"),
        "secondary_text": QColor("#B5B5B5"),
        "no_frames_text": QColor("#777777"),
        "overlay_text": QColor("#F5F5F5"),
        "playhead": QColor("#4C8BF5"),
    }

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(self.FRAME_HEIGHT + self.LANE_PADDING * 2)
        self.setMouseTracking(True)
        self._zoom = 1.0
        self._frames: List[Tuple[str, Optional[QPixmap]]] = []
        self._playhead_index: int = 0
        self._markers: List[TimelineMarker] = []
        self._overlays: List[TimelineOverlay] = []
        self._layer_tracks: List[TimelineLayerTrack] = []
        self._hover_index: Optional[int] = None
        self._hover_overlay_index: Optional[int] = None
        self._highlighted_frames: Dict[int, QColor] = {}  # frame_index -> highlight color
        self._hover_layer_index: Optional[int] = None
        self._dragging_playhead = False
        self._selected_action_index: Optional[int] = None
        self._selected_layer_index: Optional[int] = None
        self._selected_indices: Set[int] = set()  # Multi-select support
        self._colors: Dict[str, QColor] = dict(self.DEFAULT_PALETTE)
        self._overlay_rects: List[Tuple[QRect, TimelineOverlay]] = []
        self._layer_track_rects: List[Tuple[QRect, int]] = []
        
        # CapCut-style grid rendering state
        self._grid_mode = False  # Enable grid mode (will be enabled by DesignToolsTab)
        self._layer_strip_width = 200  # Width of left sidebar for layer controls
        self._frame_durations: List[int] = []  # Duration in ms for each frame
        self._frame_positions: List[float] = []  # X positions for frames (cumulative duration)
        self._thumbnail_cache: Dict[Tuple[int, int], QPixmap] = {}  # (frame_index, layer_index) -> thumbnail
        self._composite_thumbnail_cache: Dict[int, QPixmap] = {}  # frame_index -> composite thumbnail
        
        # Drag-and-drop state
        self._dragging_frame: Optional[Tuple[int, int]] = None  # (frame_index, layer_index) or None
        self._drag_start_pos: Optional[QPoint] = None
        self._resizing_frame: Optional[Tuple[int, str]] = None  # (frame_index, 'left'|'right')
        self._resize_start_x: Optional[float] = None
        self._resize_start_duration: Optional[int] = None
        
        # Layer drag state
        self._dragging_layer: Optional[int] = None  # layer_index
        self._layer_drag_start_y: Optional[float] = None
        
        # Manager references
        self._frame_manager = None
        self._layer_manager = None
        
        # Layer strip rects for interaction
        self._layer_strip_rects: List[Optional[QRect]] = []

    def sizeHint(self) -> QSize:
        if self._grid_mode and self._layer_tracks:
            # Grid mode: calculate width based on cumulative duration
            self._calculate_frame_positions()
            if self._frame_positions:
                total_width = self._frame_positions[-1] + self._frame_width_at(len(self._frame_positions) - 1)
            else:
                total_width = self._frame_width() * max(1, len(self._frames))
            width = int(total_width + self._layer_strip_width + self.LANE_PADDING * 2)
            height = self.LANE_PADDING * 2 + len(self._layer_tracks) * (self.TRACK_HEIGHT + self.TRACK_GAP) + 20  # +20 for ruler
            return QSize(width, height)
        else:
            # Legacy mode
            width = int(self._frame_width() * max(1, len(self._frames)) + self.LANE_PADDING * 2)
            return QSize(width, self.FRAME_HEIGHT + self.LANE_PADDING * 2 + self._layer_tracks_height())

    # Data updates ------------------------------------------------------

    def set_frames(self, frames: List[Tuple[str, Optional[QPixmap]]]) -> None:
        self._frames = frames
        self._playhead_index = min(self._playhead_index, max(0, len(frames) - 1))
        self._update_geometry()
        self._invalidate_thumbnails()
    
    def highlight_frames(self, indices: List[int], color: QColor) -> None:
        """Highlight specified frames with given color."""
        for idx in indices:
            if 0 <= idx < len(self._frames):
                self._highlighted_frames[idx] = QColor(color)
        self.update()
    
    def clear_highlights(self) -> None:
        """Clear all frame highlights."""
        self._highlighted_frames.clear()
        self.update()
    
    def set_frame_durations(self, durations: List[int]) -> None:
        """Set frame durations for duration-based positioning."""
        self._frame_durations = durations
        self._calculate_frame_positions()
        self._update_geometry()
    
    def _invalidate_thumbnails(self) -> None:
        """Clear thumbnail cache when frames change."""
        self._thumbnail_cache.clear()
        self._composite_thumbnail_cache.clear()

    def set_playhead(self, index: int) -> None:
        if not self._frames:
            return
        index = max(0, min(len(self._frames) - 1, index))
        if index != self._playhead_index:
            self._playhead_index = index
            self.update()

    def ensure_marker_visible(self, index: int) -> None:
        """Scroll the parent scroll area to make the specified frame visible."""
        if not self._frames or index < 0 or index >= len(self._frames):
            return
            
        # Get frame X position
        if self._grid_mode and self._frame_positions:
            grid_start_x = self._layer_strip_width
            if index < len(self._frame_positions):
                frame_x = grid_start_x + self._frame_positions[index]
                frame_width = self._frame_width_at(index)
            else:
                return
        else:
            grid_start_x = self.LANE_PADDING
            frame_width = self._frame_width()
            frame_x = grid_start_x + index * frame_width
        
        # Find parent scroll area
        from PySide6.QtWidgets import QScrollArea
        parent = self.parent()
        while parent and not isinstance(parent, QScrollArea):
            parent = parent.parent()
            
        if parent:
            scroll_bar = parent.horizontalScrollBar()
            viewport_width = parent.viewport().width()
            current_scroll = scroll_bar.value()
            
            # Check if frame is outside viewport (with 50px padding)
            if frame_x < current_scroll + 50:
                scroll_bar.setValue(max(0, int(frame_x - 50)))
            elif frame_x + frame_width > current_scroll + viewport_width - 50:
                scroll_bar.setValue(int(frame_x + frame_width - viewport_width + 50))

    def set_zoom(self, zoom: float) -> None:
        self._zoom = max(0.25, min(zoom, 4.0))
        self._update_geometry()

    def set_markers(self, markers: List[TimelineMarker]) -> None:
        self._markers = markers
        self.update()

    def set_overlays(self, overlays: List[TimelineOverlay]) -> None:
        self._overlays = overlays
        self._overlay_rects = []
        self._hover_overlay_index = None
        if self._selected_action_index is not None:
            if not any(
                overlay.action_index == self._selected_action_index for overlay in overlays
            ):
                self._selected_action_index = None
        self.update()

    def set_layer_tracks(self, tracks: List[TimelineLayerTrack]) -> None:
        self._layer_tracks = tracks or []
        self._layer_track_rects = []
        if not self._layer_tracks:
            self._selected_layer_index = None
        else:
            if (
                self._selected_layer_index is None
                or self._selected_layer_index >= len(self._layer_tracks)
            ):
                self._selected_layer_index = 0
        self._update_geometry()

    def set_selected_layer(self, layer_index: Optional[int]) -> None:
        if layer_index is not None and (layer_index < 0 or layer_index >= len(self._layer_tracks)):
            layer_index = None
        if layer_index == self._selected_layer_index:
            return
        self._selected_layer_index = layer_index
        self.update()

    # Painting ----------------------------------------------------------

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), self._colors["background"])

        if not self._frames:
            painter.setPen(self._colors["no_frames_text"])
            painter.drawText(self.rect(), Qt.AlignCenter, "No frames")
            return

        # Use grid mode if enabled and we have layer tracks
        if self._grid_mode and self._layer_tracks:
            self._paint_grid_mode(painter)
        else:
            self._paint_legacy_mode(painter)
    
    def _paint_legacy_mode(self, painter: QPainter) -> None:
        """Original timeline rendering (for backward compatibility)."""
        frame_width = self._frame_width()
        x = self.LANE_PADDING
        y = self.LANE_PADDING

        # overlays background
        self._overlay_rects = []
        for idx_overlay, overlay in enumerate(self._overlays):
            start = max(overlay.start_frame, 0)
            end = min(overlay.end_frame, len(self._frames) - 1)
            left = x + start * frame_width
            right = x + (end + 1) * frame_width
            rect = QRect(int(left), y, int(right - left), self.FRAME_HEIGHT)
            if rect.width() <= 0:
                continue
            overlay_color = QColor(overlay.color)
            is_hovered = idx_overlay == self._hover_overlay_index
            is_selected = (
                overlay.action_index >= 0 and overlay.action_index == self._selected_action_index
            )
            fill_color = QColor(overlay_color)
            fill_color.setAlpha(150 if is_selected else 100 if is_hovered else 60)
            border_color = QColor(overlay_color)
            border_color.setAlpha(255 if is_selected else 220 if is_hovered else 140)
            painter.fillRect(rect, fill_color)
            painter.setPen(QPen(border_color, 2 if is_selected else 1))
            painter.drawRect(rect)
            if is_selected:
                highlight_color = QColor(self._colors["playhead"])
                highlight_color.setAlpha(220)
                painter.fillRect(rect.adjusted(0, 0, 0, -self.FRAME_HEIGHT + 6), highlight_color)
            if overlay.label:
                if is_selected:
                    text_color = self._colors["text"]
                elif is_hovered:
                    text_color = self._colors["text"]
                else:
                    text_color = self._colors["overlay_text"]
                painter.setPen(text_color)
                painter.drawText(rect.adjusted(4, 4, -4, -4), Qt.AlignLeft | Qt.AlignTop, overlay.label)
            self._overlay_rects.append((rect, overlay))

        for idx, (label, pixmap) in enumerate(self._frames):
            rect = QRect(int(x + idx * frame_width), y, int(frame_width), self.FRAME_HEIGHT)

            # background
            base_color = self._colors["frame_bg"] if idx != self._hover_index else self._colors["frame_hover"]
            painter.fillRect(rect.adjusted(1, 1, -1, -1), base_color)
            
            # Draw highlight if frame is highlighted
            if idx in self._highlighted_frames:
                highlight_color = QColor(self._highlighted_frames[idx])
                highlight_color.setAlpha(100)
                painter.fillRect(rect.adjusted(1, 1, -1, -1), highlight_color)
                # Draw border with highlight color
                border_color = QColor(self._highlighted_frames[idx])
                border_color.setAlpha(200)
                painter.setPen(QPen(border_color, 2))
                painter.drawRect(rect)
            else:
                painter.setPen(self._colors["frame_border"])
                painter.drawRect(rect)

            if pixmap:
                thumb_rect = rect.adjusted(6, 6, -6, -26)
                scaled = pixmap.scaled(thumb_rect.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_rect = QRect(
                    thumb_rect.left() + (thumb_rect.width() - scaled.width()) // 2,
                    thumb_rect.top() + (thumb_rect.height() - scaled.height()) // 2,
                    scaled.width(),
                    scaled.height(),
                )
                painter.drawPixmap(img_rect, scaled)

            painter.setPen(self._colors["text"])
            painter.drawText(rect.adjusted(4, rect.height() - 20, -4, -4), Qt.AlignLeft | Qt.AlignBottom, label)

        # markers
        for marker in self._markers:
            if 0 <= marker.frame_index < len(self._frames):
                left = x + marker.frame_index * frame_width
                marker_rect = QRect(int(left), y - 10, 12, 10)
                painter.fillRect(marker_rect, marker.color)
                painter.setPen(marker.color)
                painter.drawRect(marker_rect)
                if marker.label:
                    painter.setPen(self._colors["secondary_text"])
                    painter.drawText(marker_rect.translated(14, -2), Qt.AlignLeft | Qt.AlignTop, marker.label)

        # playhead
        playhead_x = x + self._playhead_index * frame_width
        playhead_color = self._colors["playhead"]
        pen = QPen(playhead_color, 2)
        painter.setPen(pen)
        painter.drawLine(int(playhead_x), y, int(playhead_x), y + self.FRAME_HEIGHT)
        painter.setBrush(playhead_color)
        painter.drawPolygon(
            [
                QPoint(int(playhead_x), y - 12),
                QPoint(int(playhead_x) - 6, y),
                QPoint(int(playhead_x) + 6, y),
            ]
        )

        # layer tracks
        track_y = y + self.FRAME_HEIGHT + self.TRACK_GAP
        self._layer_track_rects = []
        for idx_track, track in enumerate(self._layer_tracks):
            row_top = track_y + idx_track * (self.TRACK_HEIGHT + self.TRACK_GAP)
            track_width = int(frame_width * max(1, len(self._frames)))
            row_rect = QRect(
                self.LANE_PADDING,
                int(row_top),
                track_width,
                self.TRACK_HEIGHT,
            )
            self._layer_track_rects.append((row_rect, idx_track))

            base_color = QColor(self._colors["frame_bg"])
            base_color.setAlpha(80 if idx_track != self._selected_layer_index else 130)
            painter.fillRect(row_rect.adjusted(0, 0, 0, -1), base_color)
            painter.setPen(self._colors["frame_border"])
            painter.drawRect(row_rect)

            # Layer label
            label_rect = QRect(
                row_rect.left() + 4,
                row_rect.top() + 2,
                120,
                self.TRACK_HEIGHT - 4,
            )
            painter.setPen(self._colors["text"])
            painter.drawText(label_rect, Qt.AlignLeft | Qt.AlignVCenter, track.name)

            # Per-frame states
            for frame_idx in range(len(self._frames)):
                state = track.states[frame_idx] if frame_idx < len(track.states) else 0
                frame_rect = QRect(
                    int(self.LANE_PADDING + frame_idx * frame_width),
                    int(row_top),
                    int(frame_width),
                    self.TRACK_HEIGHT,
                )
                if state == 0:
                    continue  # No layer on this frame
                if state == 3:
                    fill = QColor(track.color)
                    fill.setAlpha(35)
                    painter.fillRect(frame_rect.adjusted(1, 1, -1, -1), fill)
                    painter.setPen(QPen(track.color, 1, Qt.DashLine))
                    painter.drawRect(frame_rect.adjusted(1, 1, -1, -1))
                    continue
                fill = QColor(track.color)
                if state == 1:
                    fill.setAlpha(70)  # Hidden
                else:
                    fill.setAlpha(150 if idx_track == self._selected_layer_index else 110)
                painter.fillRect(frame_rect.adjusted(1, 1, -1, -1), fill)
                painter.setPen(fill.darker(125))
                painter.drawRect(frame_rect.adjusted(1, 1, -1, -1))
    
    def _paint_grid_mode(self, painter: QPainter) -> None:
        """CapCut-style grid rendering: layers as rows, frames as columns."""
        # Calculate frame positions based on duration
        self._calculate_frame_positions()
        
        # Calculate dimensions
        layer_strip_width = self._layer_strip_width
        grid_start_x = layer_strip_width
        grid_y = self.LANE_PADDING + 20  # Space for ruler
        row_height = self.TRACK_HEIGHT
        row_gap = self.TRACK_GAP
        
        # Draw frame number ruler at top
        self._render_frame_ruler(painter, grid_start_x, self.LANE_PADDING)
        
        # Draw layer strips (left sidebar)
        self._render_layer_strips(painter, 0, grid_y, layer_strip_width, row_height, row_gap)
        
        # Draw grid with frame blocks
        self._render_grid(painter, grid_start_x, grid_y, row_height, row_gap)
        
        # Draw playhead across all layers
        if self._frame_positions and 0 <= self._playhead_index < len(self._frame_positions):
            playhead_x = grid_start_x + self._frame_positions[self._playhead_index]
            total_height = len(self._layer_tracks) * (row_height + row_gap) if self._layer_tracks else row_height
            self._render_playhead(painter, playhead_x, grid_y, total_height)
        
        # Draw drag feedback
        if self._dragging_frame:
            frame_idx, layer_idx = self._dragging_frame
            # Visual feedback will be handled in frame block rendering
            pass
    
    def _calculate_frame_positions(self) -> None:
        """Calculate X positions for frames based on cumulative duration."""
        if not self._frames:
            self._frame_positions = []
            return
        
        # Use durations if available, otherwise use default
        if not self._frame_durations or len(self._frame_durations) != len(self._frames):
            # Default: 100ms per frame, scaled by zoom
            base_duration = 100
            self._frame_durations = [base_duration] * len(self._frames)
        
        # Calculate positions: cumulative duration scaled by zoom
        positions = [0.0]
        duration_scale = self._zoom * 0.5  # Scale factor for duration to pixels
        for i, duration in enumerate(self._frame_durations):
            if i < len(self._frame_durations) - 1:
                positions.append(positions[-1] + duration * duration_scale)
        
        self._frame_positions = positions
    
    def _render_frame_ruler(self, painter: QPainter, start_x: float, y: float) -> None:
        """Render frame number ruler at top of timeline."""
        if not self._frame_positions:
            return
        
        # Draw ruler background
        ruler_height = 18
        ruler_rect = QRect(int(start_x), int(y), self.width() - int(start_x), ruler_height)
        bg_color = QColor(self._colors["frame_bg"])
        bg_color.setAlpha(150)
        painter.fillRect(ruler_rect, bg_color)
        painter.setPen(self._colors["frame_border"])
        painter.drawLine(ruler_rect.left(), ruler_rect.bottom(), ruler_rect.right(), ruler_rect.bottom())
        
        # Draw frame numbers
        painter.setPen(self._colors["secondary_text"])
        for i in range(len(self._frames)):
            if i < len(self._frame_positions):
                x = start_x + self._frame_positions[i]
                frame_width = self._frame_width_at(i)
                text_rect = QRect(int(x), int(y), int(frame_width), ruler_height)
                painter.drawText(text_rect, Qt.AlignCenter, f"F{i}")
    
    def _render_layer_strips(self, painter: QPainter, x: float, y: float, width: float, row_height: int, row_gap: int) -> None:
        """Render left sidebar with layer controls."""
        strip_x = int(x)
        strip_width = int(width)
        
        # Initialize layer strip rects list
        if len(self._layer_strip_rects) < len(self._layer_tracks):
            self._layer_strip_rects.extend([None] * (len(self._layer_tracks) - len(self._layer_strip_rects)))
        
        for idx, track in enumerate(self._layer_tracks):
            row_y = int(y + idx * (row_height + row_gap))
            strip_rect = QRect(strip_x, row_y, strip_width, row_height)
            
            # Background
            bg_color = QColor(self._colors["frame_bg"])
            if idx == self._selected_layer_index:
                bg_color.setAlpha(180)
            elif idx == self._hover_layer_index:
                bg_color.setAlpha(150)
            else:
                bg_color.setAlpha(120)
            painter.fillRect(strip_rect, bg_color)
            painter.setPen(self._colors["frame_border"])
            painter.drawRect(strip_rect)
            
            # Eye icon (visibility toggle) - check if any frame has this layer visible
            has_visible = track.states and any(s == 2 for s in track.states)
            eye_rect = QRect(strip_x + 4, row_y + 2, 20, row_height - 4)
            eye_color = self._colors["text"] if has_visible else QColor("#666666")
            painter.setPen(eye_color)
            # Use simple circle for eye icon
            painter.drawEllipse(eye_rect.adjusted(4, 4, -4, -4))
            if not has_visible:
                # Draw line through eye for hidden
                painter.drawLine(eye_rect.left() + 2, eye_rect.top() + 2, eye_rect.right() - 2, eye_rect.bottom() - 2)
            
            # Layer name
            name_rect = QRect(strip_x + 28, row_y + 2, strip_width - 32, row_height - 4)
            painter.setPen(self._colors["text"])
            painter.drawText(name_rect, Qt.AlignLeft | Qt.AlignVCenter, track.name)
            
            # Store strip rect for interaction
            self._layer_strip_rects[idx] = strip_rect
    
    def _render_grid(self, painter: QPainter, start_x: float, y: float, row_height: int, row_gap: int) -> None:
        """Render grid with frame blocks for each layer."""
        grid_x = int(start_x)
        
        # Ensure frame positions are calculated
        if not self._frame_positions or len(self._frame_positions) != len(self._frames):
            self._calculate_frame_positions()
        
        for layer_idx, track in enumerate(self._layer_tracks):
            row_y = int(y + layer_idx * (row_height + row_gap))
            
            # Draw frame blocks for this layer
            for frame_idx in range(len(self._frames)):
                if frame_idx < len(self._frame_positions):
                    # Calculate frame block position and width
                    frame_x = grid_x + int(self._frame_positions[frame_idx])
                    frame_width = self._frame_width_at(frame_idx)
                    
                    frame_rect = QRect(frame_x, row_y, int(frame_width), row_height)
                    
                    # Render frame block
                    self._render_frame_block(painter, frame_rect, frame_idx, layer_idx, track)
            
            # Draw grid lines between frames
            painter.setPen(QPen(self._colors["frame_border"], 1, Qt.DashLine))
            for frame_idx in range(len(self._frames)):
                if frame_idx < len(self._frame_positions):
                    frame_x = grid_x + int(self._frame_positions[frame_idx])
                    painter.drawLine(int(frame_x), row_y, int(frame_x), row_y + row_height)
    
    def _frame_width_at(self, frame_idx: int) -> float:
        """Get width of frame block based on duration."""
        if not self._frame_durations or frame_idx >= len(self._frame_durations):
            return self._frame_width()
        
        duration = self._frame_durations[frame_idx]
        duration_scale = self._zoom * 0.5
        width = max(self.MIN_FRAME_WIDTH, duration * duration_scale)
        return width
    
    def _render_frame_block(self, painter: QPainter, rect: QRect, frame_idx: int, layer_idx: int, track: TimelineLayerTrack) -> None:
        """Render a single frame block in the grid."""
        # Check if layer is visible for this frame
        state = track.states[frame_idx] if frame_idx < len(track.states) else 0
        if state == 0:
            return  # No layer on this frame
        
        # Determine colors based on state
        is_selected = frame_idx in self._selected_indices or frame_idx == self._playhead_index
        is_hovered = frame_idx == self._hover_index and layer_idx == self._hover_layer_index
        is_dragging = self._dragging_frame and self._dragging_frame[0] == frame_idx
        
        # Background
        bg_color = QColor(track.color)
        if state == 1:  # Hidden
            bg_color.setAlpha(50)
        elif is_selected:
            bg_color.setAlpha(200)
        elif is_dragging:
            bg_color.setAlpha(180)
        elif is_hovered:
            bg_color.setAlpha(150)
        else:
            bg_color.setAlpha(100)
        
        painter.fillRect(rect.adjusted(1, 1, -1, -1), bg_color)
        
        # Border
        border_color = track.color
        border_width = 2 if is_selected else 1
        if state != 2:
            border_color = QColor("#666666")
        else:
            # Darken the track color for border
            border_color = QColor(
                max(0, track.color.red() - 50),
                max(0, track.color.green() - 50),
                max(0, track.color.blue() - 50)
            )
        painter.setPen(QPen(border_color, border_width))
        painter.drawRect(rect)
        
        # Render composite thumbnail (from all visible layers)
        thumbnail = self._get_composite_frame_thumbnail(frame_idx)
        if thumbnail:
            thumb_rect = rect.adjusted(4, 4, -4, -20)
            scaled = thumbnail.scaled(thumb_rect.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            thumb_draw_rect = QRect(
                thumb_rect.left() + (thumb_rect.width() - scaled.width()) // 2,
                thumb_rect.top() + (thumb_rect.height() - scaled.height()) // 2,
                scaled.width(),
                scaled.height()
            )
            painter.drawPixmap(thumb_draw_rect, scaled)
        
        # Frame number label
        painter.setPen(self._colors["text"])
        painter.drawText(rect.adjusted(4, rect.height() - 16, -4, -4), Qt.AlignLeft | Qt.AlignBottom, f"F{frame_idx}")
        
        # Duration label
        if frame_idx < len(self._frame_durations):
            duration_ms = self._frame_durations[frame_idx]
            painter.setPen(self._colors["secondary_text"])
            painter.drawText(rect.adjusted(4, rect.height() - 16, -4, -4), Qt.AlignRight | Qt.AlignBottom, f"{duration_ms}ms")
        
        # Resize handle indicators
        if is_hovered or is_selected:
            # Draw small handles on edges
            handle_size = 4
            # Left edge
            if self._check_resize_edge(QPoint(rect.left(), rect.center().y()), frame_idx) == 'left':
                handle_rect = QRect(rect.left(), rect.center().y() - handle_size, 2, handle_size * 2)
                painter.fillRect(handle_rect, self._colors["playhead"])
            # Right edge
            if self._check_resize_edge(QPoint(rect.right(), rect.center().y()), frame_idx) == 'right':
                handle_rect = QRect(rect.right() - 2, rect.center().y() - handle_size, 2, handle_size * 2)
                painter.fillRect(handle_rect, self._colors["playhead"])
    
    def _get_composite_frame_thumbnail(self, frame_idx: int) -> Optional[QPixmap]:
        """Get composite thumbnail for frame (from frame data)."""
        if frame_idx < len(self._frames):
            _, pixmap = self._frames[frame_idx]
            return pixmap
        return None
    
    def _render_playhead(self, painter: QPainter, x: float, y: float, height: float) -> None:
        """Render vertical playhead line across all layers."""
        playhead_color = self._colors["playhead"]
        pen = QPen(playhead_color, 2)
        painter.setPen(pen)
        painter.drawLine(int(x), int(y), int(x), int(y + height))
        
        # Playhead triangle at top
        painter.setBrush(playhead_color)
        painter.drawPolygon([
            QPoint(int(x), int(y - 8)),
            QPoint(int(x) - 6, int(y)),
            QPoint(int(x) + 6, int(y)),
        ])
    
    
    def set_composite_thumbnail(self, frame_idx: int, thumbnail: QPixmap) -> None:
        """Set composite thumbnail for a frame (called from external code)."""
        self._composite_thumbnail_cache[frame_idx] = thumbnail
        self.update()
    
    def enable_grid_mode(self, enabled: bool = True) -> None:
        """Enable or disable CapCut-style grid mode."""
        self._grid_mode = enabled
        self._update_geometry()
    
    def set_frame_manager(self, frame_manager) -> None:
        """Set FrameManager for drag-and-drop operations."""
        self._frame_manager = frame_manager
        if frame_manager:
            # Connect signals
            self.frameMoved.connect(self._on_frame_moved)
            self.frameDurationChanged.connect(self._on_frame_duration_changed)
    
    def set_layer_manager(self, layer_manager) -> None:
        """Set LayerManager for layer operations."""
        self._layer_manager = layer_manager
        if layer_manager:
            # Connect signals
            self.layerMoved.connect(self._on_layer_moved)
    
    def _on_frame_moved(self, from_idx: int, to_idx: int) -> None:
        """Handle frame move from drag-and-drop."""
        if self._frame_manager:
            try:
                self._frame_manager.move(from_idx, to_idx)
                # Refresh timeline after move
                self.update()
            except Exception as e:
                import logging
                logging.exception(f"Error moving frame from {from_idx} to {to_idx}: {e}")
            # Update playhead if needed
            if self._playhead_index == from_idx:
                self.set_playhead(to_idx)
    
    def _on_frame_duration_changed(self, frame_idx: int, duration_ms: int) -> None:
        """Handle frame duration change from resize."""
        if self._frame_manager:
            self._frame_manager.set_duration(frame_idx, duration_ms)
            # Update local duration cache
            if frame_idx < len(self._frame_durations):
                self._frame_durations[frame_idx] = duration_ms
                self._calculate_frame_positions()
                self.update()
    
    def _on_layer_moved(self, from_idx: int, to_idx: int) -> None:
        """Handle layer move from drag-and-drop."""
        if self._layer_manager:
            # Get current frame index
            current_frame = 0
            if self._frame_manager:
                current_frame = self._frame_manager.current_index()
            self._layer_manager.move_layer(current_frame, from_idx, to_idx)
            # Update selected layer
            if self._selected_layer_index == from_idx:
                self.set_selected_layer(to_idx)

    # Interaction -------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._grid_mode and self._layer_tracks:
            self._handle_grid_mouse_press(event)
        else:
            self._handle_legacy_mouse_press(event)
    
    def _handle_grid_mouse_press(self, event: QMouseEvent) -> None:
        """Handle mouse press in grid mode."""
        pos = event.pos()
        
        # Check if clicking on eye icon in layer strip
        eye_layer_idx = self._grid_layer_strip_eye_at(pos)
        if eye_layer_idx is not None and event.button() == Qt.LeftButton:
            # Toggle layer visibility
            self.layerVisibilityToggled.emit(eye_layer_idx)
            return
        
        # Check if clicking on layer strip
        layer_idx = self._grid_layer_strip_at(pos)
        if layer_idx is not None:
            if event.button() == Qt.LeftButton:
                self.set_selected_layer(layer_idx)
                self.layerTrackSelected.emit(layer_idx)
                # Check if starting layer drag (not on eye icon)
                if eye_layer_idx is None and hasattr(self, '_layer_strip_rects') and layer_idx < len(self._layer_strip_rects):
                    self._dragging_layer = layer_idx
                    self._layer_drag_start_y = pos.y()
            return
        
        # Check if clicking on frame block
        frame_info = self._grid_frame_at(pos)
        if frame_info:
            frame_idx, layer_idx = frame_info
            
            if event.button() == Qt.LeftButton:
                # Check if clicking on resize edge
                resize_edge = self._check_resize_edge(pos, frame_idx)
                if resize_edge:
                    self._resizing_frame = (frame_idx, resize_edge)
                    self._resize_start_x = pos.x()
                    if frame_idx < len(self._frame_durations):
                        self._resize_start_duration = self._frame_durations[frame_idx]
                    self.setCursor(QCursor(Qt.SizeHorCursor))
                    return
                
                # Start frame drag
                self._dragging_frame = (frame_idx, layer_idx)
                self._drag_start_pos = pos
                
                # Handle selection
                modifiers = event.modifiers()
                if modifiers & Qt.ControlModifier or modifiers & Qt.MetaModifier:
                    if frame_idx in self._selected_indices:
                        self.remove_from_selection(frame_idx)
                    else:
                        self.add_to_selection(frame_idx)
                elif modifiers & Qt.ShiftModifier and self._selected_indices:
                    start_idx = min(min(self._selected_indices), frame_idx)
                    end_idx = max(max(self._selected_indices), frame_idx)
                    for i in range(start_idx, end_idx + 1):
                        self._selected_indices.add(i)
                    self.framesSelected.emit(sorted(list(self._selected_indices)))
                else:
                    self._selected_indices = {frame_idx}
                    self.framesSelected.emit([frame_idx])
                
                self.set_playhead(frame_idx)
                self.frameSelected.emit(frame_idx)
            elif event.button() == Qt.RightButton:
                self.contextMenuRequested.emit(frame_idx)
        else:
            # Clicked on empty space - might be playhead drag
            frame_idx = self._grid_frame_index_at_x(pos.x())
            if frame_idx is not None:
                self._dragging_playhead = True
                self.set_playhead(frame_idx)
                self.playheadDragged.emit(frame_idx)
    
    def _handle_legacy_mouse_press(self, event: QMouseEvent) -> None:
        """Handle mouse press in legacy mode."""
        overlay_idx = self._overlay_index_at(event.pos())
        layer_idx = self._layer_track_at(event.pos())
        if event.button() == Qt.LeftButton:
            if layer_idx is not None:
                self.set_selected_layer(layer_idx)
                self.layerTrackSelected.emit(layer_idx)
                return

            if overlay_idx is not None and 0 <= overlay_idx < len(self._overlays):
                overlay = self._overlays[overlay_idx]
                if overlay.action_index >= 0:
                    self.set_selected_action(overlay.action_index)
                    self.overlayActivated.emit(overlay.action_index)
                index = overlay.start_frame
            else:
                index = self._index_at(event.pos())
            if index is not None:
                # Multi-select support: Ctrl/Cmd for multi-select, Shift for range
                modifiers = event.modifiers()
                if modifiers & Qt.ControlModifier or modifiers & Qt.MetaModifier:
                    # Toggle selection
                    if index in self._selected_indices:
                        self.remove_from_selection(index)
                    else:
                        self.add_to_selection(index)
                elif modifiers & Qt.ShiftModifier and self._selected_indices:
                    # Range select
                    start_idx = min(min(self._selected_indices), index)
                    end_idx = max(max(self._selected_indices), index)
                    for i in range(start_idx, end_idx + 1):
                        self._selected_indices.add(i)
                    self.update()
                    self.framesSelected.emit(sorted(list(self._selected_indices)))
                else:
                    # Single select
                    self._selected_indices = {index}
                    self.update()
                    self.framesSelected.emit([index])
                
                self._dragging_playhead = True
                self.set_playhead(index)
                self.frameSelected.emit(index)
                self.playheadDragged.emit(index)
        elif event.button() == Qt.RightButton:
            if layer_idx is not None:
                self.set_selected_layer(layer_idx)
                self.layerTrackSelected.emit(layer_idx)
                return
            if overlay_idx is not None and 0 <= overlay_idx < len(self._overlays):
                overlay = self._overlays[overlay_idx]
                if overlay.action_index >= 0:
                    frame_index = self._index_at(event.pos())
                    if frame_index is None:
                        frame_index = overlay.start_frame
                    self.overlayContextMenuRequested.emit(overlay.action_index, frame_index)
                    return
            index = self._index_at(event.pos())
            if index is not None:
                self.contextMenuRequested.emit(index)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._grid_mode and self._layer_tracks:
            self._handle_grid_mouse_move(event)
        else:
            self._handle_legacy_mouse_move(event)
    
    def _handle_grid_mouse_move(self, event: QMouseEvent) -> None:
        """Handle mouse move in grid mode."""
        pos = event.pos()
        
        # Handle frame resize
        if self._resizing_frame:
            frame_idx, edge = self._resizing_frame
            if frame_idx < len(self._frame_durations) and self._resize_start_x is not None:
                delta_x = pos.x() - self._resize_start_x
                duration_scale = self._zoom * 0.5
                delta_duration = int(delta_x / duration_scale) if duration_scale > 0 else 0
                new_duration = max(10, self._resize_start_duration + delta_duration)
                self._frame_durations[frame_idx] = new_duration
                self._calculate_frame_positions()
                self.update()
            return
        
        # Handle frame drag
        if self._dragging_frame:
            frame_idx, layer_idx = self._dragging_frame
            # Find drop target
            drop_info = self._grid_frame_at(pos)
            if drop_info:
                drop_frame_idx, drop_layer_idx = drop_info
                if drop_frame_idx != frame_idx or drop_layer_idx != layer_idx:
                    # Visual feedback - will be handled in paintEvent
                    self.update()
            return
        
        # Handle layer drag
        if self._dragging_layer is not None:
            # Visual feedback - will be handled in paintEvent
            self.update()
            return
        
        # Handle playhead drag
        if self._dragging_playhead:
            frame_idx = self._grid_frame_index_at_x(pos.x())
            if frame_idx is not None:
                self.set_playhead(frame_idx)
                self.playheadDragged.emit(frame_idx)
            return
        
        # Update hover state
        frame_info = self._grid_frame_at(pos)
        layer_idx = self._grid_layer_strip_at(pos)
        
        needs_update = False
        if frame_info:
            frame_idx, _ = frame_info
            if frame_idx != self._hover_index:
                self._hover_index = frame_idx
                needs_update = True
            # Check if hovering over resize edge
            resize_edge = self._check_resize_edge(pos, frame_idx)
            if resize_edge:
                self.setCursor(QCursor(Qt.SizeHorCursor))
            else:
                self.setCursor(QCursor(Qt.ArrowCursor))
        else:
            if self._hover_index is not None:
                self._hover_index = None
                needs_update = True
            self.setCursor(QCursor(Qt.ArrowCursor))
        
        if layer_idx != self._hover_layer_index:
            self._hover_layer_index = layer_idx
            needs_update = True
        
        if needs_update:
            self.update()
    
    def _handle_legacy_mouse_move(self, event: QMouseEvent) -> None:
        """Handle mouse move in legacy mode."""
        index = self._index_at(event.pos())
        overlay_idx = self._overlay_index_at(event.pos())
        layer_idx = self._layer_track_at(event.pos())
        needs_update = False
        if index != self._hover_index:
            self._hover_index = index
            needs_update = True
        if overlay_idx != self._hover_overlay_index:
            self._hover_overlay_index = overlay_idx
            needs_update = True
        if layer_idx != self._hover_layer_index:
            self._hover_layer_index = layer_idx
            needs_update = True
        if needs_update:
            self.update()
        if self._dragging_playhead and index is not None:
            self.set_playhead(index)
            self.playheadDragged.emit(index)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            # Handle frame drag completion
            if self._dragging_frame:
                frame_idx, layer_idx = self._dragging_frame
                drop_info = self._grid_frame_at(event.pos())
                if drop_info:
                    drop_frame_idx, drop_layer_idx = drop_info
                    if drop_frame_idx != frame_idx:
                        # Emit signal for frame move
                        self.frameMoved.emit(frame_idx, drop_frame_idx)
                self._dragging_frame = None
                self._drag_start_pos = None
                self.update()
            
            # Handle frame resize completion
            if self._resizing_frame:
                frame_idx, _ = self._resizing_frame
                if frame_idx < len(self._frame_durations):
                    # Emit signal for duration change
                    self.frameDurationChanged.emit(frame_idx, self._frame_durations[frame_idx])
                self._resizing_frame = None
                self._resize_start_x = None
                self._resize_start_duration = None
                self.setCursor(QCursor(Qt.ArrowCursor))
                self.update()
            
            # Handle layer drag completion
            if self._dragging_layer is not None:
                drop_layer_idx = self._grid_layer_strip_at(event.pos())
                if drop_layer_idx is not None and drop_layer_idx != self._dragging_layer:
                    # Emit signal for layer move
                    self.layerMoved.emit(self._dragging_layer, drop_layer_idx)
                self._dragging_layer = None
                self._layer_drag_start_y = None
                self.update()
            
            self._dragging_playhead = False

    def leaveEvent(self, _event) -> None:
        self._hover_index = None
        self._hover_overlay_index = None
        self._hover_layer_index = None
        self._dragging_playhead = False
        self.update()

    # Helpers -----------------------------------------------------------

    def _frame_width(self) -> float:
        width = max(self.MIN_FRAME_WIDTH, self.BASE_FRAME_WIDTH * self._zoom)
        return width

    def _index_at(self, pos) -> Optional[int]:
        if not self._frames:
            return None
        frame_width = self._frame_width()
        timeline_rect = QRect(
            self.LANE_PADDING,
            self.LANE_PADDING,
            int(frame_width * len(self._frames)),
            self.FRAME_HEIGHT,
        )
        if not timeline_rect.contains(pos):
            return None
        relative_x = pos.x() - self.LANE_PADDING
        index = int(relative_x // frame_width)
        if 0 <= index < len(self._frames):
            return index
        return None

    def _update_geometry(self):
        self.updateGeometry()
        self.update()

    def _layer_tracks_height(self) -> int:
        if not self._layer_tracks:
            return 0
        return len(self._layer_tracks) * (self.TRACK_HEIGHT + self.TRACK_GAP) + self.TRACK_GAP

    # Theming ------------------------------------------------------------

    def apply_palette(self, palette: Dict[str, str]) -> None:
        """
        Apply a colour palette defined by hex strings or QColor objects.
        """

        def to_color(value) -> QColor:
            if isinstance(value, QColor):
                return value
            return QColor(value)

        resolved = dict(self.DEFAULT_PALETTE)
        for key, value in palette.items():
            if key in resolved and value is not None:
                resolved[key] = to_color(value)
        self._colors = resolved
        self.update()

    def _overlay_index_at(self, pos) -> Optional[int]:
        for idx, (rect, _overlay) in enumerate(self._overlay_rects):
            if rect.contains(pos):
                return idx
        return None

    def _layer_track_at(self, pos) -> Optional[int]:
        for rect, idx in self._layer_track_rects:
            if rect.contains(pos):
                return idx
        return None
    
    # Grid mode helpers --------------------------------------------------
    
    def _grid_frame_at(self, pos: QPoint) -> Optional[Tuple[int, int]]:
        """Find frame and layer at position in grid mode. Returns (frame_idx, layer_idx) or None."""
        if not self._frames or not self._layer_tracks:
            return None
        
        grid_start_x = self._layer_strip_width
        row_height = self.TRACK_HEIGHT
        row_gap = self.TRACK_GAP
        
        # Check if in grid area
        if pos.x() < grid_start_x:
            return None
        
        # Find layer row
        grid_y = self.LANE_PADDING
        relative_y = pos.y() - grid_y
        layer_idx = int(relative_y // (row_height + row_gap))
        
        if layer_idx < 0 or layer_idx >= len(self._layer_tracks):
            return None
        
        # Find frame column
        relative_x = pos.x() - grid_start_x
        frame_idx = self._grid_frame_index_at_x(pos.x())
        
        if frame_idx is not None:
            return (frame_idx, layer_idx)
        return None
    
    def _grid_frame_index_at_x(self, x: float) -> Optional[int]:
        """Find frame index at X position in grid mode."""
        if not self._frame_positions:
            return None
        
        grid_start_x = self._layer_strip_width
        relative_x = x - grid_start_x
        
        if relative_x < 0:
            return None
        
        # Find which frame this X position falls into
        for i in range(len(self._frame_positions)):
            frame_x = self._frame_positions[i]
            frame_width = self._frame_width_at(i)
            
            if frame_x <= relative_x < frame_x + frame_width:
                return i
        
        # Check if past last frame
        if len(self._frame_positions) > 0:
            last_frame_x = self._frame_positions[-1]
            last_frame_width = self._frame_width_at(len(self._frame_positions) - 1)
            if last_frame_x <= relative_x < last_frame_x + last_frame_width:
                return len(self._frame_positions) - 1
        
        return None
    
    def _grid_layer_strip_at(self, pos: QPoint) -> Optional[int]:
        """Find layer strip at position in grid mode."""
        if pos.x() >= self._layer_strip_width:
            return None
        
        grid_y = self.LANE_PADDING + 20  # Account for ruler
        row_height = self.TRACK_HEIGHT
        row_gap = self.TRACK_GAP
        
        relative_y = pos.y() - grid_y
        if relative_y < 0:
            return None
        
        layer_idx = int(relative_y // (row_height + row_gap))
        
        if 0 <= layer_idx < len(self._layer_tracks):
            return layer_idx
        return None
    
    def _grid_layer_strip_eye_at(self, pos: QPoint) -> Optional[int]:
        """Check if click is on eye icon in layer strip."""
        layer_idx = self._grid_layer_strip_at(pos)
        if layer_idx is None:
            return None
        
        if not hasattr(self, '_layer_strip_rects') or layer_idx >= len(self._layer_strip_rects):
            return None
        
        strip_rect = self._layer_strip_rects[layer_idx]
        if strip_rect is None:
            return None
        
        # Check if click is in eye icon area (first 28 pixels)
        eye_rect = QRect(strip_rect.left() + 4, strip_rect.top() + 2, 20, strip_rect.height() - 4)
        if eye_rect.contains(pos):
            return layer_idx
        return None
    
    def _check_resize_edge(self, pos: QPoint, frame_idx: int) -> Optional[str]:
        """Check if mouse is on frame resize edge. Returns 'left' or 'right' or None."""
        if frame_idx >= len(self._frame_positions) or not self._frame_positions:
            return None
        
        grid_start_x = self._layer_strip_width
        frame_x = grid_start_x + self._frame_positions[frame_idx]
        frame_width = self._frame_width_at(frame_idx)
        
        edge_threshold = 5  # pixels
        relative_x = pos.x() - frame_x
        
        if 0 <= relative_x < edge_threshold:
            return 'left'
        elif frame_width - edge_threshold < relative_x <= frame_width:
            return 'right'
        return None

    def set_selected_action(self, action_index: Optional[int]) -> None:
        if action_index is not None and action_index < 0:
            action_index = None
        self._selected_action_index = action_index
        self.update()
    
    def add_to_selection(self, index: int) -> None:
        """Add frame to selection."""
        if 0 <= index < len(self._frames):
            self._selected_indices.add(index)
            self.update()
    
    def remove_from_selection(self, index: int) -> None:
        """Remove frame from selection."""
        self._selected_indices.discard(index)
        self.update()

    def event(self, event) -> bool:
        if event.type() == QEvent.ToolTip and isinstance(event, QHelpEvent):
            overlay_idx = self._overlay_index_at(event.pos())
            if overlay_idx is not None and 0 <= overlay_idx < len(self._overlays):
                overlay = self._overlays[overlay_idx]
                tooltip_text = overlay.tooltip or overlay.label
                if tooltip_text:
                    QToolTip.showText(event.globalPos(), tooltip_text, self)
                else:
                    QToolTip.hideText()
            else:
                QToolTip.hideText()
            return True
        return super().event(event)

