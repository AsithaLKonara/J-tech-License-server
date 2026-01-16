"""
Lightweight procedural icon pack for Upload Bridge.

The design follows the visual spec (2 px stroke, rounded joins) and renders
icons on-demand so we avoid shipping binary assets.  Icons are cached per
name/size/colour to keep things fast.
"""

from __future__ import annotations

from math import cos, sin, radians
from typing import Callable, Dict, Tuple

from PySide6.QtCore import QPointF, QRectF, Qt, QSize
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap, QScreen, QGuiApplication

_ICON_CACHE: Dict[Tuple[str, int, str, float], QIcon] = {}


def get_device_pixel_ratio(widget=None) -> float:
    """
    Get device pixel ratio for HiDPI support.
    
    Args:
        widget: Optional widget to get DPR from (uses primary screen if None)
    
    Returns:
        Device pixel ratio (1.0 for standard, 2.0 for Retina, etc.)
    """
    if widget:
        # Try to get from widget's screen
        try:
            screen = widget.screen()
            if screen:
                return screen.devicePixelRatio()
        except Exception:
            pass
    
    # Fallback to primary screen
    try:
        app = QGuiApplication.instance()
        if app and app.primaryScreen():
            return app.primaryScreen().devicePixelRatio()
    except Exception:
        pass
    
    # Default fallback
    return 1.0


def available_icons() -> Tuple[str, ...]:
    """Return the list of icon ids provided by the pack."""
    return tuple(sorted(_DRAWERS.keys()))


def get_icon(
    name: str,
    size: int = 20,
    color: str | QColor = "#F5F5F5",
    device_pixel_ratio: float = None,
    widget=None,
) -> QIcon:
    """
    Render (or fetch cached) icon.

    Args:
        name: icon identifier (see `available_icons()`).
        size: logical size in pixels; artwork adapts automatically.
        color: stroke colour.
        device_pixel_ratio: allows crisp output on HiDPI displays (auto-detected if None).
        widget: Optional widget to detect DPR from (used if device_pixel_ratio is None).
    """
    # Auto-detect device pixel ratio if not provided
    if device_pixel_ratio is None:
        device_pixel_ratio = get_device_pixel_ratio(widget)
    
    if isinstance(color, QColor):
        color_name = color.name(QColor.HexArgb)
        qcolor = QColor(color)
    else:
        color_name = QColor(color).name(QColor.HexArgb)
        qcolor = QColor(color)

    key = (name, size, color_name, device_pixel_ratio)
    if key in _ICON_CACHE:
        return _ICON_CACHE[key]

    drawer = _DRAWERS.get(name, _draw_placeholder)

    pixmap = QPixmap(int(size * device_pixel_ratio), int(size * device_pixel_ratio))
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    pen = QPen(qcolor)
    pen.setWidthF(max(1.6, 2.0 * device_pixel_ratio))
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)

    logical_size = size * device_pixel_ratio
    drawer(painter, logical_size)

    painter.end()

    pixmap.setDevicePixelRatio(device_pixel_ratio)
    icon = QIcon(pixmap)
    _ICON_CACHE[key] = icon
    return icon


def _draw_placeholder(painter: QPainter, size: float) -> None:
    margin = size * 0.2
    rect = QRectF(margin, margin, size - 2 * margin, size - 2 * margin)
    painter.drawRoundedRect(rect, size * 0.15, size * 0.15)


def _draw_plus(painter: QPainter, size: float) -> None:
    c = size / 2
    length = size * 0.3
    painter.drawLine(QPointF(c - length, c), QPointF(c + length, c))
    painter.drawLine(QPointF(c, c - length), QPointF(c, c + length))


def _draw_duplicate(painter: QPainter, size: float) -> None:
    side = size * 0.36
    offset = size * 0.14
    rect_back = QRectF(size * 0.5 - side / 2 - offset, size * 0.5 - side / 2 - offset, side, side)
    rect_front = QRectF(size * 0.5 - side / 2 + offset * 0.3, size * 0.5 - side / 2 + offset * 0.3, side, side)
    painter.drawRoundedRect(rect_back, size * 0.08, size * 0.08)
    painter.drawRoundedRect(rect_front, size * 0.08, size * 0.08)


def _draw_trash(painter: QPainter, size: float) -> None:
    w = size * 0.4
    h = size * 0.45
    left = size * 0.5 - w / 2
    top = size * 0.4
    rect = QRectF(left, top, w, h)
    painter.drawRoundedRect(rect, size * 0.08, size * 0.08)
    painter.drawLine(QPointF(left - size * 0.08, top), QPointF(left + w + size * 0.08, top))
    painter.drawLine(QPointF(size * 0.5 - w * 0.25, size * 0.28), QPointF(size * 0.5 + w * 0.25, size * 0.28))


