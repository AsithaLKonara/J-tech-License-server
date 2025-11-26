# UAT Test Scenarios

**Project**: Upload Bridge  
**Version**: 1.0  
**Date**: 2024

---

## Test Scenario Format

Each scenario includes:
- **ID**: Unique identifier
- **Title**: Scenario name
- **Priority**: Critical / High / Medium / Low
- **Prerequisites**: What's needed before starting
- **Steps**: Detailed test steps
- **Expected Result**: What should happen
- **Actual Result**: [To be filled by tester]
- **Status**: Pass / Fail / Blocked
- **Notes**: Additional observations

---

## Category 1: Basic Functionality

### TS-001: Create New Pattern
**Priority**: Critical  
**Prerequisites**: Application installed and launched

**Steps**:
1. Click "New Pattern" or File → New
2. Set dimensions: 16x16
3. Click "Create"
4. Verify canvas appears
5. Draw a simple shape using brush tool
6. Click "Save" or File → Save
7. Enter filename: "test_pattern"
8. Click "Save"
9. Close application
10. Reopen application
11. File → Open → "test_pattern"
12. Verify pattern loads correctly

**Expected Result**:
- Pattern creates successfully
- Canvas displays correctly
- Drawing works
- Pattern saves to file
- Pattern can be reopened
- All data preserved

**Actual Result**: [To be filled]  
**Status**: [ ]  
**Notes**: [To be filled]

---

### TS-002: Import Image
**Priority**: Critical  
**Prerequisites**: Test image file available (PNG, 16x16 or larger)

**Steps**:
1. Create new pattern (16x16)
2. Click "Import" → "Import Image"
3. Select test image file
4. Choose resize mode: "Fit"
5. Click "Import"
6. Verify image appears on canvas
7. Verify colors match original

**Expected Result**:
- Image imports successfully
- Image fits canvas correctly
- Colors preserved accurately
- No errors or crashes

**Actual Result**: [To be filled]  
**Status**: [ ]  
**Notes**: [To be filled]

---

### TS-003: Export Pattern
**Priority**: Critical  
**Prerequisites**: Pattern created with at least 1 frame

**Steps**:
1. Open or create pattern
2. Click "Export" or File → Export
3. Select format: "Binary (.bin)"
4. Choose export location
5. Click "Export"
6. Verify file created
7. Verify file size > 0

**Expected Result**:
- Export dialog appears
- Export completes successfully
- File created at specified location
- File contains valid data

**Actual Result**: [To be filled]  
**Status**: [ ]  
**Notes**: [To be filled]

---

## Category 2: Animation Features

### TS-004: Create Multi-Frame Animation
**Priority**: High  
**Prerequisites**: Pattern created

**Steps**:
1. Create pattern with 3 frames
2. Draw different content on each frame
3. Set frame durations: 100ms, 200ms, 300ms
4. Click "Play" to preview
5. Verify animation plays
6. Verify timing is correct

**Expected Result**:
- Frames can be added
- Each frame can be edited independently
- Preview plays animation smoothly
- Frame durations apply correctly

**Actual Result**: [To be filled]  
**Status**: [ ]  
**Notes**: [To be filled]

---

### TS-005: Frame Duplication
**Priority**: Medium  
**Prerequisites**: Pattern with at least 1 frame

**Steps**:
1. Select frame 0
2. Draw content on frame
3. Right-click frame → "Duplicate"
4. Verify new frame created
5. Verify content copied
6. Modify duplicated frame
7. Verify original unchanged

**Expected Result**:
- Frame duplicates successfully
- Content copied correctly
- Modifications don't affect original
- Frame count increases

**Actual Result**: [To be filled]  
**Status**: [ ]  
**Notes**: [To be filled]

---

## Category 3: Advanced Features

### TS-006: Layer Management
**Priority**: High  
**Prerequisites**: Pattern created

**Steps**:
1. Open layer panel
2. Add new layer
3. Draw on new layer
4. Toggle layer visibility
5. Adjust layer opacity (50%)
6. Reorder layers
7. Delete layer (not last one)

**Expected Result**:
- Layers can be added/removed
- Visibility toggle works
- Opacity adjustment works
- Layer reordering works
- Last layer cannot be deleted

**Actual Result**: [To be filled]  
**Status**: [ ]  
**Notes**: [To be filled]

---

### TS-007: Template Library
**Priority**: Medium  
**Prerequisites**: None

**Steps**:
1. Click "Templates" or Tools → Templates
2. Browse template library
3. Select "Scrolling Text" template
4. Customize parameters:
   - Text: "TEST"
   - Speed: 2
   - Color: Red
5. Click "Generate"
6. Verify pattern created
7. Preview pattern

**Expected Result**:
- Template library opens
- Templates are listed
- Parameters can be customized
- Pattern generates correctly
- Preview shows expected result

