from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QEvent, QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QCursor,
    QHelpEvent,
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
        self._hover_layer_index: Optional[int] = None
        self._dragging_playhead = False
        self._selected_action_index: Optional[int] = None
        self._selected_layer_index: Optional[int] = None
        self._selected_indices: Set[int] = set()  # Multi-select support
        self._colors: Dict[str, QColor] = dict(self.DEFAULT_PALETTE)
        self._overlay_rects: List[Tuple[QRect, TimelineOverlay]] = []
        self._layer_track_rects: List[Tuple[QRect, int]] = []

    def sizeHint(self) -> QSize:
        width = int(self._frame_width() * max(1, len(self._frames)) + self.LANE_PADDING * 2)
        return QSize(width, self.FRAME_HEIGHT + self.LANE_PADDING * 2 + self._layer_tracks_height())

    # Data updates ------------------------------------------------------

    def set_frames(self, frames: List[Tuple[str, Optional[QPixmap]]]) -> None:
        self._frames = frames
        self._playhead_index = min(self._playhead_index, max(0, len(frames) - 1))
        self._update_geometry()

    def set_playhead(self, index: int) -> None:
        if not self._frames:
            return
        index = max(0, min(len(self._frames) - 1, index))
        if index != self._playhead_index:
            self._playhead_index = index
            self.update()

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

    # Interaction -------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:
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

    def set_selected_action(self, action_index: Optional[int]) -> None:
        if action_index is not None and action_index < 0:
            action_index = None
        self._selected_action_index = action_index
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

