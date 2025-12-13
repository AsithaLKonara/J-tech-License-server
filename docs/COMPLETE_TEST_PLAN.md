# Complete Test Plan - Upload Bridge Application

## Test Strategy Overview

### Test Objectives

- Verify all functional requirements are met
- Ensure cross-tab integration works correctly
- Validate circular layout features (Budurasmala)
- Test hardware compatibility (14+ chip types)
- Verify export/import formats (10+ formats)
- Test performance under load
- Ensure data integrity and error handling
- Validate user workflows end-to-end

### Test Scope

**In Scope:**

- All 9 tabs (Media Upload, Design Tools, Preview, Flash, WiFi Upload, Arduino IDE, Pattern Library, Audio Reactive, Batch Flash)
- 8 drawing tools
- Multi-layer system
- Frame management and timeline
- Circular layouts (multi-ring, radial rays, custom positions)
- Export/import (10+ formats)
- Firmware building and flashing
- Device management and APIs
- Pattern sharing

**Out of Scope:**

- Third-party library bugs
- OS-level issues
- Hardware failures

### Test Levels

1. **Unit Testing** - Individual components
2. **Integration Testing** - Component interactions
3. **System Testing** - End-to-end workflows
4. **Acceptance Testing** - User acceptance scenarios

### Test Types

1. **Functional Testing** - Feature correctness
2. **Integration Testing** - Cross-component communication
3. **UI/UX Testing** - User interface and experience
4. **Performance Testing** - Load, stress, scalability
5. **Security Testing** - Data protection, API security
6. **Compatibility Testing** - OS, chip types, file formats
7. **Regression Testing** - Existing functionality
8. **Usability Testing** - User workflows

---

## Test Environment Setup

### Hardware Requirements

- Windows 10/11, Linux (Ubuntu 20.04+), macOS 11+
- ESP8266/ESP32 development boards (for hardware testing)
- USB cables for flashing
- Network access for WiFi upload testing

### Software Requirements

- Python 3.9+
- PySide6
- Required dependencies (from requirements.txt)
- Test data files (patterns, images, videos)
- Firmware templates

### Test Data Requirements

- Sample patterns (rectangular, circular, multi-ring, radial rays)
- Media files (images, GIFs, videos)
- Project files (.ledproj)
- Export files (all formats)
- Invalid/corrupted files (for negative testing)

---

## Test Cases by Feature Area

### 1. Application Launch & Initialization

#### TC-APP-001: Application Launch

**Priority**: High  
**Type**: Functional  
**Steps**:

1. Launch application
2. Verify main window opens
3. Verify all tabs are present
4. Verify status bar shows "Ready"
5. Verify no errors in console

**Expected**: Application launches successfully, all tabs visible

#### TC-APP-002: Tab Initialization (Lazy Loading)

**Priority**: Medium  
**Type**: Integration  
**Steps**:

1. Launch application
2. Click each tab sequentially
3. Verify tab initializes on first access
4. Verify tab state persists on return

**Expected**: Tabs initialize correctly on demand

#### TC-APP-003: Settings Persistence

**Priority**: Medium  
**Type**: Functional  
**Steps**:

1. Change settings (theme, window size, etc.)
2. Close application
3. Reopen application
4. Verify settings restored

**Expected**: Settings persist across sessions

---

### 2. Design Tools Tab

#### TC-DT-001: Create New Pattern (Rectangular)

**Priority**: High  
**Type**: Functional  
**Steps**:

1. Click Design Tools tab
2. Click "New" button
3. Select "Rectangular" layout
4. Set dimensions: 16×16
5. Click "Create"
6. Verify canvas shows 16×16 grid
7. Verify pattern created in repository

**Expected**: Pattern created, canvas initialized

#### TC-DT-002: Create Circular Pattern

**Priority**: High  
**Type**: Functional  
**Steps**:

1. Click "New" button
2. Select "Circle" layout
3. Set: 60 LEDs, radius 15
4. Click "Create"
5. Verify circular preview appears
6. Verify mapping table generated
7. Verify canvas shows circular overlay

**Expected**: Circular pattern created with mapping table

#### TC-DT-003: Pixel Tool Drawing

**Priority**: High  
**Type**: Functional  
**Steps**:

1. Create new pattern
2. Select Pixel tool
3. Select color (red)
4. Click on canvas at (5, 5)
5. Verify pixel turns red
6. Verify pattern_modified signal emitted
7. Verify Preview tab updates

**Expected**: Pixel drawn, cross-tab sync works

#### TC-DT-004: Multi-Layer System