def _draw_arrow(painter: QPainter, size: float, direction: str) -> None:
    c = size / 2
    length = size * 0.32
    half = size * 0.18
    if direction == "up":
        painter.drawLine(QPointF(c, c + length / 2), QPointF(c, c - length / 2))
        painter.drawLine(QPointF(c, c - length / 2), QPointF(c - half, c - length / 2 + half))
        painter.drawLine(QPointF(c, c - length / 2), QPointF(c + half, c - length / 2 + half))
    elif direction == "down":
        painter.drawLine(QPointF(c, c - length / 2), QPointF(c, c + length / 2))
        painter.drawLine(QPointF(c, c + length / 2), QPointF(c - half, c + length / 2 - half))
        painter.drawLine(QPointF(c, c + length / 2), QPointF(c + half, c + length / 2 - half))
    elif direction == "left":
        painter.drawLine(QPointF(c + length / 2, c), QPointF(c - length / 2, c))
        painter.drawLine(QPointF(c - length / 2, c), QPointF(c - length / 2 + half, c - half))
        painter.drawLine(QPointF(c - length / 2, c), QPointF(c - length / 2 + half, c + half))
    else:  # right
        painter.drawLine(QPointF(c - length / 2, c), QPointF(c + length / 2, c))
        painter.drawLine(QPointF(c + length / 2, c), QPointF(c + length / 2 - half, c - half))
        painter.drawLine(QPointF(c + length / 2, c), QPointF(c + length / 2 - half, c + half))


def _draw_step(painter: QPainter, size: float, direction: str) -> None:
    _draw_arrow(painter, size, direction)
    c = size / 2
    length = size * 0.32
    if direction == "left":
        painter.drawLine(QPointF(c + length / 2, c - length / 2), QPointF(c + length / 2, c + length / 2))
    else:
        painter.drawLine(QPointF(c - length / 2, c - length / 2), QPointF(c - length / 2, c + length / 2))


def _draw_play(painter: QPainter, size: float) -> None:
    c = size / 2
    half = size * 0.22
    path = QPainterPath()
    path.moveTo(QPointF(c - half, c - half))
    path.lineTo(QPointF(c + half, c))
    path.lineTo(QPointF(c - half, c + half))
    path.closeSubpath()
    painter.save()
    painter.setBrush(painter.pen().color())
    painter.drawPath(path)
    painter.restore()


def _draw_pause(painter: QPainter, size: float) -> None:
    c = size / 2
    height = size * 0.36
    gap = size * 0.09
    painter.drawLine(QPointF(c - gap, c - height / 2), QPointF(c - gap, c + height / 2))
    painter.drawLine(QPointF(c + gap, c - height / 2), QPointF(c + gap, c + height / 2))


def _draw_stop(painter: QPainter, size: float) -> None:
    side = size * 0.32
    rect = QRectF(size / 2 - side / 2, size / 2 - side / 2, side, side)
    painter.save()
    painter.setBrush(painter.pen().color())
    painter.drawRoundedRect(rect, size * 0.08, size * 0.08)
    painter.restore()


def _draw_loop(painter: QPainter, size: float) -> None:
    c = size / 2
    radius = size * 0.28
    rect = QRectF(c - radius, c - radius, radius * 2, radius * 2)
    painter.drawArc(rect, int(40 * 16), int(260 * 16))
    angle = radians(-60)
    end = QPointF(c + radius * cos(angle), c - radius * sin(angle))
    wing = size * 0.12
    painter.drawLine(end, QPointF(end.x() + wing * 0.6, end.y() + wing))
    painter.drawLine(end, QPointF(end.x() - wing, end.y() + wing * 0.4))


def _draw_refresh(painter: QPainter, size: float) -> None:
    _draw_loop(painter, size)


def _draw_undo(painter: QPainter, size: float) -> None:
    c = size / 2
    radius = size * 0.28
    rect = QRectF(c - radius, c - radius, radius * 2, radius * 2)
    painter.drawArc(rect, int(200 * 16), int(200 * 16))
    start_angle = radians(200)
    start = QPointF(c + radius * cos(start_angle), c - radius * sin(start_angle))
    wing = size * 0.14
    painter.drawLine(start, QPointF(start.x() - wing, start.y() - wing * 0.2))
    painter.drawLine(start, QPointF(start.x() - wing * 0.2, start.y() + wing))


def _draw_redo(painter: QPainter, size: float) -> None:
    c = size / 2
    radius = size * 0.28
    rect = QRectF(c - radius, c - radius, radius * 2, radius * 2)
    painter.drawArc(rect, int(-20 * 16), int(-200 * 16))
    end_angle = radians(-20)
    end = QPointF(c + radius * cos(end_angle), c - radius * sin(end_angle))
    wing = size * 0.14
    painter.drawLine(end, QPointF(end.x() + wing, end.y() - wing * 0.2))
    painter.drawLine(end, QPointF(end.x() + wing * 0.2, end.y() + wing))


