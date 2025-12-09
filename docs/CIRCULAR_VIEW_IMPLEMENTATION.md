# Circular View Implementation Documentation

## Overview

This document describes the LED Matrix Studio-style circular view implementation. The circular view follows the principle: **"Circular View is a lens, not a new world"**.

## Core Concept

The circular view is **NOT** a polar coordinate drawing system. Instead, it is:

1. **Grid-based editing** - Users paint on a rectangular grid (rows × columns) as normal
2. **Mapping layer** - A mapping table interprets the grid as a circular layout
3. **Visual interpretation** - Preview and export use the mapping to display/reorder pixels

### Mental Model

```
[ Rectangular Grid Canvas ]
          ↓
[ Circular Mapping Table ]  ← Single Source of Truth
          ↓
[ Circular Preview / Export Order ]
```

## Architecture

### Pattern Metadata

Circular layout information is stored in `PatternMetadata`:

- `layout_type`: "rectangular", "circle", "ring", "arc", "radial"
- `circular_led_count`: Number of LEDs in circular layout
- `circular_radius`: Outer radius
- `circular_inner_radius`: Inner radius (for rings)
- `circular_start_angle` / `circular_end_angle`: Arc angles
- `circular_mapping_table`: Precomputed LED_INDEX → (grid_x, grid_y) mapping

### CircularMapper

The `CircularMapper` class provides:

- `generate_mapping_table()`: Creates deterministic mapping table
- `grid_to_led_index()`: Converts grid (x,y) to LED index
- `led_index_to_grid()`: Converts LED index to grid (x,y)
- `validate_mapping_table()`: Validates mapping table consistency
- `ensure_mapping_table()`: Safe helper to regenerate if missing

### Mapping Table

The mapping table is the **single source of truth**:

- Format: `List[Tuple[int, int]]` where `mapping_table[led_idx] = (grid_x, grid_y)`
- Generated once when pattern is created
- Stored in pattern metadata
- Used by preview and export (no live calculations)
- Deterministic: same inputs always produce same outputs

## Drawing Behavior

**All drawing tools work identically on circular and rectangular patterns:**

- Pixel tool, Rectangle, Circle, Line, Fill, Gradient, Random, Eyedropper
- All effects (blur, color adjustments, etc.)
- All automation (scroll, rotate, mirror, flip, etc.)
- Layers, undo/redo, history

**No special-case logic exists for circular layouts in drawing tools.**

## Visual Feedback

The canvas overlay provides visual feedback:

1. **Circular bounds** - Shows circle/ring/arc outline
2. **Active cells** - Highlights grid cells that map to LEDs (green overlay)
3. **Inactive cells** - Dims grid cells that don't map to LEDs
4. **LED indices** - Optional display of LED index numbers on active cells

This teaches users which grid cells are "active" without changing how they draw.

## Preview Rendering

The live preview:

1. Checks `pattern.metadata.layout_type`
2. If circular, uses `_paint_circular_layout()`
3. Iterates LED indices 0..N-1
4. For each LED index:
   - Looks up grid (x,y) from mapping table
   - Reads pixel color from grid at that position
   - Renders LED at calculated circular position

**Key**: Pixel colors come from mapping table lookup, not live calculations.

## Export System

Export for circular layouts:

1. Detects circular layout from metadata
2. Iterates LED indices 0..N-1 (physical wiring order)
3. For each LED index:
   - Looks up grid (x,y) from mapping table
   - Reads pixel color from grid
4. Outputs pixels in LED index order

**Never exports row-by-row for circular layouts.**

## Backward Compatibility

- Old rectangular patterns load unchanged
- Missing circular metadata defaults to "rectangular"
- Missing mapping table is regenerated automatically
- Export of rectangular patterns unchanged

## Edge Cases

### Missing Mapping Table

- Automatically regenerated using `ensure_mapping_table()`
- Falls back to rectangular if generation fails
- Logs warnings for debugging

### Invalid Parameters

- Validation in `PatternMetadata.__post_init__()`
- Validation in `CircularMapper.generate_mapping_table()`
- Clear error messages guide users

### Loading Old Patterns

- `from_dict()` defaults circular fields appropriately
- Mapping table regenerated if missing
- No data loss for rectangular patterns

## Performance

- Mapping table generated once (not per frame)
- Preview uses cached mapping table
- Export uses cached mapping table
- No performance impact on drawing tools

## Files Modified

- `core/pattern.py` - PatternMetadata extended
- `core/mapping/circular_mapper.py` - Mapping logic
- `ui/dialogs/new_pattern_dialog.py` - Layout selection
- `ui/widgets/matrix_design_canvas.py` - Canvas overlay
- `ui/widgets/enhanced_led_simulator.py` - Preview rendering
- `core/export/encoders.py` - Export reordering
- `core/schemas/pattern_converter.py` - Serialization

## Usage Example

```python
# Create circular pattern
metadata = PatternMetadata(
    width=12, height=12,  # Virtual grid
    layout_type="circle",
    circular_led_count=60,
    circular_radius=5.0
)

# Generate mapping table
mapping_table = CircularMapper.generate_mapping_table(metadata)
metadata.circular_mapping_table = mapping_table

# User paints on grid normally
# Preview shows circular layout
# Export reorders pixels using mapping table
```

## Design Philosophy

> "Circular View is a lens, not a new world."

- Grid-based editing remains primary
- Circular layout is interpretation layer only
- Mapping table is single source of truth
- No polar drawing or special circular tools
- All existing features work unchanged