**Priority**: High  
**Type**: Functional  
**Steps**:

1. Create pattern with 2 layers
2. Draw on Layer 1 (red)
3. Draw on Layer 2 (blue)
4. Toggle Layer 1 visibility
5. Verify only Layer 2 visible
6. Change Layer 2 opacity to 50%
7. Verify blend effect

**Expected**: Layers work independently, blend correctly

#### TC-DT-005: Frame Management

**Priority**: High  
**Type**: Functional  
**Steps**:

1. Create pattern
2. Add 3 frames
3. Draw different content on each frame
4. Use timeline to navigate frames
5. Delete frame 2
6. Verify frames renumbered
7. Verify content preserved

**Expected**: Frame operations work correctly

#### TC-DT-006: Undo/Redo

**Priority**: High  
**Type**: Functional  
**Steps**:

1. Draw pixels
2. Press Ctrl+Z (undo)
3. Verify pixels removed
4. Press Ctrl+Y (redo)
5. Verify pixels restored
6. Test with 10+ operations

**Expected**: Undo/redo works correctly

#### TC-DT-007: Circular Preview Real-Time Updates

**Priority**: High  
**Type**: Integration  
**Steps**:

1. Create circular pattern
2. Draw on canvas
3. Verify circular preview updates immediately
4. Switch frames
5. Verify preview updates

**Expected**: Circular preview syncs in real-time

#### TC-DT-008: Drawing Tools (All 8 Tools)

**Priority**: High  
**Type**: Functional  
**Test each tool**:

- Pixel Tool: Single pixel, brush size 1-8
- Rectangle Tool: Filled/outline, corner radius
- Circle Tool: Filled/outline, perfect circle (Shift)
- Line Tool: Straight lines, adjustable width
- Fill Tool: Flood fill, tolerance
- Gradient Tool: Linear gradients, color stops
- Random Tool: Spray density, area size
- Eyedropper Tool: Color picking

**Expected**: All tools work correctly

---

### 3. Media Upload Tab

#### TC-MU-001: Image Import

**Priority**: High  
**Type**: Functional  
**Steps**:

1. Click Media Upload tab
2. Click "Select Media File"
3. Select image (PNG, JPG, BMP)
4. Set dimensions: 32×32
5. Click "Convert to Pattern"
6. Verify pattern created
7. Verify auto-switches to Preview tab

**Expected**: Image converted to pattern

#### TC-MU-002: GIF Import

**Priority**: High  
**Type**: Functional  
**Steps**:

1. Select animated GIF
2. Verify frame extraction
3. Set target dimensions
4. Convert to pattern
5. Verify all frames imported
6. Verify animation plays correctly

**Expected**: GIF frames extracted correctly

#### TC-MU-003: Video Import

**Priority**: Medium  
**Type**: Functional  
**Steps**:

1. Select video file
2. Configure frame extraction (all/sample)
3. Set time range
4. Convert to pattern
5. Verify frames extracted
6. Verify pattern plays

**Expected**: Video converted to pattern

---

### 4. Preview Tab

#### TC-PV-001: Pattern Playback

**Priority**: High  
**Type**: Functional  
**Steps**:

1. Load pattern
2. Click "Play" button
3. Verify animation plays
4. Adjust speed (0.1x - 5.0x)
5. Verify speed changes
6. Pause/Resume
7. Use frame slider to scrub

**Expected**: Playback works correctly

#### TC-PV-002: Brightness Control

**Priority**: Medium  
**Type**: Functional  
**Steps**:

1. Load pattern
2. Adjust brightness slider
3. Verify preview updates in real-time
4. Test advanced brightness controls
5. Test per-channel brightness

**Expected**: Brightness controls work

#### TC-PV-003: Cross-Tab Sync

**Priority**: High  
**Type**: Integration  
**Steps**:

1. Load pattern in Design Tools
2. Draw pixels
3. Switch to Preview tab
4. Verify changes appear
5. Draw more in Design Tools
6. Verify Preview updates

**Expected**: Changes sync between tabs

---

### 5. Flash Tab

#### TC-FL-001: Firmware Build (ESP8266)

**Priority**: High  
**Type**: Functional  
**Steps**:

1. Load pattern
2. Select chip: ESP8266
3. Select port: COM3
4. Set GPIO: 2
5. Click "Build & Flash"
6. Verify firmware builds
7. Verify upload succeeds
8. Verify device plays pattern

**Expected**: Firmware built and flashed successfully

#### TC-FL-002: Multiple Chip Types

