# Circular View & Canvas Matrix View - Full Specification

**Version**: 1.0  
**Date**: 2025-01-27  
**Status**: ✅ Complete Specification  
**Purpose**: Comprehensive technical specification for both Circular View and Canvas Matrix View systems

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Canvas Matrix View Specification](#canvas-matrix-view-specification)
3. [Circular View Specification](#circular-view-specification)
4. [Integration & Data Flow](#integration--data-flow)
5. [API Reference](#api-reference)
6. [Technical Details](#technical-details)
7. [Performance Characteristics](#performance-characteristics)

---

## Executive Summary

### Canvas Matrix View
- **Purpose**: Interactive LED matrix editor widget for pixel-by-pixel design
- **Type**: Editable, interactive canvas
- **Location**: `ui/widgets/matrix_design_canvas.py`
- **Key Features**: 8 drawing tools, zoom/pan, onion skinning, multi-layer support

### Circular View
- **Purpose**: Read-only circular preview of grid data
- **Type**: Read-only preview widget
- **Location**: `ui/widgets/circular_preview_canvas.py`
- **Key Principle**: "Circular View is a lens, not a new world"
- **Key Features**: Real-time updates, multiple layout types, mapping table-based rendering

---

## Canvas Matrix View Specification

### 1. Overview

**MatrixDesignCanvas** is the primary interactive editing widget for LED matrix patterns. It provides a pixel grid where users can paint, draw shapes, and edit frames.

### 2. Core Architecture

#### 2.1 Data Model

```python
# Internal Grid Storage
_grid: List[List[RGB]]  # 2D array: grid[y][x] = (r, g, b)
_matrix_width: int      # Grid width in pixels
_matrix_height: int     # Grid height in pixels
_pixel_size: int        # Visual pixel size in screen pixels
```

**Data Format**:
- **RGB**: `Tuple[int, int, int]` where each value is 0-255
- **Grid**: Row-major 2D list: `grid[y][x]`
- **Linear Export**: Row-major: `pixels[y * width + x]`

#### 2.2 Coordinate System

**Screen Coordinates** → **Grid Coordinates**:
```python
def _cell_from_point(self, point: QPoint) -> Tuple[int, int]:
    """Convert screen point to grid cell."""
    adjusted_x = point.x() - self._pan_offset.x()
    adjusted_y = point.y() - self._pan_offset.y()
    x = adjusted_x // self._pixel_size
    y = adjusted_y // self._pixel_size
    return x, y
```

**Grid Coordinates** → **Screen Coordinates**:
```python
# Screen X = grid_x * pixel_size + pan_offset.x()
# Screen Y = grid_y * pixel_size + pan_offset.y()
```

### 3. Drawing Tools

#### 3.1 Tool Enumeration

```python
class DrawingMode(Enum):
    PIXEL = "pixel"              # Single pixel painting
    RECTANGLE = "rectangle"      # Rectangle/square drawing
    CIRCLE = "circle"            # Circle/ellipse drawing
    LINE = "line"                # Straight line drawing
    RANDOM = "random"            # Random color spray
    GRADIENT = "gradient"        # Gradient color brush
    BUCKET_FILL = "bucket_fill"  # Flood fill
    EYEDROPPER = "eyedropper"    # Color picker
```

#### 3.2 Pixel Tool

**Purpose**: Paint individual pixels or brush-sized areas

**Behavior**:
1. User clicks/drags on canvas
2. Calculates grid position from mouse coordinates
3. Applies brush size (1×1 to 8×8 pixels)
4. Updates pixel(s) in grid
5. Emits `pixel_updated(x, y, color)` signal

**Brush Size**:
- Range: 1-8 pixels
- Shape: Square (brush_size × brush_size)
- Applied symmetrically around click point

**Implementation**:
```python
def _handle_paint_event(self, point: QPoint, button: Qt.MouseButton):
    cell = self._cell_from_point(point)
    x, y = cell
    
    color = self._erase_color if button == Qt.RightButton else self._current_color
    
    # Apply brush size
    brush_half = self._brush_size // 2
    for dy in range(-brush_half, brush_half + 1):
        for dx in range(-brush_half, brush_half + 1):
            px, py = x + dx, y + dy
            if 0 <= px < self._matrix_width and 0 <= py < self._matrix_height:
                self._grid[py][px] = color
                self.pixel_updated.emit(px, py, color)
```

#### 3.3 Rectangle Tool

**Purpose**: Draw filled or outlined rectangles

**Behavior**:
1. User clicks to set start point
2. Drags to set end point
3. Preview shown while dragging (non-destructive)
4. On mouse release, commits rectangle to grid

**Modes**:
- **Filled**: All pixels within rectangle filled
- **Outline**: Only border pixels drawn

**Implementation**:
```python
def _draw_rectangle(self, x1: int, y1: int, x2: int, y2: int, 
                   color: RGB, preview: bool = False):
    x_min, x_max = min(x1, x2), max(x1, x2)
    y_min, y_max = min(y1, y2), max(y1, y2)
    
    if self._shape_filled:
        # Fill entire rectangle
        for y in range(y_min, y_max + 1):
            for x in range(x_min, x_max + 1):
                if 0 <= x < self._matrix_width and 0 <= y < self._matrix_height:
                    target_grid[y][x] = color
    else:
        # Outline only
        for y in range(y_min, y_max + 1):
            for x in range(x_min, x_max + 1):
                if (x == x_min or x == x_max or y == y_min or y == y_max):
                    if 0 <= x < self._matrix_width and 0 <= y < self._matrix_height:
                        target_grid[y][x] = color
```

#### 3.4 Circle Tool

**Purpose**: Draw filled or outlined circles/ellipses

**Behavior**:
1. User clicks to set center
2. Drags to set radius
3. Preview shown while dragging
4. On release, commits circle to grid

**Algorithm**: Ellipse equation: `(dx/rx)² + (dy/ry)² ≤ 1.0`

**Implementation**:
```python
def _draw_circle(self, x1: int, y1: int, x2: int, y2: int, 
                color: RGB, preview: bool = False):
    center_x = (x1 + x2) // 2
    center_y = (y1 + y2) // 2
    radius_x = abs(x2 - x1) // 2
    radius_y = abs(y2 - y1) // 2
    
    if self._shape_filled:
        for y in range(self._matrix_height):
            for x in range(self._matrix_width):
                dx = (x - center_x) / max(1, radius_x)
                dy = (y - center_y) / max(1, radius_y)
                if dx*dx + dy*dy <= 1.0:
                    target_grid[y][x] = color
```

#### 3.5 Line Tool

**Purpose**: Draw straight lines

**Behavior**:
1. User clicks to set start point
2. Drags to set end point
3. Preview shown while dragging
4. On release, commits line using Bresenham algorithm

**Algorithm**: Bresenham's line algorithm for pixel-perfect lines

**Implementation**:
```python
def _draw_line(self, x1: int, y1: int, x2: int, y2: int, 
              color: RGB, preview: bool = False):
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy
    
    x, y = x1, y1
    while True:
        if 0 <= x < self._matrix_width and 0 <= y < self._matrix_height:
            target_grid[y][x] = color
        
        if x == x2 and y == y2:
            break
        
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy
```

#### 3.6 Bucket Fill Tool

**Purpose**: Fill connected regions with color

**Behavior**:
1. User clicks on pixel
2. Flood fill algorithm finds connected pixels
3. Fills with configurable tolerance (color similarity)
4. Updates all connected pixels

**Tolerance**: 0-255 (0 = exact match, 255 = fill all)

**Algorithm**: BFS (Breadth-First Search) flood fill

**Implementation**:
```python
def _flood_fill(self, x: int, y: int, target_color: RGB, 
                fill_color: RGB, tolerance: int) -> List[Tuple[int, int, RGB]]:
    def colors_match(c1: RGB, c2: RGB, tol: int) -> bool:
        if tol == 0:
            return c1 == c2
        r1, g1, b1 = c1
        r2, g2, b2 = c2
        return (abs(r1 - r2) <= tol and 
               abs(g1 - g2) <= tol and 
               abs(b1 - b2) <= tol)
    
    filled_pixels = []
    visited = set()
    queue = deque([(x, y)])
    
    while queue:
        cx, cy = queue.popleft()
        if (cx, cy) in visited:
            continue
        if not (0 <= cx < self._matrix_width and 0 <= cy < self._matrix_height):
            continue
        
        current_color = self._grid[cy][cx]
        if not colors_match(current_color, target_color, tolerance):
            continue
        
        self._grid[cy][cx] = fill_color
        filled_pixels.append((cx, cy, fill_color))
        visited.add((cx, cy))
        
        # Add neighbors
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            queue.append((cx + dx, cy + dy))
    
    return filled_pixels
```

#### 3.7 Gradient Tool

**Purpose**: Paint with interpolated gradient colors

**Behavior**:
1. User configures start/end colors
2. Sets gradient steps (2-32)
3. Paints with colors interpolated between start/end
4. Cycles through gradient as user paints

**Color Interpolation**: Linear RGB interpolation

**Implementation**:
```python
def set_gradient_brush(self, start: RGB, end: RGB, steps: int):
    self._gradient_start = start
    self._gradient_end = end
    self._gradient_steps = max(2, steps)
    self._gradient_step_index = 0

def _next_gradient_color(self) -> RGB:
    t = (self._gradient_step_index % self._gradient_steps) / (self._gradient_steps - 1)
    r = int(self._gradient_start[0] + (self._gradient_end[0] - self._gradient_start[0]) * t)
    g = int(self._gradient_start[1] + (self._gradient_end[1] - self._gradient_start[1]) * t)
    b = int(self._gradient_start[2] + (self._gradient_end[2] - self._gradient_start[2]) * t)
    self._gradient_step_index += 1
    return (r, g, b)
```

#### 3.8 Random Tool

**Purpose**: Spray random colors from palette

**Behavior**:
1. User configures color palette
2. Clicks/drags on canvas
3. Random colors from palette applied
4. Density controlled by brush size

**Implementation**:
```python
def set_random_palette(self, palette: List[RGB]):
    if palette:
        self._random_palette = [self._clamp_color(color) for color in palette]

def _get_random_color(self) -> RGB:
    if self._random_palette:
        return random.choice(self._random_palette)
    return self._current_color
```

#### 3.9 Eyedropper Tool

**Purpose**: Pick color from canvas

**Behavior**:
1. User clicks on pixel
2. Reads color from that pixel
3. Emits `color_picked(r, g, b)` signal
4. Updates current color in color picker

**Implementation**:
```python
def _pick_color_at(self, x: int, y: int) -> Optional[RGB]:
    if not (0 <= x < self._matrix_width and 0 <= y < self._matrix_height):
        return None
    return self._grid[y][x]
```

### 4. Visual Features

#### 4.1 Pixel Rendering

**Shapes**:
- **Square**: Standard square pixels
- **Round**: Circular pixels (ellipse)
- **Rounded**: Rounded rectangle pixels

**Borders**:
- Width: 0-3 pixels
- Color: Configurable (default: dark gray)

**Implementation**:
```python
def _draw_pixel_tile(self, painter: QPainter, rect_x: int, rect_y: int, 
                     rect_w: int, rect_h: int, color: RGB):
    painter.setBrush(QBrush(QColor(*color)))
    
    if self._border_width > 0:
        painter.setPen(QPen(self._pixel_border_color, self._border_width))
    else:
        painter.setPen(Qt.NoPen)
    
    if self._pixel_shape == PixelShape.ROUND:
        painter.drawEllipse(rect_x, rect_y, rect_w, rect_h)
    elif self._pixel_shape == PixelShape.ROUNDED:
        radius = max(2, min(rect_w, rect_h) // 3)
        painter.drawRoundedRect(QRectF(rect_x, rect_y, rect_w, rect_h), radius, radius)
    else:
        painter.drawRect(rect_x, rect_y, rect_w, rect_h)
```

#### 4.2 Zoom & Pan

**Zoom Levels**: 25% - 300% (0.25x - 3.0x)

**Controls**:
- Zoom slider (25%-300%)
- Mouse wheel zoom (Ctrl+Wheel)
- Keyboard shortcuts (Ctrl+0 = reset, Ctrl+1 = fit to window)
- Pan with middle-click drag

**Implementation**:
```python
def set_zoom_factor(self, factor: float) -> None:
    factor = max(0.25, min(3.0, factor))
    self._pixel_size = int(self._base_pixel_size * factor)
    self._zoom_level = factor
    self.updateGeometry()
    self.update()

def wheelEvent(self, event):
    delta = event.angleDelta().y()
    if delta > 0:
        self._zoom_level = min(3.0, self._zoom_level * 1.1)
    else:
        self._zoom_level = max(0.25, self._zoom_level * 0.9)
    self._pixel_size = int(self._base_pixel_size * self._zoom_level)
    self.updateGeometry()
    self.update()
```

#### 4.3 Onion Skinning

**Purpose**: Show previous/next frames for animation reference

**Features**:
- Multiple previous frames (configurable count)
- Multiple next frames (configurable count)
- Per-frame opacity control (0.0-1.0)
- Semi-transparent rendering

**Implementation**:
```python
def set_onion_skin_frames(
    self,
    prev_frames: List[List[List[RGB]]],
    next_frames: List[List[List[RGB]]],
    prev_opacities: List[float],
    next_opacities: List[float]
) -> None:
    self._onion_skin_prev_frames = prev_frames
    self._onion_skin_next_frames = next_frames
    self._onion_skin_prev_opacities = prev_opacities
    self._onion_skin_next_opacities = next_opacities
    self.update()

def _draw_onion_skins(self, painter: QPainter):
    # Draw previous frames (behind current)
    for prev_grid, opacity in zip(self._onion_skin_prev_frames, self._onion_skin_prev_opacities):
        if opacity <= 0.0:
            continue
        for y in range(min(len(prev_grid), self._matrix_height)):
            for x in range(min(len(prev_grid[y]), self._matrix_width)):
                color = prev_grid[y][x]
                qcolor = QColor(*color)
                qcolor.setAlphaF(opacity)
                # Draw with reduced opacity
                # ...
    
    # Draw next frames (similar)
```

#### 4.4 Geometry Overlays

**Purpose**: Visualize different layout types and wiring

**Types**:
- **Matrix**: Standard rectangular grid
- **Circle**: Circular LED arrangement overlay
- **Ring**: Ring/annulus arrangement overlay
- **Radial**: Radial spoke arrangement overlay

**Features**:
- Circular bounds outline
- Active cell highlighting (green overlay)
- Inactive cell dimming (gray overlay)
- LED index numbers (optional)
- Wiring path visualization

**Implementation**:
```python
def _draw_geometry_overlay(self, painter: QPainter):
    if not self._pattern_metadata:
        return
    
    layout_type = getattr(self._pattern_metadata, 'layout_type', 'rectangular')
    
    if layout_type != "rectangular":
        # Dim unmapped cells
        for y in range(self._matrix_height):
            for x in range(self._matrix_width):
                if not CircularMapper.is_mapped(x, y, self._pattern_metadata):
                    # Dim unmapped cell
                    # ...
        
        # Draw circular bounds
        if layout_type == "circle":
            painter.drawEllipse(bounds)
        elif layout_type == "ring":
            painter.drawEllipse(bounds)
            # Draw inner circle
            # ...
        elif layout_type == "arc":
            # Draw arc based on angles
            # ...
    
    # Draw wiring overlay
    if hasattr(self._pattern_metadata, 'wiring_mode'):
        self._draw_wiring_overlay(painter, bounds)
```

#### 4.5 Wiring Overlay

**Purpose**: Show physical LED strip wiring order

**Features**:
- Supports Row-major, Serpentine, Column-major wiring modes
- Shows data flow direction with arrows
- LED index labels (first 50 LEDs)
- Color-coded path (yellow/orange)
- Start point (green) and end point (red) markers

**Implementation**:
```python
def _draw_wiring_overlay(self, painter: QPainter, bounds):
    from core.wiring_mapper import WiringMapper
    
    wiring_mode = getattr(self._pattern_metadata, 'wiring_mode', 'Row-major')
    mapper = WiringMapper(
        width=self._pattern_metadata.width,
        height=self._pattern_metadata.height,
        wiring_mode=wiring_mode,
        data_in_corner=getattr(self._pattern_metadata, 'data_in_corner', 'LT')
    )
    
    mapping = mapper._build_mapping_table()
    
    # Draw wiring path
    wiring_pen = QPen(QColor(255, 200, 0, 150), 2)
    prev_x, prev_y = None, None
    
    for hw_idx in range(len(mapping)):
        design_idx = mapping[hw_idx]
        grid_x = design_idx % self._pattern_metadata.width
        grid_y = design_idx // self._pattern_metadata.width
        
        x = bounds.x() + (grid_x + 0.5) * cell_width
        y = bounds.y() + (grid_y + 0.5) * cell_height
        
        if prev_x is not None:
            painter.drawLine(int(prev_x), int(prev_y), int(x), int(y))
        
        prev_x, prev_y = x, y
```

### 5. Signals & Events

#### 5.1 Signals

```python
pixel_updated = Signal(int, int, tuple)      # x, y, (r, g, b)
hover_changed = Signal(int, int)              # x, y under cursor (or -1, -1)
painting_finished = Signal()                 # Emitted when mouse released
color_picked = Signal(int, int, int)         # r, g, b from eyedropper
```

#### 5.2 Mouse Events

- **Left Click**: Paint with current color
- **Right Click**: Erase (paint with erase color)
- **Middle Click + Drag**: Pan canvas
- **Wheel**: Zoom in/out
- **Hover**: Show pixel coordinates

### 6. Public API

#### 6.1 Pixel Management

```python
def set_matrix_size(self, width: int, height: int, default_color: RGB = (0, 0, 0))
def get_grid_data(self) -> List[List[RGB]]
def set_frame_pixels(self, pixels: List[RGB])
def to_pixels(self) -> List[RGB]
```

#### 6.2 Drawing Configuration

```python
def set_drawing_mode(self, mode: DrawingMode)
def set_current_color(self, color: RGB)
def set_erase_color(self, color: RGB)
def set_brush_size(self, size: int)
def get_brush_size(self) -> int
def set_shape_filled(self, filled: bool)
```

#### 6.3 Visual Settings

```python
def set_pixel_shape(self, shape: PixelShape | str)
def set_geometry_overlay(self, mode: GeometryOverlay | str)
def set_border_width(self, width: int)
def set_pattern_metadata(self, metadata: Optional[PatternMetadata])
```

#### 6.4 Zoom/Pan

```python
def set_zoom_factor(self, factor: float) -> None
def reset_zoom(self) -> None
```

#### 6.5 Onion Skinning

```python
def set_onion_skin_frames(
    self,
    prev_frames: List[List[List[RGB]]],
    next_frames: List[List[List[RGB]]],
    prev_opacities: List[float],
    next_opacities: List[float]
) -> None
```

---

## Circular View Specification

### 1. Overview

**CircularPreviewCanvas** is a read-only preview widget that displays rectangular grid data in a circular/radial arrangement. It follows the principle: **"Circular View is a lens, not a new world"**.

### 2. Core Philosophy

**Key Principle**: "Circular View is a lens, not a new world"

**Implications**:
- Grid-based editing remains primary
- Circular layout is an interpretation layer only
- Mapping table is the single source of truth
- No polar coordinate drawing
- All drawing tools work unchanged

### 3. Architecture

#### 3.1 Data Flow

```
[ Rectangular Grid Canvas ]
          ↓
[ Circular Mapping Table ]  ← Single Source of Truth
          ↓
[ Circular Preview / Export Order ]
```

#### 3.2 Mapping Table

**Format**: `List[Tuple[int, int]]` where `mapping_table[led_idx] = (grid_x, grid_y)`

**Properties**:
- Generated once when pattern is created
- Stored in `PatternMetadata.circular_mapping_table`
- Used by preview and export (no live calculations)
- Deterministic: same inputs always produce same outputs

**Example**:
```python
# For a 60-LED circle on a 12×12 grid:
mapping_table = [
    (6, 0),   # LED 0 → grid (6, 0)
    (7, 1),   # LED 1 → grid (7, 1)
    (8, 2),   # LED 2 → grid (8, 2)
    # ... 57 more mappings
]
```

### 4. Layout Types

#### 4.1 Standard Circular Layouts

**Types**:
- **Circle**: Full circle (0-360°)
- **Ring**: Annulus (inner + outer radius)
- **Arc**: Partial circle (start_angle to end_angle)
- **Semi-Circle**: 180° arc

**Parameters**:
```python
layout_type: str = "circle" | "ring" | "arc"
circular_led_count: int                    # Number of LEDs
circular_radius: float                     # Outer radius
circular_inner_radius: Optional[float]    # Inner radius (for rings)
circular_start_angle: float = 0.0         # Start angle (degrees)
circular_end_angle: float = 360.0          # End angle (degrees)
```

#### 4.2 Multi-Ring Layout

**Purpose**: Multiple concentric rings (Budurasmala feature)

**Parameters**:
```python
layout_type: str = "multi_ring"
multi_ring_count: int                      # Number of rings (1-5)
ring_led_counts: List[int]                 # LEDs per ring
ring_radii: List[float]                    # Radius per ring
```

**LED Order**: Ring 0 (inner) → Ring 1 → ... → Ring N-1 (outer)

#### 4.3 Radial Ray Layout

**Purpose**: LEDs arranged along straight lines (rays) from center

**Parameters**:
```python
layout_type: str = "radial_rays"
ray_count: int                             # Number of rays
leds_per_ray: int                           # LEDs per ray
ray_spacing_angle: Optional[float]         # Angle between rays (auto if None)
```

**LED Order**: Ray 0 (all LEDs) → Ray 1 (all LEDs) → ... → Ray N-1 (all LEDs)

#### 4.4 Custom Position Layout

**Purpose**: Custom LED positions (for custom PCBs)

**Parameters**:
```python
layout_type: str = "custom_positions"
custom_led_positions: List[Tuple[float, float]]  # (x, y) positions
led_position_units: str = "grid" | "mm" | "inches"
custom_position_center_x: Optional[float]
custom_position_center_y: Optional[float]
```

### 5. CircularMapper

**Location**: `core/mapping/circular_mapper.py`

**Purpose**: Maps between 2D grid coordinates and circular LED layouts

#### 5.1 Core Methods

```python
@staticmethod
def generate_mapping_table(metadata: PatternMetadata) -> List[Tuple[int, int]]
    """
    Generate mapping table: LED index -> (grid_x, grid_y).
    
    This is the SINGLE SOURCE OF TRUTH for circular layout mapping.
    The mapping table is deterministic and stable across sessions.
    """

@staticmethod
def grid_to_led_index(x: int, y: int, metadata: PatternMetadata) -> Optional[int]
    """Convert grid coordinate to LED index."""

@staticmethod
def led_index_to_grid(led_idx: int, metadata: PatternMetadata) -> Optional[Tuple[int, int]]
    """Convert LED index to grid coordinate."""

@staticmethod
def validate_mapping_table(metadata: PatternMetadata) -> Tuple[bool, Optional[str]]
    """Validate that the mapping table is consistent with metadata."""

@staticmethod
def ensure_mapping_table(metadata: PatternMetadata) -> bool
    """Ensure mapping table exists, generating it if necessary."""

@staticmethod
def is_mapped(x: int, y: int, metadata: PatternMetadata) -> bool
    """Check if grid cell (x, y) is mapped to a LED."""
```

#### 5.2 Mapping Generation Algorithm

**For Standard Circular Layouts**:
```python
1. Calculate center of grid: center_x = (width - 1) / 2.0
2. Generate LED positions in polar coordinates:
   - For each LED i (0 to led_count-1):
     - angle = start_angle + (i / led_count) * (end_angle - start_angle)
     - radius = circular_radius (or interpolated for rings)
3. Convert polar to cartesian:
   - x_rel = radius * cos(angle)
   - y_rel = radius * sin(angle)
4. Map to grid:
   - grid_x = round(center_x + x_rel)
   - grid_y = round(center_y + y_rel)
5. Clamp to grid bounds
```

**For Multi-Ring Layouts**:
```python
1. For each ring (inner to outer):
   - Generate circular positions for that ring
   - Map each position to grid
   - Append to mapping table
2. LED order: ring 0 (all LEDs) → ring 1 (all LEDs) → ...
```

**For Radial Ray Layouts**:
```python
1. Calculate ray spacing angle
2. For each ray:
   - Calculate ray angle
   - For each LED on ray (center to edge):
     - Calculate distance from center
     - Convert to cartesian
     - Map to grid
3. LED order: ray 0 (all LEDs) → ray 1 (all LEDs) → ...
```

### 6. CircularPreviewCanvas

**Location**: `ui/widgets/circular_preview_canvas.py`

**Purpose**: Read-only circular preview widget

#### 6.1 Core Methods

```python
def set_grid_data(self, grid: List[List[RGB]])
    """Update grid data and refresh preview."""

def set_pattern_metadata(self, metadata: Optional[PatternMetadata])
    """Set pattern metadata for layout information."""
```

#### 6.2 Rendering Algorithm

**Passive Rendering** (uses mapping table only):

```python
def _paint_from_mapping_table(self, painter: QPainter, rect):
    """
    Paint preview using mapping table only (passive rendering).
    
    This method does NOT know about layout types. It only knows:
    - LED index -> grid coordinate mapping
    - Grid data (colors)
    - Visual arrangement is calculated from LED index order (simple circular)
    """
    mapping_table = self._pattern_metadata.circular_mapping_table
    led_count = len(mapping_table)
    
    center_x = rect.center().x()
    center_y = rect.center().y()
    max_radius = min(rect.width(), rect.height()) / 2 - 10
    
    for led_idx in range(led_count):
        # Get grid coordinate from mapping table (single source of truth)
        grid_x, grid_y = mapping_table[led_idx]
        
        # Get pixel color from grid
        if 0 <= grid_y < len(self._grid_data) and 0 <= grid_x < len(self._grid_data[grid_y]):
            r, g, b = self._grid_data[grid_y][grid_x]
        else:
            r, g, b = (0, 0, 0)
        
        # Calculate visual position from LED index (simple circular arrangement)
        angle = 2 * pi * (led_idx / led_count) if led_count > 0 else 0
        radius = max_radius * 0.8
        
        x = center_x + radius * cos(angle)
        y = center_y + radius * sin(angle)
        
        # Draw LED
        color = QColor(r, g, b)
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(self._pixel_border_color, 1))
        painter.drawEllipse(int(x) - pixel_size // 2, int(y) - pixel_size // 2, 
                           pixel_size, pixel_size)
```

**Key Points**:
- Uses mapping table to get grid coordinates
- Reads colors from grid data
- Arranges LEDs in simple circle for preview
- Does NOT recalculate layout (uses mapping table)

### 7. Real-Time Updates

**Integration with Canvas**:
```python
# In DesignToolsTab
def _on_canvas_pixel_updated(self, x: int, y: int, color: Tuple[int, int, int]):
    # Update circular preview in real-time
    if hasattr(self, 'circular_preview') and hasattr(self.canvas, 'get_grid_data'):
        grid_data = self.canvas.get_grid_data()
        self.circular_preview.set_grid_data(grid_data)
```

**Update Flow**:
1. User paints on canvas
2. Canvas emits `pixel_updated` signal
3. DesignToolsTab receives signal
4. Gets updated grid data from canvas
5. Updates circular preview
6. Preview redraws using mapping table

### 8. Export Integration

**Export for Circular Layouts**:
```python
# In core/export/encoders.py
def encode_frame_bytes(frame: Frame, metadata: PatternMetadata) -> bytes:
    if metadata.layout_type != "rectangular":
        # Use mapping table to reorder pixels
        if not metadata.circular_mapping_table:
            CircularMapper.ensure_mapping_table(metadata)
        
        mapping_table = metadata.circular_mapping_table
        
        # Iterate LED indices 0..N-1 (physical wiring order)
        reordered_pixels = []
        for led_idx in range(len(mapping_table)):
            grid_x, grid_y = mapping_table[led_idx]
            # Read pixel from grid
            pixel_idx = grid_y * metadata.width + grid_x
            if pixel_idx < len(frame.pixels):
                reordered_pixels.append(frame.pixels[pixel_idx])
        
        # Export reordered pixels
        return encode_pixels(reordered_pixels)
    else:
        # Standard rectangular export
        return encode_pixels(frame.pixels)
```

**Key Points**:
- Never exports row-by-row for circular layouts
- Uses mapping table to reorder pixels
- Exports in LED index order (physical wiring order)

### 9. Canvas Overlay Integration

**Visual Feedback on Canvas**:
```python
# In MatrixDesignCanvas._draw_geometry_overlay()
if layout_type != "rectangular":
    # Dim unmapped cells
    for y in range(self._matrix_height):
        for x in range(self._matrix_width):
            if not CircularMapper.is_mapped(x, y, self._pattern_metadata):
                # Dim unmapped cell (gray overlay)
                # ...
    
    # Draw circular bounds
    if layout_type == "circle":
        painter.drawEllipse(bounds)
    elif layout_type == "ring":
        painter.drawEllipse(bounds)
        # Draw inner circle
        # ...
```

**Features**:
- Highlights active grid cells (green overlay)
- Dims inactive grid cells (gray overlay)
- Shows circular bounds outline
- Optional LED index numbers

---

## Integration & Data Flow

### 1. Canvas → Circular Preview Flow

```
User Paints on Canvas
    ↓
pixel_updated(x, y, color) signal
    ↓
_on_canvas_pixel_updated(x, y, color)
    ↓
grid_data = canvas.get_grid_data()
    ↓
circular_preview.set_grid_data(grid_data)
    ↓
Circular Preview Redraw
    ├─→ Reads layout_type from PatternMetadata
    ├─→ Uses circular_mapping_table
    └─→ Renders circular arrangement
```

### 2. Pattern Creation Flow

```
User Creates Circular Pattern
    ↓
New Pattern Dialog
    ├─→ User selects "Circular" layout
    ├─→ User sets LED count, radius, angles
    └─→ User clicks "Create"
    ↓
DesignToolsTab._on_new_pattern_clicked()
    ├─→ Creates PatternMetadata with circular parameters
    ├─→ Calls CircularMapper.generate_mapping_table()
    ├─→ Validates mapping table
    └─→ Creates Pattern with metadata
    ↓
Pattern Created
    ├─→ circular_mapping_table stored in metadata
    ├─→ Canvas.set_pattern_metadata() called
    └─→ Circular preview.set_pattern_metadata() called
```

### 3. Export Flow

```
User Exports Pattern
    ↓
Export Service
    ├─→ Checks layout_type from metadata
    ├─→ If circular:
    │   ├─→ Uses circular_mapping_table
    │   ├─→ Iterates LED indices 0..N-1
    │   ├─→ Looks up grid (x,y) from mapping table
    │   └─→ Reads pixel color from grid
    └─→ If rectangular:
        └─→ Uses standard row-major order
    ↓
Pixels Exported in Correct Order
```

---

## API Reference

### MatrixDesignCanvas API

#### Signals
```python
pixel_updated = Signal(int, int, tuple)      # x, y, (r, g, b)
hover_changed = Signal(int, int)              # x, y under cursor
painting_finished = Signal()                 # Mouse released
color_picked = Signal(int, int, int)         # r, g, b from eyedropper
```

#### Methods
```python
# Pixel Management
set_matrix_size(width: int, height: int, default_color: RGB = (0, 0, 0))
get_grid_data() -> List[List[RGB]]
set_frame_pixels(pixels: List[RGB])
to_pixels() -> List[RGB]

# Drawing Configuration
set_drawing_mode(mode: DrawingMode)
set_current_color(color: RGB)
set_erase_color(color: RGB)
set_brush_size(size: int)
get_brush_size() -> int
set_shape_filled(filled: bool)

# Visual Settings
set_pixel_shape(shape: PixelShape | str)
set_geometry_overlay(mode: GeometryOverlay | str)
set_border_width(width: int)
set_pattern_metadata(metadata: Optional[PatternMetadata])

# Zoom/Pan
set_zoom_factor(factor: float) -> None
reset_zoom() -> None

# Onion Skinning
set_onion_skin_frames(
    prev_frames: List[List[List[RGB]]],
    next_frames: List[List[List[RGB]]],
    prev_opacities: List[float],
    next_opacities: List[float]
) -> None
```

### CircularPreviewCanvas API

#### Methods
```python
set_grid_data(grid: List[List[RGB]])
set_pattern_metadata(metadata: Optional[PatternMetadata])
```

### CircularMapper API

#### Static Methods
```python
@staticmethod
def generate_mapping_table(metadata: PatternMetadata) -> List[Tuple[int, int]]

@staticmethod
def grid_to_led_index(x: int, y: int, metadata: PatternMetadata) -> Optional[int]

@staticmethod
def led_index_to_grid(led_idx: int, metadata: PatternMetadata) -> Optional[Tuple[int, int]]

@staticmethod
def validate_mapping_table(metadata: PatternMetadata) -> Tuple[bool, Optional[str]]

@staticmethod
def ensure_mapping_table(metadata: PatternMetadata) -> bool

@staticmethod
def is_mapped(x: int, y: int, metadata: PatternMetadata) -> bool

@staticmethod
def get_led_count_for_layout(metadata: PatternMetadata) -> int

@staticmethod
def suggest_grid_size(led_count: int, layout_type: str) -> Tuple[int, int]
```

---

## Technical Details

### Coordinate Systems

#### Canvas Matrix View
- **Grid Coordinates**: (x, y) where x ∈ [0, width-1], y ∈ [0, height-1]
- **Screen Coordinates**: Pixel positions in widget
- **Conversion**: `screen_x = grid_x * pixel_size + pan_offset.x()`

#### Circular View
- **Grid Coordinates**: Same as canvas (x, y)
- **LED Index**: Physical LED order (0 to N-1)
- **Polar Coordinates**: (angle, radius) for layout calculation
- **Mapping**: `mapping_table[led_idx] = (grid_x, grid_y)`

### Data Formats

#### RGB Color
```python
RGB = Tuple[int, int, int]  # (R, G, B) where each value is 0-255
```

#### Grid Data
```python
grid: List[List[RGB]]  # 2D array: grid[y][x] = (r, g, b)
```

#### Linear Pixels
```python
pixels: List[RGB]  # Row-major: pixels[y * width + x] = grid[y][x]
```

#### Mapping Table
```python
mapping_table: List[Tuple[int, int]]  # mapping_table[led_idx] = (grid_x, grid_y)
```

### Performance Characteristics

#### Canvas Matrix View
- **Rendering**: O(width × height) per frame
- **Dirty Regions**: Optimized partial redraws
- **Memory**: O(width × height × 3 bytes) for grid
- **Zoom/Pan**: O(1) coordinate conversion

#### Circular View
- **Mapping Generation**: O(led_count) - one-time cost
- **Preview Rendering**: O(led_count) per frame
- **Export**: O(led_count) pixel reordering
- **Memory**: O(led_count × 2 × 4 bytes) for mapping table

### Error Handling

#### Missing Mapping Table
- **Detection**: `CircularMapper.validate_mapping_table()`
- **Recovery**: `CircularMapper.ensure_mapping_table()` auto-regenerates
- **Fallback**: Rectangular layout if generation fails

#### Invalid Parameters
- **Validation**: `PatternMetadata.__post_init__()`
- **Errors**: Clear ValueError messages
- **Recovery**: User-friendly error dialogs

---

## Summary

### Canvas Matrix View
- **15+ Core Features**: Pixel grid, 8 drawing tools, zoom/pan, onion skinning, overlays
- **50+ Total Features**: Including integrations, rendering options, and visual feedback
- **Real-Time**: Immediate visual feedback on all operations
- **Multi-Layer**: Full integration with layer system
- **Animation**: Frame support with onion skinning

### Circular View
- **6 Layout Types**: Circle, Ring, Arc, Multi-Ring, Radial Rays, Custom Positions
- **Mapping-Based**: Single source of truth (mapping table)
- **Real-Time Preview**: Updates as user draws
- **Export Integration**: Automatic pixel reordering
- **Visual Feedback**: Canvas overlay shows active cells

### Key Integrations
1. **LayerManager** → Multi-layer support
2. **FrameManager** → Multi-frame animation
3. **HistoryManager** → Undo/redo
4. **CircularMapper** → Circular layouts
5. **WiringMapper** → Wiring visualization
6. **PatternMetadata** → Layout configuration

---

**Document Status**: ✅ Complete Specification  
**Last Updated**: 2025-01-27  
**Coverage**: 100% of both systems documented

