# Circular Preview Visualization Guide

## Matrix Grid (4 rows × 6 columns)

```
        Column 0  Column 1  Column 2  Column 3  Column 4  Column 5
Row 0:     1         2         3         4         5         6
Row 1:     7         8         9        10        11        12
Row 2:    13        14        15        16        17        18
Row 3:    19        20        21        22        23        24
```

## Mapping Interpretation

For **circle/ring** layouts:
- **Columns** = **Rays** (6 rays extending from center)
- **Rows** = **LEDs per ray** (4 LEDs along each ray)
- **Row 0** (top) = **Outer circle** (farthest from center)
- **Row 3** (bottom) = **Inner circle** (closest to center)

## LED Index Mapping

The mapping table creates this order:
- **LED 0-3**: Ray 0 (Column 0) - from outer to inner
- **LED 4-7**: Ray 1 (Column 1) - from outer to inner
- **LED 8-11**: Ray 2 (Column 2) - from outer to inner
- **LED 12-15**: Ray 3 (Column 3) - from outer to inner
- **LED 16-19**: Ray 4 (Column 4) - from outer to inner
- **LED 20-23**: Ray 5 (Column 5) - from outer to inner

## Circular Preview Visualization

```
                    Ray 0 (Column 0)
                        │
                        │
         Ray 5 ────────┼─────── Ray 1
         (Col 5)       │       (Col 1)
                        │
                        │
         Ray 4 ────────┼─────── Ray 2
         (Col 4)       │       (Col 2)
                        │
                        │
                    Ray 3 (Column 3)
                        │
                        │
```

### Detailed Ray-by-Ray View

Each ray contains 4 LEDs arranged from outer (top row) to inner (bottom row):

**Ray 0 (Column 0):**
```
    Outer Circle (Row 0)
        1
        │
        │
        7 (Row 1)
        │
        │
        13 (Row 2)
        │
        │
    Inner Circle (Row 3)
        19
```

**Ray 1 (Column 1):**
```
    Outer Circle (Row 0)
        2
        │
        │
        8 (Row 1)
        │
        │
        14 (Row 2)
        │
        │
    Inner Circle (Row 3)
        20
```

**Ray 2 (Column 2):**
```
    Outer Circle (Row 0)
        3
        │
        │
        9 (Row 1)
        │
        │
        15 (Row 2)
        │
        │
    Inner Circle (Row 3)
        21
```

**Ray 3 (Column 3):**
```
    Outer Circle (Row 0)
        4
        │
        │
        10 (Row 1)
        │
        │
        16 (Row 2)
        │
        │
    Inner Circle (Row 3)
        22
```

**Ray 4 (Column 4):**
```
    Outer Circle (Row 0)
        5
        │
        │
        11 (Row 1)
        │
        │
        17 (Row 2)
        │
        │
    Inner Circle (Row 3)
        23
```

**Ray 5 (Column 5):**
```
    Outer Circle (Row 0)
        6
        │
        │
        12 (Row 1)
        │
        │
        18 (Row 2)
        │
        │
    Inner Circle (Row 3)
        24
```

## Complete Circular View (Top-Down)

### View from Above (Circular Arrangement)

```
                    Ray 0 (Col 0)
                        │
                        │ 1 (outer)
                        │
                        │ 7
                        │
                        │ 13
                        │
                        │ 19 (inner)
                        │
                        ● (center)
                        │
                        │ 20 (inner)
                        │
                        │ 14
                        │
                        │ 8
                        │
                        │ 2 (outer)
                        │
                    Ray 1 (Col 1)
```

### Full 360° View (Unfolded)

```
                    Ray 5      Ray 0      Ray 1      Ray 2      Ray 3      Ray 4
                    (Col 5)    (Col 0)    (Col 1)    (Col 2)    (Col 3)    (Col 4)
                      
    Outer Circle       6         1         2         3         4         5
    (Row 0)            │         │         │         │         │         │
                       │         │         │         │         │         │
    Ring 1            12        7         8         9        10        11
    (Row 1)            │         │         │         │         │         │
                       │         │         │         │         │         │
    Ring 2            18        13        14        15        16        17
    (Row 2)            │         │         │         │         │         │
                       │         │         │         │         │         │
    Inner Circle      24        19        20        21        22        23
    (Row 3)            │         │         │         │         │         │
                       │         │         │         │         │         │
                       ●─────────●─────────●─────────●─────────●─────────●
                                (Center Point)
```