**Priority**: High  
**Type**: Compatibility  
**Test each chip type**:

- ESP8266, ESP32
- ATmega328P, ATmega2560, ATtiny85
- STM32F103C8
- PIC16F876A
- NuMicro M051

**Expected**: All chip types supported

#### TC-FL-003: Flash Error Handling

**Priority**: Medium  
**Type**: Negative  
**Steps**:

1. Select invalid port
2. Attempt flash
3. Verify error message
4. Disconnect device mid-flash
5. Verify error handling

**Expected**: Errors handled gracefully

---

### 6. Export/Import

#### TC-EX-001: Export Formats

**Priority**: High  
**Type**: Functional  
**Test each format**:

- .bin (binary)
- .hex (Intel HEX)
- .dat (LEDS format)
- .leds (LEDS format)
- .json (JSON)
- .ledproj (project)
- WLED JSON
- Falcon Player
- xLights

**Steps for each**:

1. Create pattern
2. Export to format
3. Verify file created
4. Import file back
5. Verify pattern matches

**Expected**: All formats export/import correctly

#### TC-EX-002: Circular Layout Export

**Priority**: High  
**Type**: Functional  
**Steps**:

1. Create circular pattern
2. Draw pixels
3. Export to WLED
4. Verify pixel order matches mapping table
5. Import back
6. Verify pattern preserved

**Expected**: Circular layouts export correctly

#### TC-EX-003: Export Validation

**Priority**: Medium  
**Type**: Functional  
**Steps**:

1. Create pattern with invalid dimensions
2. Attempt export
3. Verify validation error
4. Fix dimensions
5. Verify export succeeds

**Expected**: Validation prevents invalid exports

---

### 7. Circular Layouts (Budurasmala)

#### TC-CL-001: Multi-Ring Layout

**Priority**: High  
**Type**: Functional  
**Steps**:

1. Create multi-ring pattern (3 rings)
2. Set ring parameters (LED counts, radii)
3. Verify mapping table generated
4. Draw on each ring
5. Verify circular preview shows rings
6. Export and verify

**Expected**: Multi-ring layout works

#### TC-CL-002: Radial Rays Layout

**Priority**: High  
**Type**: Functional  
**Steps**:

1. Create radial rays pattern
2. Set: 8 rays, 10 LEDs per ray
3. Verify mapping table
4. Draw on rays
5. Verify preview
6. Export

**Expected**: Radial rays layout works

#### TC-CL-003: Custom LED Positions

**Priority**: Medium  
**Type**: Functional  
**Steps**:

1. Create custom position pattern
2. Import LED positions (CSV/JSON)
3. Verify positions loaded
4. Draw on custom positions
5. Verify preview
6. Export

**Expected**: Custom positions work

#### TC-CL-004: Mapping Table Validation

**Priority**: High  
**Type**: Functional  
**Steps**:

1. Load pattern with missing mapping table
2. Verify table regenerated
3. Load pattern with invalid table
4. Verify table regenerated
5. Export pattern
6. Verify validation runs

**Expected**: Mapping tables validated/regenerated

---

### 8. Integration Testing

#### TC-IT-001: Pattern Modification Sync

**Priority**: High  
**Type**: Integration  
**Steps**:

1. Create pattern in Design Tools
2. Draw pixels
3. Verify pattern_modified signal emitted
4. Verify MainWindow.on_pattern_modified() called
5. Verify pattern_changed signal emitted
6. Verify Preview tab updates
7. Verify Flash tab updates

**Expected**: All tabs sync correctly

#### TC-IT-002: Repository Pattern Management

**Priority**: High  
**Type**: Integration  
**Steps**:

1. Set pattern in repository
2. Verify pattern_changed signal emitted
3. Verify all tabs receive update
4. Modify pattern
5. Verify repository updated
6. Verify dirty flag set

**Expected**: Repository manages state correctly

#### TC-IT-003: Service Integration

**Priority**: Medium  
**Type**: Integration  
**Test each service**:

- ExportService: Export operations
- FlashService: Firmware building
- PatternService: Load/save
- DeviceManager: Device control

**Expected**: All services integrate correctly

---

### 9. Performance Testing

#### TC-PF-001: Large Pattern Handling

**Priority**: Medium  
**Type**: Performance  
**Steps**:

1. Create pattern: 256×256, 100 frames
2. Draw pixels across all frames
3. Measure memory usage
4. Test save/load time
5. Test export time
6. Verify no crashes

**Expected**: Handles large patterns efficiently

#### TC-PF-002: Real-Time Updates Performance

