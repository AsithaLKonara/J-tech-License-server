# Diagnostic Tools

This directory contains diagnostic and verification tools for the Upload Bridge LED pattern system.

---

## Verification Scripts

### 1. `verify_all_16_wiring_combinations.py`
**Purpose:** Verify that WiringMapper produces correct output for all 16 wiring/corner combinations

**Usage:**
```bash
python verify_all_16_wiring_combinations.py
```

**What it tests:**
- All 4 wiring modes (Row-major, Serpentine, Column-major, Column-serpentine)
- All 4 corners (LT, LB, RT, RB)
- Total: 16 combinations

**Expected result:**
- All 16 combinations should PASS
- Each should produce a UNIQUE checksum
- No duplicates or failures

---

### 2. `verify_hardware_to_design.py`
**Purpose:** Test round-trip conversion (Design → Hardware → Design)

**Usage:**
```bash
python verify_hardware_to_design.py
```

**What it tests:**
- Converts design order to hardware order
- Converts hardware order back to design order
- Verifies result matches original

**Expected result:**
- All 16 combinations should pass perfect round-trip
- Exit code 0 if all pass, 1 if any fail

---

### 3. `verify_speed_brightness_pixel_order.py`
**Purpose:** Verify speed and brightness don't affect pixel ORDER

**Usage:**
```bash
python verify_speed_brightness_pixel_order.py
```

**What it tests:**
- FPS changes (only affects frame timing)
- Brightness scaling (only affects RGB values)
- Speed curves (only affects frame timing)
- Frame interpolation (adds frames, doesn't reorder)

**Expected result:**
- All pixel order checksums should match before/after
- Only timing (duration_ms) and intensity (RGB values) change

---

## Diagnostic Pattern Generator

### 4. `create_diagnostic_pattern.py`
**Purpose:** Generate a test pattern with identifiable corner markers

**Usage:**
```bash
python create_diagnostic_pattern.py
```

**Output:** `diagnostic_12x6.bin` (224 bytes)

**Pattern layout:**
```
RED    CYAN  CYAN  ... CYAN  GREEN      (Row 0 - Top)
MAGENTA  ...  ...  ...  ... WHITE       (Row 1)
MAGENTA  ...  ... ORANGE ... WHITE      (Row 2)
MAGENTA  ...  ...  ...  ... WHITE       (Row 3)
MAGENTA  ...  ...  ...  ... WHITE       (Row 4)
BLUE   ...  ...  ...  ... YELLOW        (Row 5 - Bottom)
```

**How to use:**
1. Load `diagnostic_12x6.bin` in the app
2. Set File Format: Row-major, File Data-In: Left Top
3. Preview should show:
   - Red at top-left (0,0)
   - Green at top-right (11,0)
   - Blue at bottom-left (0,5)
   - Yellow at bottom-right (11,5)
4. Flash with different Target Wiring settings
5. Use corner colors to identify your panel's actual wiring:
   - Where does RED appear? → That's your Data-In corner
   - Are rows/columns flipped? → Adjust wiring mode
   - Use Flip X/Y if orientation is wrong

---

## Troubleshooting with Diagnostic Pattern

### Scenario 1: Red is at bottom-left (not top-left)
**Diagnosis:** Your hardware has Data-In at bottom-left  
**Fix:** Set Target Data-In: Left Bottom

### Scenario 2: Red and Green swapped (Green at top-left)
**Diagnosis:** Your panel is horizontally flipped  
**Fix:** Enable Flip X in Flash tab

### Scenario 3: Red is at bottom-right
**Diagnosis:** Your hardware has Data-In at bottom-right  
**Fix:** Set Target Data-In: Right Bottom

### Scenario 4: Odd rows are backwards
**Diagnosis:** Your hardware is Serpentine (row-based)  
**Fix:** Set Target Wiring: Serpentine

### Scenario 5: Odd columns are backwards
**Diagnosis:** Your hardware is Column-serpentine  
**Fix:** Set Target Wiring: Column-serpentine

---

## Complete Testing Workflow

### Step 1: Verify Core Logic
```bash
python verify_all_16_wiring_combinations.py
python verify_hardware_to_design.py
python verify_speed_brightness_pixel_order.py
```
**All should pass** ✓

### Step 2: Generate Diagnostic Pattern
```bash
python create_diagnostic_pattern.py
```
**Creates:** `diagnostic_12x6.bin`

### Step 3: Test in App
1. Run Upload Bridge: `python main.py`
2. Load `diagnostic_12x6.bin`
3. Try all File Format combinations until preview looks correct
4. Try all Target Wiring combinations
5. Flash each and verify hardware

### Step 4: Test Your Actual Pattern
1. Load your pattern (e.g., "12.6 rows up down.bin")
2. Use correct File Format (from Step 3)
3. Use correct Target Wiring (from Step 3)
4. Flash and verify

---

## Expected Console Output

### When Loading Pattern:
```
======================================================================
PREVIEW LAYER - PATTERN LOAD
======================================================================
Pattern name: diagnostic 12x6
Dimensions: 12×6
LED count: 72
...
📂 File format specified: Serpentine LT
📊 Frame 0 BEFORE unwrap (Serpentine LT format):
     LED 0: RGB(255, 0, 0)
     ...
   Checksum BEFORE: abc123...
📊 Frame 0 AFTER unwrap (design order):
     LED 0: RGB(255, 0, 0)
     ...
   Checksum AFTER: def456...
✓ Preview unwrapped from Serpentine LT → design order
```

### When Flashing:
```
============================================================
WIRING CONVERSION PIPELINE
============================================================
Matrix: 12×6 (72 LEDs)
Frames: 18
Step 1: File (Serpentine LT) → Design order
Step 2: Design order → Target (Column-serpentine LB)
...
🔄 STEP 1: Converting Serpentine LT → Design order
   Frame 0 BEFORE Step 1:
     LED 0: RGB(255, 0, 0)
     ...
   Checksum BEFORE: abc123
   Frame 0 AFTER Step 1 (design order):
     LED 0: RGB(255, 0, 0)
     ...
   Checksum AFTER: def456
✓ Step 1 complete: Pattern now in design order

🔄 STEP 2: Converting Design order → Column-serpentine LB
   Frame 0 BEFORE Step 2 (design order):
     LED 0: RGB(255, 0, 0)
     ...
   Checksum BEFORE Step 2: def456
   Frame 0 AFTER Step 2 (Column-serpentine LB):
     LED 0: RGB(255, 0, 0)
     ...
   Checksum AFTER Step 2: ghi789
✓ Step 2 complete: 18 frames converted to hardware order

============================================================
✅ CONVERSION COMPLETE
============================================================
```

---

## Files Reference

- `verify_all_16_wiring_combinations.py` - Core mapper verification
- `verify_hardware_to_design.py` - Round-trip conversion test
- `verify_speed_brightness_pixel_order.py` - Speed/brightness independence test
- `create_diagnostic_pattern.py` - Generate test pattern
- `diagnostic_12x6.bin` - Test pattern file (generated)

All scripts can be run independently and should pass without errors.

