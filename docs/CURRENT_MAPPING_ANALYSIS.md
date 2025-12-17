# Current Mapping Implementation Analysis

## Matrix Grid Structure (4 rows × 6 columns)

```
        Column 0  Column 1  Column 2  Column 3  Column 4  Column 5
Row 0:     1         2         3         4         5         6
Row 1:     7         8         9        10        11        12
Row 2:    13        14        15        16        17        18
Row 3:    19        20        21        22        23        24
```

**Grid Storage**: `grid[y][x]` where:
- `grid[0][x]` = Top row (Row 0)
- `grid[3][x]` = Bottom row (Row 3)

## Current Mapping Table Generation

**Code Location**: `core/mapping/circular_mapper.py` lines 467-472

```python
for col in range(ray_count):  # For each ray (column)
    for row in range(leds_per_ray):  # For each LED along the ray
        # row=0 -> outer circle (top row)
        # row=height-1 -> inner circle (bottom row)
        mapping.append((col, row))
```

**Mapping Order**:
- LED 0 → (col=0, row=0) → grid[0][0] = value 1
- LED 1 → (col=0, row=1) → grid[1][0] = value 7
- LED 2 → (col=0, row=2) → grid[2][0] = value 13
- LED 3 → (col=0, row=3) → grid[3][0] = value 19
- LED 4 → (col=1, row=0) → grid[0][1] = value 2
- LED 5 → (col=1, row=1) → grid[1][1] = value 8
- ... and so on

## Current Position Generation

**Code Location**: `core/mapping/circular_mapper.py` lines 982-990

```python
for row in range(leds_per_ray):
    # Row 0 = outer circle, row height-1 = inner circle
    # Calculate radius: row 0 has largest radius, row height-1 has smallest
    radius = outer_radius - radius_delta * row
```

**Radius Calculation**:
- Row 0: `radius = outer_radius - 0 * delta = outer_radius` (largest = outer circle)
- Row 1: `radius = outer_radius - 1 * delta` (middle)
- Row 2: `radius = outer_radius - 2 * delta` (middle)
- Row 3: `radius = outer_radius - 3 * delta = inner_radius` (smallest = inner circle)

## Current Rendering Flow

**Code Location**: `ui/widgets/circular_preview_canvas.py` lines 163-187

```
For LED 0:
  mapping_table[0] = (col=0, row=0)
  → Get color from grid[0][0] = value 1
  → Get position: row 0 → outer_radius (outer circle)
  → Render at outer circle position

For LED 3:
  mapping_table[3] = (col=0, row=3)
  → Get color from grid[3][0] = value 19
  → Get position: row 3 → inner_radius (inner circle)
  → Render at inner circle position
```

## Visual Diagram of Current Implementation

### Expected Behavior (What Should Happen)
```
                    Ray 0 (Bottom)
                        │
    Outer Circle        1 (Row 0, value 1)
    (Row 0)            │
                       │
    Ring 1            7 (Row 1, value 7)
    (Row 1)            │
                       │
    Ring 2           13 (Row 2, value 13)
    (Row 2)            │
                       │
    Inner Circle      19 (Row 3, value 19)
    (Row 3)            │
                       ● (center)
```

### Current Implementation Logic
- **Mapping**: LED 0 maps to (col=0, row=0) → grid[0][0] = 1
- **Position**: LED 0 gets outer_radius (largest radius)
- **Result**: Row 0 (top) → Outer circle ✓

- **Mapping**: LED 3 maps to (col=0, row=3) → grid[3][0] = 19
- **Position**: LED 3 gets inner_radius (smallest radius)
- **Result**: Row 3 (bottom) → Inner circle ✓

## Issue Analysis

The code logic appears correct:
1. Mapping table maps row 0 → outer, row 3 → inner ✓
2. Position generation assigns row 0 → outer_radius, row 3 → inner_radius ✓
3. Grid access uses `grid[y][x]` where y=0 is top row ✓

**However**, if the UI is showing the opposite (row 0 as inner, row 3 as outer), there might be:
1. A mismatch in how positions are generated vs. how they're rendered
2. The radius calculation might be inverted somewhere
3. The mapping table might be generated in reverse order

## Next Steps

Need to verify:
1. Is the radius calculation actually producing outer_radius for row 0?
2. Is the position array being used in the correct order?
3. Is there any inversion happening in the rendering code?