**Priority**: Medium  
**Type**: Performance  
**Steps**:

1. Create pattern
2. Rapidly draw pixels (10/second)
3. Verify circular preview updates
4. Verify Preview tab updates
5. Measure update latency
6. Verify no lag

**Expected**: Updates remain responsive

#### TC-PF-003: Export Performance

**Priority**: Low  
**Type**: Performance  
**Steps**:

1. Create large pattern
2. Export to each format
3. Measure export time
4. Verify within acceptable limits (<5s for 1000 LEDs)

**Expected**: Exports complete in reasonable time

---

### 10. Error Handling & Edge Cases

#### TC-EC-001: Invalid File Handling

**Priority**: Medium  
**Type**: Negative  
**Steps**:

1. Attempt to open corrupted file
2. Verify error message
3. Attempt to open unsupported format
4. Verify error message
5. Attempt to open non-existent file
6. Verify error handling

**Expected**: Errors handled gracefully

#### TC-EC-002: Invalid Pattern Dimensions

**Priority**: Medium  
**Type**: Negative  
**Steps**:

1. Attempt to create pattern: 0×0
2. Verify validation error
3. Attempt: -5×10
4. Verify validation
5. Attempt: 10000×10000
6. Verify warning/limit

**Expected**: Invalid dimensions rejected

#### TC-EC-003: Concurrent Operations

**Priority**: Low  
**Type**: Edge Case  
**Steps**:

1. Start export
2. Immediately start another export
3. Verify handling
4. Start flash during export
5. Verify handling

**Expected**: Concurrent operations handled

---

### 11. Usability Testing

#### TC-US-001: Complete Workflow

**Priority**: High  
**Type**: Usability  
**Steps**:

1. Launch application
2. Create new pattern
3. Draw animation (5 frames)
4. Save project
5. Close application
6. Reopen project
7. Edit pattern
8. Export to WLED
9. Flash to device

**Expected**: Complete workflow works smoothly

#### TC-US-002: Keyboard Shortcuts

**Priority**: Medium  
**Type**: Usability  
**Test all shortcuts**:

- Ctrl+Z (undo), Ctrl+Y (redo)
- Ctrl+S (save), Ctrl+O (open)
- Ctrl+N (new)
- Space (play/pause)
- Arrow keys (frame navigation)

**Expected**: All shortcuts work

#### TC-US-003: Tooltips and Help

**Priority**: Low  
**Type**: Usability  
**Steps**:

1. Hover over all buttons
2. Verify tooltips appear
3. Check help menu
4. Verify documentation accessible

**Expected**: Help available and clear

---

## Test Execution Plan

### Phase 1: Unit Testing (Week 1)

- Execute unit tests for all modules
- Target: 90%+ code coverage
- Tools: pytest, coverage.py

### Phase 2: Integration Testing (Week 2)

- Test tab-to-tab integration
- Test service integration
- Test repository integration
- Verify signal connections

### Phase 3: System Testing (Week 3-4)

- Execute all functional test cases
- Test complete user workflows
- Test circular layout features
- Test export/import formats

### Phase 4: Performance Testing (Week 5)

- Load testing
- Stress testing
- Memory profiling
- Performance optimization

### Phase 5: Regression Testing (Week 6)

- Execute full regression suite
- Verify no regressions
- Fix critical bugs

### Phase 6: Acceptance Testing (Week 7)

- User acceptance testing
- Beta testing
- Feedback collection

---

## Test Metrics & Reporting

### Metrics to Track

- Test case execution: Pass/Fail rate
- Defect density: Bugs per feature
- Code coverage: % lines covered
- Defect resolution time: Time to fix
- Test execution time: Total test duration

### Reporting

- Daily test execution reports
- Weekly defect summary
- Test coverage reports
- Performance benchmark reports
- Final test summary report

---

## Risk Assessment

### High Risk Areas

1. Circular layout mapping table generation
2. Cross-tab synchronization
3. Firmware building for multiple chip types
4. Export format compatibility
5. Large pattern performance

### Mitigation

- Extra test coverage for high-risk areas
- Automated regression tests
- Performance monitoring
- Early testing of critical features

---

## Test Deliverables

1. Test Plan (this document)
2. Test Cases (detailed test scripts)
3. Test Data (sample files, patterns)
4. Test Execution Reports
5. Defect Reports
6. Test Summary Report
7. Test Coverage Report

---

## Sign-off

**Test Plan Prepared By**: [QA Lead]  
**Date**: [Date]  
**Approved By**: [Project Manager]  
**Date**: [Date]