def _draw_target(painter: QPainter, size: float) -> None:
    c = size / 2
    radius = size * 0.22
    painter.drawEllipse(QPointF(c, c), radius, radius)
    painter.drawLine(QPointF(c - radius * 1.4, c), QPointF(c + radius * 1.4, c))
    painter.drawLine(QPointF(c, c - radius * 1.4), QPointF(c, c + radius * 1.4))


def _draw_brush(painter: QPainter, size: float) -> None:
    offset = size * 0.18
    start = QPointF(offset, size * 0.65)
    end = QPointF(size - offset, size * 0.35)
    painter.drawLine(start, end)
    tip_radius = size * 0.08
    painter.save()
    painter.setBrush(painter.pen().color())
    painter.drawEllipse(end, tip_radius, tip_radius * 1.2)
    painter.restore()


def _draw_layers_icon(painter: QPainter, size: float) -> None:
    base_w = size * 0.6
    base_h = size * 0.18
    for idx in range(3):
        y_offset = size * 0.18 * idx
        rect = QRectF(
            (size - base_w) / 2,
            (size - base_h) / 2 + y_offset - size * 0.18,
            base_w,
            base_h,
        )
        painter.drawRoundedRect(rect, size * 0.05, size * 0.05)


def _draw_automation(painter: QPainter, size: float) -> None:
    c = size / 2
    radius = size * 0.24
    painter.drawEllipse(QPointF(c, c), radius, radius)
    for angle in (0, 120, 240):
        rad = radians(angle)
        inner = QPointF(c + radius * cos(rad), c + radius * sin(rad))
        outer = QPointF(c + (radius + size * 0.14) * cos(rad), c + (radius + size * 0.14) * sin(rad))
        painter.drawLine(inner, outer)
    painter.save()
    painter.setBrush(painter.pen().color())
    painter.drawEllipse(QPointF(c, c), size * 0.08, size * 0.08)
    painter.restore()


def _draw_export(painter: QPainter, size: float) -> None:
    body = QRectF(size * 0.24, size * 0.28, size * 0.52, size * 0.46)
    painter.drawRoundedRect(body, size * 0.08, size * 0.08)
    arrow_start = QPointF(body.center().x(), body.top() - size * 0.12)
    arrow_end = QPointF(body.center().x(), body.top() - size * 0.32)
    painter.drawLine(arrow_start, arrow_end)
    wing = size * 0.12
    painter.drawLine(arrow_end, QPointF(arrow_end.x() - wing, arrow_end.y() + wing * 0.6))
    painter.drawLine(arrow_end, QPointF(arrow_end.x() + wing, arrow_end.y() + wing * 0.6))


def _draw_effects(painter: QPainter, size: float) -> None:
    c = size / 2
    outer = size * 0.32
    inner = size * 0.12
    points = []
    for i in range(8):
        angle_deg = 45 * i
        angle = radians(angle_deg)
        radius = outer if i % 2 == 0 else inner
        points.append(QPointF(c + radius * cos(angle), c + radius * sin(angle)))
    path = QPainterPath()
    path.moveTo(points[0])
    for point in points[1:]:
        path.lineTo(point)
    path.closeSubpath()
    painter.save()
    painter.setBrush(painter.pen().color())
    painter.drawPath(path)
    painter.restore()
    dots_radius = size * 0.04
    offsets = [(-outer * 0.6, -outer * 0.6), (outer * 0.6, -outer * 0.4), (-outer * 0.5, outer * 0.5)]
    for dx, dy in offsets:
        painter.drawEllipse(QPointF(c + dx, c + dy), dots_radius, dots_radius)


_DRAWERS: Dict[str, Callable[[QPainter, float], None]] = {
    "add": _draw_plus,
    "duplicate": _draw_duplicate,
    "delete": _draw_trash,
    "arrow-up": lambda p, s: _draw_arrow(p, s, "up"),
    "arrow-down": lambda p, s: _draw_arrow(p, s, "down"),
    "arrow-left": lambda p, s: _draw_arrow(p, s, "left"),
    "arrow-right": lambda p, s: _draw_arrow(p, s, "right"),
    "step-back": lambda p, s: _draw_step(p, s, "left"),
    "step-forward": lambda p, s: _draw_step(p, s, "right"),
    "play": _draw_play,
    "pause": _draw_pause,
    "stop": _draw_stop,
    "loop": _draw_loop,
    "refresh": _draw_refresh,
    "undo": _draw_undo,
    "redo": _draw_redo,
    "target": _draw_target,
    "brush": _draw_brush,
    "layers": _draw_layers_icon,
    "automation": _draw_automation,
    "export": _draw_export,
    "effects": _draw_effects,
}