**Actual Result**: [To be filled]  
**Status**: [ ]  
**Notes**: [To be filled]

---

### TS-008: Enhanced Text Tool
**Priority**: Medium  
**Prerequisites**: Pattern created

**Steps**:
1. Select "Text Tool"
2. Enter text: "Hello"
3. Select font: "5x7"
4. Enable outline
5. Set outline color: Red
6. Enable shadow
7. Set alignment: Center
8. Click "Generate"
9. Verify text appears correctly

**Expected Result**:
- Text tool opens
- Text can be entered
- Font selection works
- Effects (outline, shadow) apply
- Alignment works
- Preview updates live

**Actual Result**: [To be filled]  
**Status**: [ ]  
**Notes**: [To be filled]

---

## Category 4: Firmware Operations

### TS-009: Build Firmware
**Priority**: Critical  
**Prerequisites**: Pattern created, chip type selected

**Steps**:
1. Create or open pattern
2. Go to "Firmware" tab
3. Select chip: "ESP32"
4. Configure options:
   - GPIO pin: 2
   - Brightness: 100%
5. Click "Build Firmware"
6. Wait for build to complete
7. Verify firmware file created
8. Verify build log shows success

**Expected Result**:
- Firmware builds successfully
- No build errors
- Firmware file created
- Build log shows success

**Actual Result**: [To be filled]  
**Status**: [ ]  
**Notes**: [To be filled]

---

### TS-010: Upload Firmware
**Priority**: Critical  
**Prerequisites**: Firmware built, device connected

**Steps**:
1. Build firmware (from TS-009)
2. Connect ESP32 device
3. Select COM port
4. Click "Upload"
5. Monitor upload progress
6. Wait for completion
7. Verify device displays pattern

**Expected Result**:
- Device detected
- Upload starts
- Progress shown
- Upload completes successfully
- Device displays pattern correctly

**Actual Result**: [To be filled]  
**Status**: [ ]  
**Notes**: [To be filled]

---

## Category 5: Error Handling

### TS-011: Invalid File Import
**Priority**: High  
**Prerequisites**: Invalid test file available

**Steps**:
1. Click "Import" → "Import Image"
2. Select invalid file (e.g., .txt file renamed to .png)
3. Click "Import"
4. Observe error handling

**Expected Result**:
- Error message appears
- Message is clear and helpful
- Application doesn't crash
- User can recover and try again

**Actual Result**: [To be filled]  
**Status**: [ ]  
**Notes**: [To be filled]

---

### TS-012: Device Connection Failure
**Priority**: High  
**Prerequisites**: No device connected

**Steps**:
1. Build firmware
2. Attempt upload without device connected
3. Observe error handling

**Expected Result**:
- Clear error message
- Suggests checking connection
- Application doesn't crash
- User can retry after connecting

**Actual Result**: [To be filled]  
**Status**: [ ]  
**Notes**: [To be filled]

---

## Category 6: Performance

### TS-013: Large Pattern Handling
**Priority**: Medium  
**Prerequisites**: None

**Steps**:
1. Create pattern: 64x64, 50 frames
2. Draw content on multiple frames
3. Measure:
   - Load time
   - Frame switching time
   - Preview playback smoothness
   - Export time

**Expected Result**:
- Pattern loads in < 5 seconds
- Frame switching is smooth (< 1s)
- Preview plays without stuttering
- Export completes in reasonable time

**Actual Result**: [To be filled]  
**Status**: [ ]  
**Notes**: [To be filled]

---

## Category 7: Usability

### TS-014: Feature Discoverability
**Priority**: Medium  
**Prerequisites**: New user (first time using application)

**Steps**:
1. Launch application (first time)
2. Without reading documentation, attempt to:
   - Create a pattern
   - Add animation
   - Export pattern
3. Note: How easy was it to find features?
4. Note: Were tooltips/help available?

**Expected Result**:
- Features are discoverable
- UI is intuitive
- Help/tooltips available
- User can complete tasks without documentation

**Actual Result**: [To be filled]  
**Status**: [ ]  
**Notes**: [To be filled]

---

### TS-015: Undo/Redo
**Priority**: Medium  
**Prerequisites**: Pattern created

**Steps**:
1. Draw on canvas
2. Press Ctrl+Z (Undo)
3. Verify last action undone
4. Press Ctrl+Y (Redo)
5. Verify action redone
6. Test multiple undo/redo operations

**Expected Result**:
- Undo works correctly
- Redo works correctly
- Multiple operations supported
- Keyboard shortcuts work

**Actual Result**: [To be filled]  
**Status**: [ ]  
**Notes**: [To be filled]

---

## Test Execution Summary

**Total Scenarios**: 15  
**Critical**: 4  
**High**: 5  
**Medium**: 6  
**Low**: 0

**Execution Date**: [To be filled]  
**Tester**: [To be filled]  
**Environment**: [To be filled]

---

**Last Updated**: 2024