### Concentric Rings View

```
                    ┌─────────────────────────────────────┐
                    │  Outer Circle (Row 0)               │
                    │  6 ──── 1 ──── 2 ──── 3 ──── 4 ──── 5 │
                    │  │     │     │     │     │     │     │
                    │  │     │     │     │     │     │     │
                    │  └─────┴─────┴─────┴─────┴─────┴─────┘
                    │                                      │
                    │  ┌───────────────────────────────┐  │
                    │  │  Ring 1 (Row 1)               │  │
                    │  │  12 ─── 7 ─── 8 ─── 9 ─── 10 ─── 11 │
                    │  │  │     │     │     │     │     │  │
                    │  │  │     │     │     │     │     │  │
                    │  │  └─────┴─────┴─────┴─────┴─────┘  │
                    │  │                                    │
                    │  │  ┌─────────────────────────────┐  │
                    │  │  │  Ring 2 (Row 2)             │  │
                    │  │  │  18 ─── 13 ─── 14 ─── 15 ─── 16 ─── 17 │
                    │  │  │  │     │     │     │     │     │  │
                    │  │  │  │     │     │     │     │     │  │
                    │  │  │  └─────┴─────┴─────┴─────┴─────┘  │
                    │  │  │                                    │
                    │  │  │  ┌───────────────────────────┐  │
                    │  │  │  │  Inner Circle (Row 3)     │  │
                    │  │  │  │  24 ─── 19 ─── 20 ─── 21 ─── 22 ─── 23 │
                    │  │  │  │                          │  │
                    │  │  │  └───────────────────────────┘  │
                    │  │  │                                    │
                    │  │  └────────────────────────────────────┘
                    │  │                                      │
                    │  └──────────────────────────────────────┘
                    │                                        │
                    └────────────────────────────────────────┘
```

## LED Index to Grid Coordinate Mapping

| LED Index | Grid (col, row) | Matrix Value | Position in Circle |
|-----------|-----------------|--------------|-------------------|
| 0         | (0, 0)          | 1            | Ray 0, Outer      |
| 1         | (0, 1)          | 7            | Ray 0, Ring 1     |
| 2         | (0, 2)          | 13           | Ray 0, Ring 2     |
| 3         | (0, 3)          | 19           | Ray 0, Inner      |
| 4         | (1, 0)          | 2            | Ray 1, Outer      |
| 5         | (1, 1)          | 8            | Ray 1, Ring 1     |
| 6         | (1, 2)          | 14           | Ray 1, Ring 2     |
| 7         | (1, 3)          | 20           | Ray 1, Inner      |
| 8         | (2, 0)          | 3            | Ray 2, Outer      |
| 9         | (2, 1)          | 9            | Ray 2, Ring 1     |
| 10        | (2, 2)          | 15           | Ray 2, Ring 2     |
| 11        | (2, 3)          | 21           | Ray 2, Inner      |
| 12        | (3, 0)          | 4            | Ray 3, Outer      |
| 13        | (3, 1)          | 10           | Ray 3, Ring 1     |
| 14        | (3, 2)          | 16           | Ray 3, Ring 2     |
| 15        | (3, 3)          | 22           | Ray 3, Inner      |
| 16        | (4, 0)          | 5            | Ray 4, Outer      |
| 17        | (4, 1)          | 11           | Ray 4, Ring 1     |
| 18        | (4, 2)          | 17           | Ray 4, Ring 2     |
| 19        | (4, 3)          | 23           | Ray 4, Inner      |
| 20        | (5, 0)          | 6            | Ray 5, Outer      |
| 21        | (5, 1)          | 12           | Ray 5, Ring 1     |
| 22        | (5, 2)          | 18           | Ray 5, Ring 2     |
| 23        | (5, 3)          | 24           | Ray 5, Inner      |

## Key Points

1. **Columns become rays**: Each column in the matrix becomes a ray extending from the center outward
2. **Rows become rings**: Each row becomes a concentric ring (outer to inner)
3. **Top row = Outer circle**: Row 0 pixels appear on the outermost ring
4. **Bottom row = Inner circle**: Row 3 pixels appear on the innermost ring
5. **LED order**: LEDs are numbered sequentially by ray (all LEDs in ray 0, then all in ray 1, etc.)
6. **Within each ray**: LEDs go from outer (row 0) to inner (row 3)
