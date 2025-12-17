# Fixed Mapping Visual Diagram

## Matrix Grid (4 rows × 6 columns)

```
        Column 0  Column 1  Column 2  Column 3  Column 4  Column 5
Row 0:     1         2         3         4         5         6    ← Top row → OUTER circle
Row 1:     7         8         9        10        11        12
Row 2:    13        14        15        16        17        18
Row 3:    19        20        21        22        23        24    ← Bottom row → INNER circle
```

## Fixed Position Generation

**Code**: `core/mapping/circular_mapper.py` lines 982-990

**Before (WRONG)**:
```python
radius = outer_radius - radius_delta * row
```
- Row 0: `radius = outer_radius - 0 = outer_radius` → Outer ✓ (but UI showed inner)
- Row 3: `radius = outer_radius - 3*delta = inner_radius` → Inner ✓ (but UI showed outer)

**After (FIXED)**:
```python
inverted_row = leds_per_ray - 1 - row  # Row 0 → 3, Row 3 → 0
radius = inner_radius + radius_delta * inverted_row
```

**Radius Calculation**:
- Row 0: `inverted_row = 3` → `radius = inner_radius + 3*delta = outer_radius` → **OUTER circle** ✓
- Row 1: `inverted_row = 2` → `radius = inner_radius + 2*delta` → Middle
- Row 2: `inverted_row = 1` → `radius = inner_radius + 1*delta` → Middle
- Row 3: `inverted_row = 0` → `radius = inner_radius + 0 = inner_radius` → **INNER circle** ✓

## Visual Representation After Fix

### Circular View (Ray 0 at Bottom)

```
                    Ray 0 (Bottom, 6 o'clock)
                        │
    Outer Circle        1 (Row 0, value 1) ← Top row → Outer ✓
    (Row 0)            │
                       │
    Ring 1            7 (Row 1, value 7)
    (Row 1)            │
                       │
    Ring 2           13 (Row 2, value 13)
    (Row 2)            │
                       │
    Inner Circle      19 (Row 3, value 19) ← Bottom row → Inner ✓
    (Row 3)            │
                       ● (center)
```

## Complete Flow After Fix

**For LED 0** (Row 0, Column 0):
1. `mapping_table[0] = (col=0, row=0)` → grid[0][0] = value 1
2. Position: `row=0` → `inverted_row=3` → `radius = outer_radius` → **OUTER circle** ✓
3. **Result**: Row 0 (top) → Outer circle ✓ **CORRECT**

**For LED 3** (Row 3, Column 0):
1. `mapping_table[3] = (col=0, row=3)` → grid[3][0] = value 19
2. Position: `row=3` → `inverted_row=0` → `radius = inner_radius` → **INNER circle** ✓
3. **Result**: Row 3 (bottom) → Inner circle ✓ **CORRECT**

## Summary

- **Mapping Table**: Unchanged - still maps row 0 → LED 0, row 3 → LED 3
- **Position Generation**: **FIXED** - now inverts row index so row 0 gets outer_radius and row 3 gets inner_radius
- **Result**: Row 0 (top) → Outer circle, Row 3 (bottom) → Inner circle ✓
