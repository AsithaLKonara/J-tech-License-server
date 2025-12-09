# Split-View Canvas Implementation Plan

## Overview
Implement a split-view canvas similar to LED Matrix Studio:
- **Left Column**: Editable rectangular grid (existing MatrixDesignCanvas)
- **Right Column**: Read-only circular preview (shows same data in circular form)
- Both views update in real-time as user draws

## Requirements

1. **Split Canvas Layout**
   - Horizontal splitter dividing canvas area into two columns
   - Left: Existing editable grid
   - Right: Circular preview (read-only)

2. **Circular Preview Widget**
   - New widget that displays grid data in circular/radial form
   - Read-only (no editing)
   - Updates in real-time when grid changes
   - Shows same pixels as rectangular grid, just arranged circularly

3. **Real-Time Synchronization**
   - When user draws on left (rectangular), right (circular) updates immediately
   - Uses same pixel data from grid
   - Mapping: rows = circles, columns = LEDs per circle (for radial layout)

## Implementation Steps

### 1. Create Circular Preview Widget
**File**: `ui/widgets/circular_preview_canvas.py` (new file)

**Features**:
- Read-only canvas widget
- Displays grid pixels in circular/radial arrangement
- Takes grid data as input
- Renders based on layout_type (radial, circle, ring, arc)
- Updates when grid data changes

**Methods**:
- `set_grid_data(pixels: List[List[RGB]])` - Update grid data
- `set_pattern_metadata(metadata: PatternMetadata)` - Set layout info
- `paintEvent()` - Render circular preview

### 2. Modify Canvas Panel
**File**: `ui/tabs/design_tools_tab.py`

**Changes**:
- Modify `_create_canvas_group()` to use horizontal splitter
- Left side: Existing `MatrixDesignCanvas`
- Right side: New `CircularPreviewCanvas`
- Connect canvas signals to update preview

**Layout**:
```
[Canvas Panel]
  └─ [Horizontal Splitter]
      ├─ [Left: MatrixDesignCanvas] (editable)
      └─ [Right: CircularPreviewCanvas] (read-only)
```

### 3. Connect Signals
- `canvas.pixel_updated` → Update preview
- `canvas.painting_finished` → Refresh preview
- When pattern metadata changes → Update preview layout

### 4. Conditional Display
- Show split view when `layout_type != "rectangular"`
- Hide right column when rectangular (or show both, user preference)

## Files to Create/Modify

1. **New File**: `ui/widgets/circular_preview_canvas.py`
   - Circular preview widget

2. **Modify**: `ui/tabs/design_tools_tab.py`
   - Update `_create_canvas_group()` to add splitter
   - Add circular preview widget
   - Connect signals

## Key Implementation Details

### Circular Preview Rendering
- For radial layout: rows = circles, columns = LEDs per circle
- Calculate positions: radius per row, angle per column
- Read pixels from grid: `grid[row][col]`
- Render as circles/ellipses at calculated positions

### Synchronization
- Preview reads from same grid data as canvas
- No separate data storage
- Updates triggered by canvas signals

### Performance
- Efficient rendering (only redraw on changes)
- Use QPainter for drawing
- Cache calculated positions if needed

## Testing Checklist

- [ ] Split view appears when circular layout selected
- [ ] Left grid is editable
- [ ] Right preview is read-only
- [ ] Drawing on left updates right in real-time
- [ ] Preview shows correct circular arrangement
- [ ] Works for all layout types (radial, circle, ring, arc)
- [ ] Splitter is resizable
- [ ] Preview scales correctly


