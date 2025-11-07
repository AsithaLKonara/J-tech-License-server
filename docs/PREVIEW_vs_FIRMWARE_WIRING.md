# Preview vs Firmware Wiring Diagrams (4×4 example)

This document shows how pixel order flows from the Preview layer (design order) to the Firmware layer (hardware traversal) for all wiring modes and data‑in corners. Use it to verify rows/columns and flipping behavior.

- Matrix size used in diagrams: 4×4 (indices 0..15)
- Preview (Design order): left‑to‑right, top‑to‑bottom numbering
- Firmware (Hardware order): traversal index of the physical strip for the selected wiring + corner

Legend:
- “Preview” grid shows design cell indices (what the simulator displays)
- “Firmware” grid shows the hardware traversal index placed into each cell
- Data‑In corner is the physical entry point of LED index 0

---

## Preview (Design order) — reference

```text
Row0:  0   1   2   3
Row1:  4   5   6   7
Row2:  8   9  10  11
Row3: 12  13  14  15
```

---

## Row-major (no zigzag)

### Data‑In: LT (Left Top)
Preview:
```text
0  1  2  3
4  5  6  7
8  9 10 11
12 13 14 15
```
Firmware:
```text
0  1  2  3
4  5  6  7
8  9 10 11
12 13 14 15
```

### Data‑In: LB (Left Bottom)
Preview: same as above
Firmware:
```text
12 13 14 15
 8  9 10 11
 4  5  6  7
 0  1  2  3
```

### Data‑In: RT (Right Top)
Preview: same as above
Firmware:
```text
 3  2  1  0
 7  6  5  4
11 10  9  8
15 14 13 12
```

### Data‑In: RB (Right Bottom)
Preview: same as above
Firmware:
```text
15 14 13 12
11 10  9  8
 7  6  5  4
 3  2  1  0
```

---

## Serpentine (row‑zigzag)

### Data‑In: LT (Left Top)
Preview: same as reference
Firmware:
```text
 0  1  2  3
 7  6  5  4
 8  9 10 11
15 14 13 12
```

### Data‑In: LB (Left Bottom)
Preview: same as reference
Firmware:
```text
15 14 13 12
 8  9 10 11
 7  6  5  4
 0  1  2  3
```

### Data‑In: RT (Right Top)
Preview: same as reference
Firmware:
```text
 3  2  1  0
 4  5  6  7
11 10  9  8
12 13 14 15
```

### Data‑In: RB (Right Bottom)
Preview: same as reference
Firmware:
```text
12 13 14 15
11 10  9  8
 4  5  6  7
 3  2  1  0
```

---

## Column-major (no zigzag)

### Data‑In: LT (Left Top)
Preview: same as reference
Firmware:
```text
 0  4  8 12
 1  5  9 13
 2  6 10 14
 3  7 11 15
```

### Data‑In: LB (Left Bottom)
Preview: same as reference
Firmware:
```text
 3  7 11 15
 2  6 10 14
 1  5  9 13
 0  4  8 12
```

### Data‑In: RT (Right Top)
Preview: same as reference
Firmware:
```text
12  8  4  0
13  9  5  1
14 10  6  2
15 11  7  3
```

### Data‑In: RB (Right Bottom)
Preview: same as reference
Firmware:
```text
15 11  7  3
14 10  6  2
13  9  5  1
12  8  4  0
```

---

## Column-serpentine (column‑zigzag)

### Data‑In: LT (Left Top)
Preview: same as reference
Firmware:
```text
 0  7  8 15
 1  6  9 14
 2  5 10 13
 3  4 11 12
```

### Data‑In: LB (Left Bottom)
Preview: same as reference
Firmware:
```text
 3  4 11 12
 2  5 10 13
 1  6  9 14
 0  7  8 15
```

### Data‑In: RT (Right Top)
Preview: same as reference
Firmware:
```text
15  8  7  0
14  9  6  1
13 10  5  2
12 11  4  3
```

### Data‑In: RB (Right Bottom)
Preview: same as reference
Firmware:
```text
12 11  4  3
13 10  5  2
14  9  6  1
15  8  7  0
```

---

## How to use this

- Pick your UI selection (wiring + corner) and find the matching Firmware grid above
- The numbers in the Firmware grid are the hardware indices assigned to each (x,y)
- `pattern_data.h` is written in ascending hardware index order; FastLED consumes `leds[0..N-1]` in that order
- If your hardware shows flipped rows/columns, compare the observed order with the Firmware grid to identify which axes need flipping or which wiring/corner is actually present

## Notes

- The Preview grid is always the same (design order), independent of wiring
- The Firmware grid changes solely based on Wiring Mode and Data‑In Corner
- These grids exactly match the logic in `core/wiring_mapper.py`
