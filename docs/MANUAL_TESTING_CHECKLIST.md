# Manual Testing Checklist - Schema Update Verification

**Date**: 2025-01-27  
**Purpose**: Verify JSON schema update for circular layouts  
**Estimated Time**: 30-45 minutes

---

## Pre-Testing Setup

- [ ] Application is running without errors
- [ ] No console errors on startup
- [ ] All tabs are accessible
- [ ] Test files directory is ready for saving patterns

---

## Test 1: Basic Circular Pattern Creation & Persistence

**Objective**: Verify circular patterns can be created, saved, and loaded with full data preservation.

### Steps:
1. [ ] Launch application
2. [ ] Click "New Pattern" or File → New
3. [ ] Select "Circular" layout type
4. [ ] Set parameters:
   - LED Count: 60
   - Radius: 15.0
   - Start Angle: 0°
   - End Angle: 360°
5. [ ] Click "Create"
6. [ ] Verify circular preview appears
7. [ ] Draw some pixels on the canvas
8. [ ] Save pattern (File → Save As → `test_circular.ledproj`)
9. [ ] Close the pattern
10. [ ] Open the saved pattern (File → Open → `test_circular.ledproj`)
11. [ ] Verify pattern loads correctly
12. [ ] Verify all drawn pixels are preserved
13. [ ] Verify circular layout parameters are preserved

### Expected Results:
- ✅ Pattern creates successfully
- ✅ Circular preview shows correct layout
- ✅ Pattern saves without errors
- ✅ Pattern loads with all data intact
- ✅ No console errors during save/load

---

## Test 2: Multi-Ring Pattern Creation & Persistence

**Objective**: Verify multi-ring patterns work with schema validation.

### Steps:
1. [ ] Create new pattern
2. [ ] Select "Multi-Ring" layout type
3. [ ] Set parameters:
   - Ring Count: 3
   - Ring 1: 24 LEDs, Radius 8.0
   - Ring 2: 36 LEDs, Radius 12.0
   - Ring 3: 48 LEDs, Radius 16.0
   - Ring Spacing: 4.0
4. [ ] Click "Create"
5. [ ] Verify multi-ring preview appears
6. [ ] Draw pixels on different rings
7. [ ] Save pattern (`test_multi_ring.ledproj`)
8. [ ] Close and reopen pattern
9. [ ] Verify all ring data is preserved
10. [ ] Verify pixel positions match original

### Expected Results:
- ✅ Multi-ring layout creates correctly
- ✅ All ring parameters saved
- ✅ Pattern loads with all rings intact
- ✅ No schema validation errors

---

## Test 3: Radial Rays Pattern Creation & Persistence

**Objective**: Verify radial rays patterns work with schema validation.

### Steps:
1. [ ] Create new pattern
2. [ ] Select "Radial Rays" layout type
3. [ ] Set parameters:
   - Ray Count: 8
   - LEDs per Ray: 10
   - Ray Spacing Angle: 45°
4. [ ] Click "Create"
5. [ ] Verify radial rays preview appears
6. [ ] Draw pixels along different rays
7. [ ] Save pattern (`test_radial_rays.ledproj`)
8. [ ] Close and reopen pattern
9. [ ] Verify all ray data is preserved
10. [ ] Verify pixel positions match original

### Expected Results:
- ✅ Radial rays layout creates correctly
- ✅ All ray parameters saved
- ✅ Pattern loads with all rays intact
- ✅ No schema validation errors

---

## Test 4: Custom Positions Pattern Creation & Persistence

**Objective**: Verify custom LED positions work with schema validation.

### Steps:
1. [ ] Create new pattern
2. [ ] Select "Custom Positions" layout type
3. [ ] Set parameters:
   - Units: mm
   - Center X: 10.0
   - Center Y: 10.0
   - Add custom positions: [[10, 10], [12, 10], [14, 10]]
4. [ ] Click "Create"
5. [ ] Verify custom positions preview appears
6. [ ] Draw pixels at custom positions
7. [ ] Save pattern (`test_custom_positions.ledproj`)
8. [ ] Close and reopen pattern
9. [ ] Verify all custom position data is preserved
10. [ ] Verify pixel positions match original

### Expected Results:
- ✅ Custom positions layout creates correctly
- ✅ All position data saved
- ✅ Pattern loads with all positions intact
- ✅ No schema validation errors

---

## Test 5: Export Formats with Circular Layouts

**Objective**: Verify all export formats work correctly with circular layouts.

### Steps:
1. [ ] Open a circular pattern (from Test 1)
2. [ ] Export to WLED format (File → Export → WLED)
   - [ ] Verify export succeeds
   - [ ] Verify exported file contains correct pixel order
3. [ ] Export to Falcon Player format (File → Export → Falcon Player)
   - [ ] Verify export succeeds
   - [ ] Verify exported file contains correct pixel order
