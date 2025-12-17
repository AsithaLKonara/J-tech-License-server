# Current Implementation Visual Diagram

## Matrix Grid (4 rows × 6 columns)

```
        Column 0  Column 1  Column 2  Column 3  Column 4  Column 5
Row 0:     1         2         3         4         5         6    ← Top row (should be OUTER)
Row 1:     7         8         9        10        11        12
Row 2:    13        14        15        16        17        18
Row 3:    19        20        21        22        23        24    ← Bottom row (should be INNER)
```

## Current Mapping Table Generation

**Code**: `core/mapping/circular_mapper.py` lines 467-472

```python
for col in range(ray_count):  # For each ray (column)
    for row in range(leds_per_ray):  # For each LED along the ray
        mapping.append((col, row))  # row goes from 0 to 3
```

**Mapping for Ray 0 (Column 0)**:
- LED 0 → (col=0, row=0) → grid[0][0] = **value 1** (Row 0, top)
- LED 1 → (col=0, row=1) → grid[1][0] = **value 7** (Row 1)
- LED 2 → (col=0, row=2) → grid[2][0] = **value 13** (Row 2)
- LED 3 → (col=0, row=3) → grid[3][0] = **value 19** (Row 3, bottom)

## Current Position Generation

**Code**: `core/mapping/circular_mapper.py` lines 982-990

```python
for row in range(leds_per_ray):  # row = 0, 1, 2, 3
    radius = outer_radius - radius_delta * row
```

**Radius Calculation**:
- Row 0: `radius = outer_radius - 0*delta = outer_radius` → **OUTER circle** (largest radius)
- Row 1: `radius = outer_radius - 1*delta` → Middle
- Row 2: `radius = outer_radius - 2*delta` → Middle  
- Row 3: `radius = outer_radius - 3*delta = inner_radius` → **INNER circle** (smallest radius)

## Current Rendering Flow

**For LED 0**:
1. `mapping_table[0] = (col=0, row=0)`
2. Get color: `grid[0][0] = value 1` (Row 0, top row)
3. Get position: `row=0 → outer_radius` (outer circle)
4. **Result**: Row 0 (top) → Outer circle ✓ **CORRECT**

**For LED 3**:
1. `mapping_table[3] = (col=0, row=3)`
2. Get color: `grid[3][0] = value 19` (Row 3, bottom row)
3. Get position: `row=3 → inner_radius` (inner circle)
4. **Result**: Row 3 (bottom) → Inner circle ✓ **CORRECT**

## Visual Representation

### Expected Circular View (Based on Current Code Logic)

```
                    Ray 0 (Bottom, 6 o'clock)
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

## Issue Analysis

**The code logic appears CORRECT**:
- Mapping: Row 0 → LED 0 (first in ray) → Outer position ✓
- Mapping: Row 3 → LED 3 (last in ray) → Inner position ✓
- Position: Row 0 → outer_radius (largest) ✓
- Position: Row 3 → inner_radius (smallest) ✓

**BUT** if the UI shows the opposite, the issue might be:

1. **Position array order mismatch**: The positions array might be generated in a different order than the mapping table expects
2. **Inverted radius calculation**: Maybe `radius_delta` is negative or the calculation is inverted somewhere
3. **Mapping table vs Position array mismatch**: The LED index order in positions might not match the mapping table order

## Next Step: Verify Position Array Order

The positions array is generated ray-by-ray, LED-by-LED:
- Position[0] = Ray 0, Row 0 (outer)
- Position[1] = Ray 0, Row 1
- Position[2] = Ray 0, Row 2
- Position[3] = Ray 0, Row 3 (inner)
- Position[4] = Ray 1, Row 0 (outer)
- ...

The mapping table is also generated ray-by-ray, LED-by-LED:
- Mapping[0] = (col=0, row=0) → grid[0][0]
- Mapping[1] = (col=0, row=1) → grid[1][0]
- Mapping[2] = (col=0, row=2) → grid[2][0]
- Mapping[3] = (col=0, row=3) → grid[3][0]
- Mapping[4] = (col=1, row=0) → grid[0][1]
- ...

**They match!** So the issue must be elsewhere.

## Possible Solution

If the UI is showing Row 0 as inner and Row 3 as outer, we need to **INVERT the radius calculation**:

**Current**:
```python
radius = outer_radius - radius_delta * row
```

**Should be**:
```python
radius = inner_radius + radius_delta * row
```

This would make:
- Row 0: `radius = inner_radius + 0 = inner_radius` → Inner circle ❌ (WRONG)
- Row 3: `radius = inner_radius + 3*delta = outer_radius` → Outer circle ❌ (WRONG)

Wait, that's backwards too!

Actually, if we want Row 0 → Outer and Row 3 → Inner, but the UI shows the opposite, we might need to invert the row index:

**Should be**:
```python
inverted_row = leds_per_ray - 1 - row  # Row 0 → 3, Row 3 → 0
radius = outer_radius - radius_delta * inverted_row
```

This would make:
- Row 0: `inverted_row = 3` → `radius = outer_radius - 3*delta = inner_radius` → Inner ❌
- Row 3: `inverted_row = 0` → `radius = outer_radius - 0 = outer_radius` → Outer ❌

That's still backwards!

Let me think differently: If Row 0 should be outer but currently shows as inner, maybe the formula should be:
```python
radius = inner_radius + radius_delta * (leds_per_ray - 1 - row)
```

This would make:
- Row 0: `radius = inner_radius + 3*delta = outer_radius` → Outer ✓
- Row 3: `radius = inner_radius + 0 = inner_radius` → Inner ✓

**THIS IS THE FIX!**