4. [ ] Export to xLights format (File → Export → xLights)
   - [ ] Verify export succeeds
   - [ ] Verify exported file contains correct pixel order
5. [ ] Repeat for multi-ring pattern
6. [ ] Repeat for radial rays pattern

### Expected Results:
- ✅ All export formats work with circular layouts
- ✅ Pixel order matches mapping table
- ✅ No export errors
- ✅ Exported files are valid

---

## Test 6: Schema Validation Error Handling

**Objective**: Verify schema validation catches invalid data.

### Steps:
1. [ ] Create a circular pattern
2. [ ] Save pattern normally (should succeed)
3. [ ] Manually edit the saved JSON file (if possible)
   - [ ] Change `circular_led_count` to invalid value (e.g., -1)
   - [ ] Try to load the pattern
   - [ ] Verify error message is clear
4. [ ] Restore valid JSON file
5. [ ] Verify pattern loads correctly

### Expected Results:
- ✅ Valid patterns load successfully
- ✅ Invalid patterns show clear error messages
- ✅ Application remains stable after validation errors

---

## Test 7: Round-Trip Conversion

**Objective**: Verify pattern → JSON → pattern conversion preserves all data.

### Steps:
1. [ ] Create a complex circular pattern:
   - Multi-ring layout
   - Multiple frames
   - Multiple layers
   - Various colors
2. [ ] Save pattern
3. [ ] Load pattern
4. [ ] Compare all properties:
   - [ ] Layout type matches
   - [ ] All circular parameters match
   - [ ] All frames match
   - [ ] All layers match
   - [ ] All pixel colors match
   - [ ] Mapping table matches

### Expected Results:
- ✅ All data preserved exactly
- ✅ No data loss or corruption
- ✅ Round-trip conversion is lossless

---

## Test 8: Console Error Check

**Objective**: Verify no errors appear in console during testing.

### Steps:
1. [ ] Open application console/log
2. [ ] Perform all tests above
3. [ ] Monitor console for:
   - [ ] Schema validation errors
   - [ ] Serialization errors
   - [ ] Deserialization errors
   - [ ] Any unexpected exceptions

### Expected Results:
- ✅ No schema validation errors
- ✅ No serialization/deserialization errors
- ✅ No unexpected exceptions
- ✅ Only expected info/warning messages (if any)

---

## Test 9: Performance Check

**Objective**: Verify schema validation doesn't impact performance.

### Steps:
1. [ ] Create large circular pattern (100+ LEDs)
2. [ ] Measure save time
3. [ ] Measure load time
4. [ ] Compare with rectangular pattern of similar size
5. [ ] Verify performance is acceptable

### Expected Results:
- ✅ Save/load times are reasonable (< 2 seconds for typical patterns)
- ✅ No noticeable performance degradation
- ✅ Schema validation is fast

---

## Test 10: Backward Compatibility

**Objective**: Verify existing rectangular patterns still work.

### Steps:
1. [ ] Create rectangular pattern (16x16)
2. [ ] Save pattern
3. [ ] Load pattern
4. [ ] Verify all functionality works
5. [ ] Verify no schema errors for rectangular patterns

### Expected Results:
- ✅ Rectangular patterns work as before
- ✅ No breaking changes
- ✅ Backward compatibility maintained

---

## Test Results Summary

### Test Status
- [ ] Test 1: Basic Circular Pattern - ☐ Pass / ☐ Fail
- [ ] Test 2: Multi-Ring Pattern - ☐ Pass / ☐ Fail
- [ ] Test 3: Radial Rays Pattern - ☐ Pass / ☐ Fail
- [ ] Test 4: Custom Positions Pattern - ☐ Pass / ☐ Fail
- [ ] Test 5: Export Formats - ☐ Pass / ☐ Fail
- [ ] Test 6: Schema Validation Errors - ☐ Pass / ☐ Fail
- [ ] Test 7: Round-Trip Conversion - ☐ Pass / ☐ Fail
- [ ] Test 8: Console Error Check - ☐ Pass / ☐ Fail
- [ ] Test 9: Performance Check - ☐ Pass / ☐ Fail
- [ ] Test 10: Backward Compatibility - ☐ Pass / ☐ Fail

### Issues Found
- Issue 1: _________________________________________________
- Issue 2: _________________________________________________
- Issue 3: _________________________________________________

### Overall Status
- ☐ All Tests Pass - Ready for Release
- ☐ Some Tests Fail - Issues Need Resolution
- ☐ Critical Issues Found - Blocking Release

---

## Notes

**Tester Name**: _______________  
**Test Date**: _______________  
**Test Duration**: _______________  
**Environment**: _______________ (OS, Python version, etc.)

---

**Last Updated**: 2025-01-27

